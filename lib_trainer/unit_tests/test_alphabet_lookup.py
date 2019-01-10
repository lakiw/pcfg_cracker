#!/usr/bin/env python3


#######################################################
# Unit tests for the AlphabetLookup
#
#######################################################


import unittest
import unittest.mock


## Functions and classes to tests
#
from ..omen.alphabet_lookup import AlphabetLookup


## Responsible for testing the the AlphabetLookup
#
# Note:
# + = positive test, (returns valid response)
# - = stress test, (expected to throw exception or return invalid response)
#
# ==Current Tests==
# + Test is_in_alphabet for both matches and not matches
# + Test that invalid length passwords are not counted when parsed
# + Test basic parse of two passwords
#
class Test_Alphabet_Lookup_Checks(unittest.TestCase):

    ## Test to make sure the check to see if a ngram is in an alphabet works
    #
    def test_is_in_alphabet(self):
        omen_trainer = AlphabetLookup(
            alphabet = "abcd",
            ngram = 4,
            min_length = 2,
            max_length = 8
        )
        
        # Ngram is in alphabet
        assert omen_trainer.is_in_alphabet("bbad") == True

        # Ngram is not in alphabet
        assert omen_trainer.is_in_alphabet("gbad") == False
        
        # Ngram is not in alphabet
        assert omen_trainer.is_in_alphabet("bgad") == False
        
        # Ngram is not in alphabet
        assert omen_trainer.is_in_alphabet("bbag") == False
            

    ## Test invalid length passwords are not counted when parsed
    #
    def test_parse_invalid_length(self):
        omen_trainer = AlphabetLookup(
            alphabet = "abcd",
            ngram = 4,
            min_length = 2,
            max_length = 8
        )
        
        # Too small
        omen_trainer.parse("a")
        assert omen_trainer.ln_counter == 0
        
        # Too large
        omen_trainer.parse("abcdabcda")
        assert omen_trainer.ln_counter == 0

    
    ## Test to make sure parsing a ngram not in the alphabet isn't counted
    #
    def test_parse_two_passwords(self):
        omen_trainer = AlphabetLookup(
            alphabet = "abcd",
            ngram = 3,
            min_length = 2,
            max_length = 8
        ) 
        
        omen_trainer.parse("abcd")
        omen_trainer.parse("abbc")
        
        # Check the IP count
        assert omen_trainer.grammar['ab']['ip_count'] == 2
        
        # Check the CP count for ab
        assert omen_trainer.grammar['ab']['next_letter']['c'] == 1
        assert omen_trainer.grammar['ab']['next_letter']['b'] == 1
        