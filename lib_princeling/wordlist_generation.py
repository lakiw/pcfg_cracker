#!/usr/bin/env python3


###############################################################################
# Logic to create the PRINCE wordlist
#
###############################################################################


import sys
import os

# Local Imports
from lib_guesser.priority_queue import PcfgQueue


def create_prince_wordlist(pcfg, max_size, base_directory, output_file):
        
    pqueue = PcfgQueue(pcfg)
    
    # Number of words generated
    num_generated_guesses = 0
    
    print("creating wordlist",file=sys.stderr)
    
    # Keep running while the p_queue.next_function still has items in it
    while max_size == None or num_generated_guesses < max_size:
    
        ## Get the next item from the pqueue
        pt_item = pqueue.next()
        
        # If the pqueue is empty, there are no more guesses to make
        if pt_item == None:
            break
              
        # Create the words for the dictionary
        try:
            num_generated_guesses += pcfg.create_guesses(pt_item['pt'])
        
        # The receiving program is no longer accepting guesses
        except OSError:
            break
            
    print ("Done generating the PRINCE wordlist.",file=sys.stderr)
    return