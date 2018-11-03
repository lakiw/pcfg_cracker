#!/usr/bin/env python3

import math
import os
from decimal import *
import copy

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
        
        # The number of passwords scored in the training when running them through the grammar again
        self.password_under_max = 0
        
        # The maximum rank to check
        self.max_rank = 1000
        
        # The probability distributed rank
        # Basically takes into account the keyspace + num passwords found
        self.prob_distributed_ranks = []
    
    
    ###############################################################################
    # Simply grab counts of the zero order and first order Markov items for 
    # an individual password
    # Do not calculate probability at this stage
    ################################################################################
    def parse_password(self, input_password):
        
        ##--Loop through the input password
        for index, c in enumerate(input_password):

            ##--Take care of the zero order Markov items
            ##--Note, I had a version that only trained on the actual first character for the zero order markov items
            ##--aka with 'abc' it would only assign a value to 'a' for the 0 order Markov.
            ##--That version did *worse* then the current one that assigns a 0 order value to every character, aka 'a', 'b', 'c'
            ##--Overtraining is a real problem to keep in mind.
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
            
            ##--First add all the rankings of the 0 order and 1st order Markov probabilities
            ##--Aka convert the counts of 'A|B' into ranks
            
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
                if child['probability'] == 0:
                    child['probability'] = 1
        
        ##--Now calculate the keysize of the different ranks
        ##--This is used later to figure out the probability of them, (and ultimatly when to use them in the PCFG)
        self.__calculate_keysize(max_rank=self.max_rank,  max_length=16, max_keyspace=1000000000000)
        return True
          
        
    #####################################################################################################################
    # Calculates the key size of a given Markov Range
    # IMPORTANT: Should only be used after the base Markov grammar is trained
    #####################################################################################################################
    def __calculate_keysize(self, max_rank=1000,  max_length=12, max_keyspace = None):
        
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
      
        ##--Loop through all the ranks--##
        for cur_rank in range(1,max_rank+1):
            num_passwords = 0
            ##--Handle the zero order markov probs
            for index, item in self.probability_map.items():
                if item['probability'] <= cur_rank:   
                    num_passwords += 1 + self.__recursive_calc_keysize(scratch_ranks, max_rank = (cur_rank - item['probability']), max_length = max_length - 1, prev_letter=index)
                    
            self.rank_results.append({'keysize':num_passwords, 'num_found':0, 'min_rank':cur_rank, 'max_rank':cur_rank})
                
            ##--Exit early if we hit the max keysize
            if max_keyspace != None and num_passwords > max_keyspace:
                break
     
        self.max_rank = len(self.rank_results)
     
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
        
        ##--Save the password if it would fall into our saved keyspace--##
        if ranking <= self.max_rank:
            self.rank_results[ranking-1]['num_found'] += 1
            self.password_under_max += 1
        ##--Cap the ranking at 1000
        if ranking > 1000:
            return 1000
        
        return ranking
        
        
    ##########################################################################################################
    # Returns the final sorted ranks
    ##########################################################################################################    
    def final_sorted_ranks(self, precision=7):
        
        ##--Calculate the final probability of the ranks and merge them if needed--##
        ##--This is a bit wonky now.
        ##--While the Markov grammar has its own probability (or ranking here) I don't want to use it
        ##--since there's a good chunk of passwords that will fall outside the keyspace that is feasable
        ##--to check. Therefore there's the previous step where we run through the passwords again and check
        ##--which effective rankings would actually crack therm
        ##--Also as counterintive as it may sound higher probablility Markov ranks may be less likely to
        ##--crack passwords than lower probablity productions. For example consider password length,
        ##-- 'a' as a password might be very very uncommon, but 'apple' would be more common. The Markov
        ##-- probability of 'a' though is gaurenteed to be higher than 'apple'. Yes we could impose min length
        ##-- limits, but we may want to try 'a' eventually.
        
        ##--First go through the list and merge rankings where no passwords were observed for them
        ##--Doing this because in the cracker I still want to bruteforce shorter key lengths for now
        scratch_list = []
        append_item = None
        for index, value in enumerate(self.rank_results):
            ##--Roll it up in the next rank
            if value['num_found'] == 0:
                if append_item == None:
                    append_item = copy.copy(value)

            ##--Create an item to sort
            else:
                if append_item == None:
                    append_item = copy.copy(value)
                else:
                    append_item['max_rank'] = value['max_rank']
                    append_item['num_found'] = value['num_found']
                    append_item['keysize'] = value['keysize']
                    
                ##--We want this item's keysize minus the items before this--##
                if append_item['min_rank'] != 1:
                    prev_keysize = self.rank_results[append_item['min_rank']-2]['keysize']
                    cur_keysize = self.rank_results[append_item['max_rank']-1]['keysize']
                    append_item['keysize'] = cur_keysize - prev_keysize
                    
                scratch_list.append(append_item)
                append_item = None
            
        ##--Don't worry about saving the last one if no items were found of that rank
        with localcontext() as ctx:
            ctx.prec = precision
  
            ##--Calculate the final probability
            for item in scratch_list:
                if item['keysize'] != 0:
                    item['final_prob'] = Decimal(item['num_found'] / (item['keysize'] * self.password_under_max)) * Decimal(1.0)
                else:
                    item['final_prob'] = Decimal(0)
        
        
        ##--Now sort it
        self.prob_distributed_ranks = sorted(scratch_list, key = lambda item: item['final_prob'], reverse = True)         
        
        return True
        
    
    ###############################################################################################
    # Save everything to disk
    ###############################################################################################
    def save_results(self, base_directory):
        ##--Save the Markov stats file (ranking) --##
        ##--This is the same as the stats file John the Ripper --Markov mode uses--##
        if not self.__save_stats_file(base_directory):
            return False
        
        ##--Now save the probabilities of the different ranks
        if not self.__save_probabilities_file(base_directory):
            return False
        
        ##--Save the keyspace info for Honeyword generation
        if not self.__save_keysize_file(base_directory):
            return False
        
    
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
    def __save_stats_file(self, base_directory):
        try:
            ##--Save the Markov stats file (ranking) --##
            ##--This is the same as the stats file John the Ripper --Markov mode uses--##
            with open(os.path.join(base_directory,'markov_stats.txt'), 'w') as datafile:
                for index in sorted(self.probability_map, key=lambda x: (self.probability_map[x]['probability'])):
                    datafile.write('%d=proba1[%d]\n' % (self.probability_map[index]['probability'], ord(index)))
                    
                    ##--Write out all the first order Markov stats
                    children = self.probability_map[index]['following_letters']
                    for child_index in sorted(children, key=lambda x: children[x]['probability']):
                        datafile.write('%d=proba2[%d*256+%d]\n' % (children[child_index]['probability'], ord(index), ord(child_index)))
        
        except:
            return False
            
        return True
    

    ########################################################################################################
    # Save the probability file for the Markov grammar
    # This is what is used in the actual PCFG to generate pre-terminals
    ###########################################################################################################
    def __save_probabilities_file(self, base_directory):
        try:
            with open(os.path.join(base_directory,'markov_prob.txt'), 'w') as datafile:
                for item in self.prob_distributed_ranks:
                    datafile.write(str(item['min_rank']) + ':' + str(item['max_rank']) + '\t' + str(item['final_prob']) + '\n')
        
        except:
            return False
        
        return True
        
    
    #############################################################################################################
    # Save the keysize for each rank of the Markov grammar
    # Used for honeyword generation and is not necessary for password guess generation
    #############################################################################################################
    def __save_keysize_file(self, base_directory):
        try:
            pass
            with open(os.path.join(base_directory,'markov_keyspace.txt'), 'w') as datafile:
                for item in self.prob_distributed_ranks:
                    datafile.write(str(item['min_rank']) + ':' + str(item['max_rank']) + '\t' + str(item['keysize']) + '\n')
        except:
            return False
                  
        return True