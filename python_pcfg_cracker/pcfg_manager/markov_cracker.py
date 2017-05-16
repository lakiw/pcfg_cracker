#!/usr/bin/env python3

import sys
import os 

#########################################################################################################
# Contains all the logic for handling Markov guess generation for the pcfg_manager
# Based on --markov mode in John the Ripper
# Seperating this out since I expect to do more work later on refining how brute force generation is
# used in the grammar
#########################################################################################################


#####################################################################################
# Loads the Markov Stats from a file
# The stats file is a dictionary lookup for zero order and first order Markov items
# Takes the form of
#   'a':{
#       'count':5, 
#       'probability':5,
#       'num_children':4,        
#       'following_letters':{
#           'b':{'count':2, 'probability':10},
#           'c':{'count':2, 'probability':10},
#       }
######################################################################################
def load_markov_stats(rule_directory):
    print("Loading the Markov stats file",file=sys.stderr)

    markov_stats = {}

    filename = os.path.join(rule_directory, 'Markov', 'markov_stats.txt')
    try:
        # The stats file is in the format JtR uses for their Markov mode
        # Note, since this training program supports non-ascii characters this can produce stats files
        # not suited for JtR since it assumes a maximum of 256 characters
        #
        # Format:
        #    Probability=proba1[ORD_REP1]
        #    Probability=proba2[ORD_REP1*256+ORD_REP2]
        #
        # Example:
        #    27=proba1[97]                  //'a' has probability 27
        #    85=proba2[97*256+114]          //'r' given 'a' has a probability of 85
        #    83=proba2[97*256+100]          //'d' given 'a' has a probability of 83
        with open(filename, 'r') as file:
            for line in file:
                if 'proba1' in line:
                    results = line.strip().split("=proba1")
                    print (results)

    except Exception as msg:
        print (msg,file=sys.stderr)
        print ("Error opening file " + filename, file=sys.stderr)
        return None

    return markov_stats
