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
import time
import threading ##--Used only for the "check for user input" threads
from multiprocessing import Process, Queue

from pcfg_manager.core_grammar import PcfgClass, print_grammar
from pcfg_manager.priority_queue import PcfgQueue
from pcfg_manager.ret_types import RetType


###################################################################################################
# Used to manage a password cracking session
###################################################################################################
class CrackingSession:
    
    ############################################################################
    # Basic initialization function
    ############################################################################
    def __init__(self, pcfg = None, p_queue = None):
        self.p_queue = p_queue
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
        ##--Setup the check to see if a user is pressing a button--#
        user_input = [None]
        user_thread = threading.Thread(target=keypress, args=(user_input,))
        user_thread.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
        user_thread.start()
    
        #-Start the clock
        self.total_time_start = time.perf_counter()
        
        #-Generate the first parse tree to process
        self.p_queue_start_time = time.perf_counter()
        queue_item_list = []
        #-This is the function that does all the work
        ret_value = self.p_queue.next_function(self.pcfg, queue_item_list)
        
        #-Currently there is only one item returned at a time, this may change in the future
        if len(queue_item_list) > 0:
            queue_item = queue_item_list[0]
        else:
            return ret_value
            
        self.p_queue_stop_time = time.perf_counter() - self.p_queue_start_time
        self.running_queue_time = self.running_queue_time + self.p_queue_stop_time
        
        ##--Keep running while the p_queue.next_function still has items in it
        while ret_value == RetType.STATUS_OK:
            
            ##--Expand the guesses from the parse tree
            self.guess_start_time = time.perf_counter()
            current_guesses = self.pcfg.list_terminals(queue_item.parse_tree) 
            self.guess_stop_time = time.perf_counter() - self.guess_start_time
            self.running_guess_time = self.running_guess_time + self.guess_stop_time
            
            self.num_parse_trees = self.num_parse_trees +1
            self.num_guesses = self.num_guesses + len(current_guesses) 
            
            ##--Print_Queue_Info says if we are running this session for debugging and performance improvements vs actually cracking passwords
            if print_queue_info == True:     
                
                if self.num_parse_trees % 10000 == 0:
                    print ("PQueue:" + str(len(self.p_queue.p_queue)),file=sys.stderr)
                    print ("Backup storage list:" + str(len(self.p_queue.storage_list)),file=sys.stderr)
                    print ("Total number of Parse Trees: " + str (self.num_parse_trees),file=sys.stderr)
                    print ("PQueueTime " + str(self.running_queue_time),file=sys.stderr)
                    print ("Guesses:" + str(self.num_guesses),file=sys.stderr)
                    print ("GuessTime " + str(self.running_guess_time),file=sys.stderr)
                    print ("Average num of guesses per parse-tree: " + str(self.num_guesses // self.num_parse_trees),file=sys.stderr)
                    print ("Total Time " + str(time.perf_counter() - self.total_time_start),file=sys.stderr)
                    print ("Number of guesses a second: " + str(self.num_guesses // (time.perf_counter() - self.total_time_start)),file=sys.stderr)
                    print ("Current probability: " + str(self.p_queue.max_probability),file=sys.stderr)
                    print ()

            ##--This is if you are actually trying to generate guesses
            else:
                for guess in current_guesses:
                    try:
                        print(guess)
                    ##--While I could silently replace/ignore the Unicode character for now I want to know if this is happening
                    except UnicodeEncodeError:
                        print("UNICODE_ERROR",file=sys.stderr)                       
            
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
            queue_item_list = []        
            ret_value = self.p_queue.next_function(self.pcfg, queue_item_list)
            if len(queue_item_list) > 0:
                queue_item = queue_item_list[0]
            self.p_queue_stop_time = time.perf_counter() - self.p_queue_start_time
            self.running_queue_time = self.running_queue_time + self.p_queue_stop_time         
                
        return RetType.STATUS_OK
    

    ######################################################################################################
    # Displays status of cracking session
    ######################################################################################################
    def display_status(self, guess_list = []):
        print ("Status Report:",file=sys.stderr)
        if len(guess_list) != 0:
            print ("Currently generating guesses from " + str(guess_list[0]) + " to " + str(guess_list[-1]),file=sys.stderr)
        print("",file=sys.stderr)
        return RetType.STATUS_OK
   

###########################################################################################
# Used to check to see if a key was pressed to output program status
# *Hopefully* should work on multiple OSs
# --Simply check user_input_char to see if it is not none
###########################################################################################
def keypress(user_input_ref):
    user_input_ref[0] = input()   