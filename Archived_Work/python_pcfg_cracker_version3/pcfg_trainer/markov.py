#!/usr/bin/env python3

from .omen.alphabet_generator import AlphabetGenerator

#############################################################################
# This file contains the functionality to train a Markov model on the dataset
# Currently using OMEN as the Markov enumerator
#############################################################################

###################################################################################
# Training class for Markov brute force implementation
# Currently using OMEN as the Markov enumerator
# 
# Values:
#   alphabet_size: The number of characters to save
#                  to the alphabet
#   ngram: The ngram count for this grammar
#          Used to identify the minimum size of passwords
#          to train on
#####################################################
class Markov:
    def __init__(self, alphabet_size=100, ngram=4):
        
        self.alphabet_size = alphabet_size
        self.ngram = ngram
        
        ##--The alphabet to use for Markov generation of strings
        ##--Currently this will be over-ridden by the dynamically learned alphabet, but putting the default standard ASCII here in
        ##--case the calling function doesn't want to generate that
        self.alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!.*@-_$#<?'
        
        ##--The alphabet generator, used to dynamically learn what characters to include in the Markov generation
        self.ag = AlphabetGenerator(alphabet_size = self.alphabet_size, ngram = self.ngram)

        
    ######################################################################################
    # Learns the alphabet for setting the underlying Markov based model
    # Aka 'abcdef...'. Making this dynamic to support non-ASCII datasets
    #
    # This will need to be run before parsing the password normally
    #
    ######################################################################################
    def learn_alphabet(self, input_password):
        self.ag.process_password(input_password)
        
        
    def finalize_alphabet(self):
        self.alphabet = self.ag.get_alphabet()


    ###############################################################################
    # Simply grab counts of the zero order and first order Markov items for 
    # an individual password
    # Do not calculate probability at this stage
    ################################################################################
    def parse_password(self, password):
        
        return True
        
    
    ##########################################################################################
    # Calculate the probabilities
    # Only do this after all the passwords have been parsed
    ##########################################################################################
    def calculate_probabilities(self):

        return True
         
        
    ###############################################################################################
    # Save everything to disk
    ###############################################################################################
    def save_results(self, base_directory):
        
        return True
        