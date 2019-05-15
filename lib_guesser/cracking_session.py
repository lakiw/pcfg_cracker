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

# Local imports
from .priority_queue import PcfgQueue


## Used to manage a password cracking session
#
class CrackingSession:
    
    
    ## Basic initialization function
    #
    def __init__(self, pcfg = None):
    
        # Save the grammar for easy reference
        self.pcfg = pcfg
        
        ## Debugging and Performance Monitoring Variables
        #    
        # Total number of parse_trees processed so far
        self.num_parse_trees = 0  

        # Total number of guesses made so far        
        self.num_guesses = 0
        
        # Start time of running the Next algorithm on the priority queue
        self.p_queue_start_time = 0
        
        # Stop time of running the Next algorithm on the priority queue
        self.p_queue_stop_time = 0
        
        # Start time of genering the actual guesses
        self.guess_start_time = 0
        
        # Stop time of generating the actual guesses
        self.guess_stop_time = 0
        
        # Total time running the "Next" algorithm to get a new pre-terminal
        self.running_queue_time = 0
        
        # Total time spent generaing guesses from pre-terminals and printing them out
        self.running_guess_time = 0

        
    ## Starts the cracking session and starts generating guesses
    #
    def run(self, print_queue_info = False):
    
        # Start the clock
        self.total_time_start = time.perf_counter()
        
        ## Initalize the priority queue
        self.pqueue = PcfgQueue(self.pcfg)
        
        ## Set up the check to see if a user is pressing a button
        #
        user_input = [None]
        user_thread = threading.Thread(target=keypress, args=(user_input,))
        user_thread.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
        user_thread.start()
                            
        # Keep running while the p_queue.next_function still has items in it
        while True:
                  
            ## Check for user requested status output
            #
            if user_input[0] is not None:          
                self.display_status(guess_list = ["test","test2"])
                user_input[0] = None
                
                # Kick off again the thread to check if user_input was entered
                if not user_thread.is_alive():
                    user_thread = threading.Thread(target=keypress, args=(user_input,))
                    user_thread.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
                    user_thread.start()
                    
            ## Get the next item from the pqueue
            #
            pt_item = self.pqueue.next()
            
            # If the pqueue is empty, there are no more guesses to make
            if pt_item == None:
                print ("Done processing the PCFG. No more guesses to generate",file=sys.stderr)
                print ("Shutting down guessing session",file=sys.stderr)
                return
                
            self.num_parse_trees += 1
            
            try:
                self.num_guesses += self.pcfg.create_guesses(pt_item['pt'])
            
            # The receiving program is no longer accepting guesses
            # Usually occurs after all passwords have been cracked
            except OSError:
                break
            
            #print(self.num_guesses)
                               
        return
    

    ## Displays status of cracking session
    #
    def display_status(self, guess_list = []):
        print ("Status Report:",file=sys.stderr)
        if len(guess_list) != 0:
            print ("Currently generating guesses from " + str(guess_list[0]) + " to " + str(guess_list[-1]),file=sys.stderr)
        print ("Press [ENTER] to display an updated status output",file=sys.stderr)
        print("",file=sys.stderr)
   

## Used to check to see if a key was pressed to output program status
#
# *Hopefully* should work on multiple OSs
# --Simply check user_input_char to see if it is not none
#
def keypress(user_input_ref):
    user_input_ref[0] = input()

