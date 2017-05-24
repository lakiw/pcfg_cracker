#!/usr/bin/env python3

import sys
import os 

#########################################################################################################
# Contains all the logic for handling Markov guess generation for the pcfg_manager
# Based on --markov mode in John the Ripper
# Seperating this out since I expect to do more work later on refining how brute force generation is
# used in the grammar
#########################################################################################################
class MarkovCracker:

    ############################################################################################
    # Initializes the cracker
    # If rule directory is none, then the cracker will basically act as a noop
    ############################################################################################
    def __init__(self, rule_directory = None):
        self.markov_stats = {}
        self.start_letter = None
        
        if rule_directory != None:
            if not self.load_markov_stats(rule_directory):
                raise
        
        ##Used for guess generation
        self.min_level = None
        self.max_level = None
        self.guess = None
        self.guess_level = 0
        
        
    #####################################################################################
    # Loads the Markov Stats from a file
    # The stats file is a dictionary lookup for zero order and first order Markov items
    # Creating a form similar to OrderedDictionary so we can have a "next" function to
    # generate the next guess after the previous one in a repetable way
    # Takes the form of
    #   'a':{
    #       'probability':5,
    #       'next': 'b',
    #       'first_child':'a',
    #       'last_child':'b',    
    #       'following_letters':{
    #           'a':{'probability':10, 'next':'b'},
    #           'b':{'probability':10, 'next':None},
    #       }
    ######################################################################################
    def load_markov_stats(self, rule_directory):
        print("Loading the Markov stats file",file=sys.stderr)

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
                prev_proba1 = None
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
                        self.markov_stats[letter] = {'probability':prob, 'following_letters':{}, 'first_child':None, 'last_child':None, 'next':None}
                        
                        ##--Update the OrderedDictionary like links
                        if self.start_letter == None:
                            self.start_letter = letter
                        
                        if prev_proba1 != None:
                            self.markov_stats[prev_proba1]['next'] = letter
                        prev_proba1 = letter
                                               
                    elif '=proba2' in line:
                        results = line.strip().split("=proba2[")
                        prob = int(results[0])
                        results = results[1].split('*256+')
                        letter1 = chr(int(results[0]))
                        letter2 = chr(int(results[1][:-1]))
                        self.markov_stats[letter1]['following_letters'][letter2] = {'probability':prob, 'next':None}
                        
                        ##--Update the OrderedDictionary like links
                        #-Do the 1st order Markov links
                        if self.markov_stats[letter1]['last_child'] != None:
                            self.markov_stats[letter1]['following_letters'][self.markov_stats[letter1]['last_child']]['next'] = letter2
                        
                        #-Do the 0 order Markov links
                        if self.markov_stats[letter1]['first_child'] == None:
                            self.markov_stats[letter1]['first_child'] = letter2
                        self.markov_stats[letter1]['last_child'] = letter2
                                                             
                    else:
                        print('Invalid line in Markov stats file')
                        print(line)
                        return None

        except Exception as msg:
            print (msg,file=sys.stderr)
            print ("Error opening file " + filename, file=sys.stderr)
            return None

        return True

        
    ################################################################################
    # Generate password guesses using Markov thresholds
    # Currently returns them as a list
    # Will want to change that in the future in case the list grows too bit, (it will)
    # Returns the guesses generated
    #################################################################################
    def generate_markov_guesses(self, min_level = 0, max_level = 1000):
        ##--handle the zero order markov level--##
        guesses = []
        for index, item in self.markov_stats.items():
            if item['probability'] <= max_level:
                ##--If it is above min level, generate a guess of just the first letter
                if item['probability'] >= min_level:
                    guesses.append(index)

                ##--Now do the the 1st order markov transitions
                guesses.extend(self.__recursive_markov_guesses(min_level = min_level, max_level = max_level, 
                    cur_level= item['probability'], prev_string = index ))
                
        return guesses
        
        
    ########################################################################################
    # Recursivly loops through the 1st order Markov transitions and generates guesses
    # Should only be called from generate_markov_guesses
    #########################################################################################
    def __recursive_markov_guesses(self, min_level = 0, max_level = 1000, 
        cur_level= 0, prev_string = 'a'):
        
        guesses = []
        for index, item in self.markov_stats[prev_string[-1]]['following_letters'].items():
            combined_rank = cur_level + item['probability']
            if combined_rank <= max_level:
                ##--If it is above min level, generate a guess
                if combined_rank >= min_level:
                    guesses.append(prev_string + index)
               
                ##--Now do additional 1st order markov transitions
                guesses.extend(self.__recursive_markov_guesses(min_level = min_level, max_level = max_level, 
                    cur_level= combined_rank, prev_string = (prev_string + index) ))
        
        return guesses
        
        
    ############################################################################################
    # Create a new guess generation session with a minimum and maximum rank thresholds
    # This should occur before creating guesses
    ############################################################################################
    def initialize_cracking_session(self, min_level = 0, max_level = 1000):
        self.min_level = min_level
        self.max_level = max_level
        self.guess = None
        self.guess_level = 0
     
     
    ###############################################################################################
    # Generates the "next" guess from this model
    # Will return None when no more guesses are left to be created
    ###############################################################################################    
    def next_guess(self):
        
        ##--Deal with starting off the Markov chain
        if self.guess == None:
            self.guess = [self.start_letter]
            self.guess_level = self.markov_stats[self.start_letter]['probability']
            
            if self.guess_level >= self.min_level and self.guess_level <= self.max_level:
                return ''.join(self.guess)
                    
        while True:
            ##--Loop through the following letter probabilities first
            while True:
                prev_letter = self.guess[-1]
                cur_letter = self.markov_stats[prev_letter]['first_child']
                self.guess_level += self.markov_stats[prev_letter]['following_letters'][cur_letter]['probability']
                self.guess.append(cur_letter)
                
                if self.guess_level >= self.min_level and self.guess_level <= self.max_level:
                    return ''.join(self.guess)
                
                ##--We dug too deep, went too far, unleashed the eldritch horrors                
                elif self.guess_level > self.max_level:
                    break

            ##--Now back out and try other letters at the same depth, or lower
            while True:
                prev_letter = self.guess.pop()
                
                ##--If it is the first letter in the chain
                ##--Check it see if the list (guess) is empty
                if not self.guess:
                    cur_letter = self.markov_stats[prev_letter]['next']
                    
                    ##--If we are done with all of the letters
                    if cur_letter == None:
                        self.guess = None
                        return None
                        
                    self.guess_level = self.markov_stats[cur_letter]['probability']
                    self.guess.append(cur_letter)
                    
                    if self.guess_level >= self.min_level and self.guess_level <= self.max_level:
                        return ''.join(self.guess)
                    
                    ##--Must dig deeper              
                    elif self.guess_level < self.max_level:
                        break
                
                ##--If we are looking at the 1st Markov Order probabilities
                else:
                    ##--Update the guess level to account for the missing children
                    self.guess_level = self.guess_level - self.markov_stats[self.guess[-1]]['following_letters'][prev_letter]['probability']
                    
                    cur_letter = self.markov_stats[self.guess[-1]]['following_letters'][prev_letter]['next']
                    
                    ##--No more children at this level, dig deeper
                    if cur_letter == None:
                        continue
                        
                    ##--Update the probability with the new item
                    self.guess_level += self.markov_stats[self.guess[-1]]['following_letters'][cur_letter]['probability']
                    
                    self.guess.append(cur_letter)
                    
                    if self.guess_level >= self.min_level and self.guess_level <= self.max_level:
                        return ''.join(self.guess)
                        
                    ##--Must dig deeper              
                    elif self.guess_level < self.max_level:
                        break
            
            
        return None
        