#!/usr/bin/env python3

################################################################################
#
# Name: PCFG_Cracker Cracking Management Code
# Description: Manages a cracking session
#
#              Making this a class to help support different guess generation
#              modes in the future
#
################################################################################


import sys
import traceback
import time
import threading ##--Used only for the "check for user input" threads

# Local imports
from .priority_queue import PcfgQueue
from .status_report import StatusReport


## Used to manage a password cracking session
#
class CrackingSession:
    
    
    ## Basic initialization function
    #
    def __init__(self, pcfg = None):
    
        # Initalize the status report class for providing debugging and
        # status information
        self.report = StatusReport()
    
        # Save the grammar for easy reference
        self.pcfg = pcfg
        
        
    ## Starts the cracking session and starts generating guesses
    #
    def run(self):
        
        
        # Start the clock
        self.report.total_time_start = time.perf_counter()
        
        ## Initalize the priority queue
        self.pqueue = PcfgQueue(self.pcfg)
        
        ## Set up the check to see if a user is pressing a button
        #
        user_thread = threading.Thread(target=keypress, args=(self.report, self.pcfg))
        user_thread.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
        user_thread.start()
                            
        # Keep running while the p_queue.next_function still has items in it
        while True:
                
            # Check to see if the program should exit based on user input
            if not user_thread.is_alive():
                print("Exiting...")
                break
                
            ## Get the next item from the pqueue
            #
            pt_item = self.pqueue.next()
            
            # If the pqueue is empty, there are no more guesses to make
            if pt_item == None:
                print ("Done processing the PCFG. No more guesses to generate",file=sys.stderr)
                print ("Shutting down guessing session",file=sys.stderr)
                return
                
            self.report.num_parse_trees += 1
            self.report.pt_item = pt_item
          
            try:
                num_generated_guesses = self.pcfg.create_guesses(pt_item['pt'])
                self.report.num_guesses += num_generated_guesses
                
                self.report.probability_coverage += pt_item['prob'] * num_generated_guesses
            
            # The receiving program is no longer accepting guesses
            # Usually occurs after all passwords have been cracked
            except OSError:
                break
                            
        return
    

## Used to check to see if a key was pressed to output program status
#
# *Hopefully* should work on multiple OSs
# --Simply check user_input_char to see if it is not none
#
def keypress(report, pcfg):
    while True:
        user_input = input()
        
        # Display the status report
        report.print_status(pcfg)
        
        # If the program should exit
        if user_input == 'q':
            print( "",file=sys.stderr)
            print ("Exit command received",file=sys.stderr)
            print ("Will exit after finishing processing current pre-terminal",file=sys.stderr)
            print ("Note: If this takes too long, you can also use CTRL-C",file=sys.stderr)
            print ("",file=sys.stderr)
            return
        
        print( "",file=sys.stderr)
        print ("Press [ENTER] to display an updated status output",file=sys.stderr)
        print ("Press 'q' [ENTER] to exit",file=sys.stderr)
        print( "",file=sys.stderr)
        
        

