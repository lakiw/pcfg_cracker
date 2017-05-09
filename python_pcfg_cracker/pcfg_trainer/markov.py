#!/usr/bin/env python3

import math
import os

#############################################################################
# This file contains the funcitonality to train a Markov model on the dataset
# Currently using the Markov approach implimented in John the Ripper
#############################################################################

##############################################################################
# Note on probabilities, (Taken from openwall.info/wiki/john/markov)
# If P(x) is the probability that x is the first letter of a password, and P(a|b) 
# the probability that b follows a, then for the word bull P(bull) = P(b)*P(u|b)*P(l|u)*P(l|l).
# When converting to integers by defining P'(x) = round(-10*log( P(x) )), 
# this becomes P'(bull) = P(b)+P'(u|b)+P'(l|u)+P'(l|l).
###############################################################################

###################################################################################
# Training class for Markov brute force implimentation
# Based on --markov mode in John the Ripper
# Trying to hide most of the mechanics from the calling process in the training
# program since I eventually want to replace this with an OMEN implementation
####################################################################################
class Markov:
    def __init__(self):
        
        # dictionary lookup for zero order and first order Markov items
        # Takes the form of
        #   'a':{
        #       'count':5, 
        #       'probability':5,
        #       'num_children':4,        
        #       'following_letters':{
        #           'b':{'count':2, 'probability':10},
        #           'c':{'count':2, 'probability':10},
        #       }
        self.probability_map = {}      
        
        # The total number of letters processed
        self.num_letters = 0
        
        # Holds the keysize for all of the ranks
        self.rank_results = []
    
    
    ###############################################################################
    # Simply grab counts of the zero order and first order Markov items for 
    # an individual password
    # Do not calculate probability at this stage
    ################################################################################
    def parse_password(self, input_password):
        
        ##--Loop through the input password
        for index, c in enumerate(input_password):

            ##--Take care of the zero order Markov items
            self.num_letters += 1
            
            ##--If we haven't seen that character before
            if c not in self.probability_map:
                self.probability_map[c] = {'count':1, 'following_letters':{}, 'num_children':0}
            
            ##--We have seen it before
            else:
                self.probability_map[c]['count'] += 1
                
            ##--Take care of the first order markov items
            ##-- If it is not the first item in the password
            if index != 0:
                prev_letter = input_password[index-1]
                self.probability_map[prev_letter]['num_children'] += 1
                
                ##--Haven't seen the second order yet
                if c not in self.probability_map[prev_letter]['following_letters']:
                    self.probability_map[prev_letter]['following_letters'][c] = {'count':1}
                
                ##-We have seen it before
                else:
                    self.probability_map[prev_letter]['following_letters'][c]['count'] += 1
        
        return True
        
    
    ##########################################################################################
    # Calculate the probabilities
    # Only do this after all the passwords have been parsed
    ##########################################################################################
    def calculate_probabilities(self):
        for item in self.probability_map.values():
            
            #--Calculate the zero order probability
            item['probability'] = round(-10 * math.log10(item['count'] / self.num_letters))
            
            ##--Handle edge case so no probabilities are 0--##
            ##--This is to prevent infinate loops so adding another character increases the count
            if item['probability'] == 0:
                item['probability'] = 1
                
            #--Calculate all the first order probabilities with this character as the starting point
            for child in item['following_letters'].values():
                child['probability'] = round(-10 * math.log10(child['count'] / item['num_children']))
            
            ##--Handle edge case so no probabilities are 0--##
            ##--This is to prevent infinate loops so adding another character increases the count
            if item['probability'] == 0:
                item['probability'] = 1
        
        self.calculate_keysize(max_rank=300,  max_length=16, max_keyspace=1000000000000)
        return True
    
    ################################################################################################
    # Save the stats file to disk
    # This may look a little weird, but saving it in the format JtR uses for their Markov mode
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
    #
    ################################################################################################
    def save_results(self, base_directory):
        
        with open(os.path.join(base_directory,'markov_stats'), 'w') as datafile:
            for index, item in self.probability_map.items():
                ##-Write out the zero order Markov stats
                datafile.write('%d=proba1[%d]\n' % (item['probability'], ord(index)))
                
                ##--Write out all the first order Markov stats
                for child_index, child in item['following_letters'].items():
                    datafile.write('%d=proba2[%d*256+%d]\n' % (child['probability'], ord(index), ord(child_index)))
        
        return True
        
    
    #####################################################################################################
    # Evaluates the ranking/probability of the input_password with the currently saved model
    # IMPORTANT: Should only be used after the base Markov grammar is trained
    ######################################################################################################
    def evaulate_ranking(self, input_password):
        ranking = 0
        try:
            for index, c in enumerate(input_password):
                if index == 0:
                    ranking = ranking + self.probability_map[c]['probability']
                else:
                    prev_letter = input_password[index -1 ]
                    ranking = ranking + self.probability_map[prev_letter]['following_letters'][c]['probability']
                    
        except KeyError as msg:
            print(input_password)
            print(msg)
            print("Shoudln't have hit this, did the coder make sure they only run evaluate_ranking after the Markov stats were fully finished?")
            return 0
        
        ##--Cap the ranking at 1000
        if ranking > 1000:
            return 1000
        
        #print(input_password + " : " + str(ranking))
        #print(ranking)
        
        return ranking
        
        
    #####################################################################################################################
    # Calculates the key size of a given Markov Range
    # IMPORTANT: Should only be used after the base Markov grammar is trained
    #####################################################################################################################
    def calculate_keysize(self, max_rank=1000,  max_length=12, max_keyspace = None):
        
        #######################################################################
        # Holds the probability of follow up letters with a specific rank left
        # {
        #     'LENGTH_LEFT': {
        #         'RANK': {
        #             'PREV_LETTER':COUNT,
        #             ...,
        #         },
        #         ...,
        #     }
        #     ...,
        # }
        # 
        # Example:
        # {
        #     8:{
        #         '10':{
        #             'a':101,
        #             'b':52,
        #         },
        #         '11':{
        #             'a':151,
        #             'b':53
        #         },
        #     }
        # }
        ########################################################################
        scratch_ranks = {}
        
        ##--Holds the results for all the ranks
        self.rank_results = []

        #print("Markov Key Sizes")
        
        ##--Loop through all the ranks--##
        for i in range(0,max_rank):
            num_passwords = 0
            ##--Handle the zero order markov probs
            for index, item in self.probability_map.items():
                if item['probability'] <= max_rank:                    
                    num_passwords += 1 + self.__recursive_calc_keysize(scratch_ranks, max_rank = (i - item['probability']), max_length = max_length - 1, prev_letter=index)
            self.rank_results.append(num_passwords)
            
            ##--Exit early if we hit the max keysize
            if max_keyspace != None and num_passwords > max_keyspace:
                break
                
            #print(str(i) + ":" + str(num_passwords))
     
     
    ############################################################################################
    # Recursivly goes through the first order Markov probabilities and helps calculate the keysize
    # for a given maximum rank and maximum length
    # Note, it saves the work in scratch_ranks since a lot of it is repeated over and over
    ############################################################################################    
    def __recursive_calc_keysize(self, scratch_ranks, prev_letter, max_rank=1000, max_length=8):
        
        ##--Exit if too long--##
        if max_length == 0:
            return 0
            
        ##--Check to see if the work has already been done or not--##
        if max_length not in scratch_ranks:
            scratch_ranks[max_length] = {}
        if max_rank in scratch_ranks[max_length]:
            if prev_letter in scratch_ranks[max_length][max_rank]:
                return scratch_ranks[max_length][max_rank][prev_letter]
        
        ##--Initialize max rank if needed
        else:
            scratch_ranks[max_length][max_rank] = {}
            
        ##--Now caluclulate the scratch_ranks[max_rank][prev_letter] value  
        num_passwords = 0        
        for index, item in self.probability_map[prev_letter]['following_letters'].items():
            if item['probability'] <= max_rank:
                num_passwords += 1 + self.__recursive_calc_keysize(scratch_ranks, prev_letter=index, max_rank = (max_rank - item['probability']), max_length = max_length - 1)
        
        scratch_ranks[max_length][max_rank][prev_letter] = num_passwords  
        
        return num_passwords