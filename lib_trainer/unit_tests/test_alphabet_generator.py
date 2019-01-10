#!/usr/bin/env python3


#######################################################
# Unit tests for the AlphabetGenerator
#
#######################################################


import unittest
import unittest.mock


## Functions and classes to tests
#
from ..omen.alphabet_generator import AlphabetGenerator


## Responsible for testing the the AlphabetGenerator
#
# Note:
# + = positive test, (valid input handling)
# - = stress test, (invalid input handling) 
#
# ==Current Tests==
# + Test proper handling when found alphabet is less than max alphabet size
# + Test on password shorter than ngram:
# + Test most frequent letter appears with max size = 1 in one pw
# + Test most frequent letter appears with max size = 1 in multiple pws
#
class Test_Alphabet_Generator_Checks(unittest.TestCase):

    ## Test proper handling when found alphabet is less than max alphabet size
    #
    def test_alphabet_shorter_than_max(self):
        ag = AlphabetGenerator(100,4)
        ag.process_password("abcd")
        assert len(ag.get_alphabet()) == 4


    ## Verify passwords shorter than ngram do not get measured
    #
    def test_pw_shorter_than_ngram(self):
        ag = AlphabetGenerator(10,4)
        ag.process_password("abc")
        
        assert len(ag.get_alphabet()) == 0
        
        
    ## Test most frequent letter appears with max size = 1 in one pw
    #
    def test_frequent_letter_in_one_pw(self):
        ag = AlphabetGenerator(1,4)
        ag.process_password("abca")
        
        assert ag.get_alphabet() == "a"
        
    
    ## Test most frequent letter appears with max size = 1 in multiple pws
    #
    def test_frequent_letter_in_multiple_pws(self):
        ag = AlphabetGenerator(1,4)
        ag.process_password("abcd")
        ag.process_password("defg")
        
        assert ag.get_alphabet() == "d"
            