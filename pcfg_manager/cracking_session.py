#!/usr/bin/env python3

########################################################################################
#
# Name: PCFG_Cracker Cracking Management Code
# Description: Manages a cracking session
#              Eventaully I want to add other functionality into the pcfg_manager codebase
#              such as honeywords, so I am moving the actually running of a cracking
#              session into this chunk of code
#
#########################################################################################

import sys
import traceback
import time
import threading ##--Used only for the "check for user input" threads
from multiprocessing import Process, Queue, Pipe

from pcfg_manager.core_grammar import PcfgClass, print_grammar
from pcfg_manager.priority_queue import PcfgQueue
from pcfg_manager.queue_storage import QueueStorage
from pcfg_manager.ret_types import RetType


###################################################################################################
# Used to manage a password cracking session
###################################################################################################
class CrackingSession:
    
    ############################################################################
    # Basic initialization function
    ############################################################################
    def __init__(self, pcfg = None):
        self.pcfg = pcfg
        
        ##--Debugging and Performance Monitoring Variables--##
        self.num_parse_trees = 0      #-Total number of parse_trees processed so far
        self.num_guesses = 0          #-Total number of guesses made so far
        self.p_queue_start_time = 0   #-Start time of running the Next algorithm on the priority queue
        self.p_queue_stop_time = 0    #-Stop time of running the Next algorithm
        self.guess_start_time = 0     #-Start time of genering the actual guesses
        self.guess_stop_time = 0      #-Stop time of generating the actual guesses
        self.running_queue_time = 0   #-Total time running the "Next" algorithm to get a new pre-terminal
        self.running_guess_time = 0   #-Total time spent generaing guesses from pre-terminals and printing them out

        
    ##############################################################################
    # Starts the cracking session and starts generating guesses
    ##############################################################################
    def run(self, print_queue_info = False):
        #-Start the clock
        self.total_time_start = time.perf_counter()
        
        #-Create a queue to send data back to the main process, (this one)
        #-In the future, may change it to a pipe for performance reasons, but starting out with queue since it is easier
        parent_conn, child_conn = Pipe()
        
        ##--Spawn a child process to handle backup storage as the list gets too big for the main priority queue
        #-Initialize the data structures
        backup_storage = QueueStorage()
        #-At least from my testing, queue while slower in general was signifincatly faster than pipes for transfering a lot of data
        #-in a non-blocking way
        backup_save_comm = Queue()
        backup_restore_comm = Queue()
        #-Now create and start the process
        backup_storage_process = Process(target=backup_storage.start_process, args=(backup_save_comm, backup_restore_comm))
        backup_storage_process.daemon = True
        backup_storage_process.start()
        
        #-Spawn a child process to start generating the pre-terminals
        priority_queue_process = Process(target=spawn_pqueue_thread, args=(self.pcfg, child_conn, print_queue_info, backup_save_comm, backup_restore_comm))
        priority_queue_process.daemon = True
        priority_queue_process.start()
        
        ##--Setup the check to see if a user is pressing a button--#
        user_input = [None]
        user_thread = threading.Thread(target=keypress, args=(user_input,))
        user_thread.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
        user_thread.start()
                 
        self.p_queue_start_time = time.perf_counter()
        
        #-Get the first item from the child priority_queue process
        queue_items = parent_conn.recv()
        
        #-If the value None is encountered the queue is either empty or an error occured so stopped
        if queue_items is None:
            print("Finished processing items from the priority queue", file=sys.stderr)
            priority_queue_process.join()
            return
                    
        self.p_queue_stop_time = time.perf_counter() - self.p_queue_start_time
        self.running_queue_time = self.running_queue_time + self.p_queue_stop_time
        
        ##--Keep running while the p_queue.next_function still has items in it
        while True:
            
            ##--Expand the guesses from the parse tree
            self.guess_start_time = time.perf_counter()
            
            for terminal in queue_items:
                try:
                    number_of_terminal_guesses, current_guesses = self.pcfg.list_terminals(terminal.parse_tree, print_output = not print_queue_info)
                ##--If we can't print out guesses anymore--##    
                except Exception as msg:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    traceback.print_tb(exc_traceback, limit=3, file=sys.stdout)
                    print(msg, file=sys.stderr)
                    return
                    
                self.num_guesses += number_of_terminal_guesses
                self.num_parse_trees = self.num_parse_trees + 1
                
                ##--Print_Queue_Info says if we are running this session for debugging and performance improvements vs actually cracking passwords
                if print_queue_info == True:     
                    
                    if self.num_parse_trees % 10000 == 0:
                        print ("PQueueTime " + str(self.running_queue_time),file=sys.stderr)
                        print ("Guesses:" + str(self.num_guesses),file=sys.stderr)
                        print ("GuessTime " + str(self.running_guess_time),file=sys.stderr)
                        print ("Average num of guesses per parse-tree: " + str(self.num_guesses // self.num_parse_trees),file=sys.stderr)
                        print ("Total Time " + str(time.perf_counter() - self.total_time_start),file=sys.stderr)
                        print ("Number of guesses a second: " + str(self.num_guesses // (time.perf_counter() - self.total_time_start)),file=sys.stderr)
                        #print ("Current probability: " + str(self.p_queue.max_probability),file=sys.stderr)
                        print ()
                        
            self.guess_stop_time = time.perf_counter() - self.guess_start_time
            self.running_guess_time = self.running_guess_time + self.guess_stop_time
                              
            ##--Check for user requested status output--##
            if user_input[0] is not None:          
                self.display_status(guess_list = current_guesses)
                user_input[0] = None
                ##--Kick off again the thread to check if user_input was entered
                if not user_thread.is_alive():
                    user_thread = threading.Thread(target=keypress, args=(user_input,))
                    user_thread.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
                    user_thread.start()
                    
            ##--Generate more parse trees from the priority queue
            self.p_queue_start_time = time.perf_counter()
            
            queue_items = parent_conn.recv()
        
            #-If the value None is encountered the queue is either empty or an error occured so stopped
            if queue_items is None:
                print("Finished processing items from the priority queue", file=sys.stderr)
                priority_queue_process.join()
                return
                
            self.p_queue_stop_time = time.perf_counter() - self.p_queue_start_time
            self.running_queue_time = self.running_queue_time + self.p_queue_stop_time         
                
        return
    

    ######################################################################################################
    # Displays status of cracking session
    ######################################################################################################
    def display_status(self, guess_list = []):
        print ("Status Report:",file=sys.stderr)
        if len(guess_list) != 0:
            print ("Currently generating guesses from " + str(guess_list[0]) + " to " + str(guess_list[-1]),file=sys.stderr)
        print("",file=sys.stderr)
   

###########################################################################################
# Used to check to see if a key was pressed to output program status
# *Hopefully* should work on multiple OSs
# --Simply check user_input_char to see if it is not none
###########################################################################################
def keypress(user_input_ref):
    user_input_ref[0] = input()


###############################################################################################
# The child process that is spawned off to run the priority queue and generate parse trees to
# send to the parent process
# The parse trees will be sent back to the parent process in priority order
###############################################################################################
def spawn_pqueue_thread(pcfg, child_conn, print_queue_info, backup_save_comm, backup_restore_comm):
      
    ##--Block size is the number of items to send back at once--##
    ##--Not making this configurable in the command line since it would just confuse users--##
    block_size = 10
    
    ##--Initialize the priority queue--##
    p_queue = PcfgQueue(backup_save_comm, backup_restore_comm)
    ret_value = p_queue.initialize(pcfg)
    if ret_value != RetType.STATUS_OK:
        print ("Error initalizing the priority queue, exiting",file=sys.stderr)
        return ret_value 
        
    ##--Now start generating parse trees to send back to the main process
    num_parse_trees = 0
    queue_item_list = []
    ret_value = p_queue.next_function(pcfg, queue_item_list, block_size)
    
    ##--There are no more items to use in the queue, let the parent know we are done
    if ret_value == RetType.QUEUE_EMPTY:
        child_con.send(None)
        return ret_value
    
    while ret_value == RetType.STATUS_OK:
        child_conn.send(queue_item_list)
        num_parse_trees = num_parse_trees + len(queue_item_list)
        
        ##--Print out debugging info if requested
        ##--Note, if blocksize is changed to something where the mod calc below would be skipped then
        ##--will need to update this debugging code
        if print_queue_info == True:
            if num_parse_trees % 10000 == 0:
                print ("Total number of Parse Trees: " + str (num_parse_trees),file=sys.stderr)
                print ("PQueue:" + str(len(p_queue.p_queue)),file=sys.stderr)
                
                ##--Request and get the size of the backup storage list
                backup_save_comm.put({"Command":"Status"})
                result = backup_restore_comm.get()
                print ("Backup storage list:" + str(result['Size']),file=sys.stderr)
            
        queue_item_list = []
        ret_value = p_queue.next_function(pcfg, queue_item_list, block_size)
        ##--There are no more items to use in the queue, let the parent know we are done
        if ret_value == RetType.QUEUE_EMPTY:
            child_conn.send(None)
            return ret_value
        
    return ret_value