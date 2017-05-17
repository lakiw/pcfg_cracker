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
#       'probability':5,     
#       'following_letters':{
#           'b':{'probability':10},
#           'c':{'probability':10},
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
                ##--Handle the 0 order Markov
                if '=proba1' in line:
                    ##--Yes this parsing is a bit hackish. It would be easy if I saved
                    ##--the data in a different format but I want to maintian compatability with
                    ##--JtR's stat file format
                    results = line.strip().split("=proba1[")
                    results[1] = results[1][:-1]
                    letter = chr(int(results[1]))
                    prob = int(results[0])
                    
                    ##--Save the result in the dictionary
                    markov_stats[letter] = {'probability':prob, 'following_letters':{}}
                
                elif '=proba2' in line:
                    results = line.strip().split("=proba2[")
                    prob = int(results[0])
                    results = results[1].split('*256+')
                    letter1 = chr(int(results[0]))
                    letter2 = chr(int(results[1][:-1]))
                    markov_stats[letter1]['following_letters'][letter2] = {'probability':prob}
                         
                else:
                    print('Invalid line in Markov stats file')
                    print(line)
                    return None

    except Exception as msg:
        print (msg,file=sys.stderr)
        print ("Error opening file " + filename, file=sys.stderr)
        return None

    return markov_stats

    
################################################################################
# Generate password guesses using Markov thresholds
# Currently returns them as a list
# Will want to change that in the future in case the list grows too bit, (it will)
# Returns the guesses generated
#################################################################################
def generate_markov_guesses(markov_stats, min_level = 0, max_level = 1000):
    ##--handle the zero order markov level--##
    guesses = []
    for index, item in markov_stats.items():
        if item['probability'] <= max_level:
            ##--If it is above min level, generate a guess of just the first letter
            if item['probability'] >= min_level:
                guesses.append(index)

            ##--Now do the the 1st order markov transitions
            guesses.extend(__recursive_markov_guesses(markov_stats, min_level = min_level, max_level = max_level, 
                cur_level= item['probability'], prev_string = index ))
            
    return guesses
    
    
########################################################################################
# Recursivly loops through the 1st order Markov transitions and generates guesses
# Should only be called from generate_markov_guesses
#########################################################################################
def __recursive_markov_guesses(markov_stats, min_level = 0, max_level = 1000, 
    cur_level= 0, prev_string = 'a'):
    
    guesses = []
    for index, item in markov_stats[prev_string[-1]]['following_letters'].items():
        combined_rank = cur_level + item['probability']
        if combined_rank <= max_level:
            ##--If it is above min level, generate a guess
            if combined_rank >= min_level:
                guesses.append(prev_string + index)
           
            ##--Now do additional 1st order markov transitions
            guesses.extend(__recursive_markov_guesses(markov_stats, min_level = min_level, max_level = max_level, 
                cur_level= combined_rank, prev_string = (prev_string + index) ))
    
    return guesses