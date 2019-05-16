#!/usr/bin/env python3

################################################################################
#
# Name: Status Report
# Description: Responsible for tracking statistcs and printing status reports
#
################################################################################


import sys


## Used to keep track of a gussing session's status
#
class StatusReport:

    ## Basic initialization function
    #
    def __init__(self, pcfg = None):
    
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
        
        # Current pt_item that is being processed
        self.pt_item = None
        
        # OMEN levels processed
        # Keeping this as a list since it can skip OMEN levels depending on
        # training
        self.past_omen_levels = []
        
        # Probability Coverage
        # See https://github.com/lakiw/pcfg_cracker/issues/9
        self.probability_coverage = 0
        
    
    ## Prints a status report to stderr
    #
    def print_status(self, pcfg):
        
        # Banner
        print("Status Report:",file=sys.stderr)
        
        # Past Guessing Status
        print("Total Guesses (Approximate): " + str(self.num_guesses),file=sys.stderr)
        print("Number of Pre-Terminals (Rules) Processed: " + str(self.num_parse_trees),file=sys.stderr)
        print("Probability Coverage: " + str(self.probability_coverage),file=sys.stderr)
        
        # Omen statistics
        if self.past_omen_levels:
            print("OMEN (Markov Brute-Force) Levels Processed: " + str(self.past_omen_levels),file=sys.stderr)
        
        # Current Guessing Status
        if self.pt_item != None:
        
            # Need to copy pt_item so it doesn't get modified while being printed
            static_pt_item = self.pt_item
            print("Current Probabilty of Guesses: " + str(static_pt_item['prob']),file=sys.stderr)
            print("Current Pre-Terminal (Rule): " + str(static_pt_item['pt']),file=sys.stderr)
            pcfg.print_status(static_pt_item['pt'])