#!/usr/bin/env python3


#######################################################
# Unit tests for multiword detection
#
#######################################################


import unittest
import unittest.mock


## Functions and classes to tests
#
from ..detection_rules.multiword_detector import MultiWordDetector


## Responsible for testing multi-word detection
#
# Note:
# + = positive test, (valid input handling)
# - = stress test, (invalid input handling) 
#
# ==Current Tests==
# + Test _get_count sub-function
# + Test _identify_multi sub-function
# + Test whole password is two multiwords
# + Test word is not a multiword
# + Test word is not a multiword even though it is a base word
#
class Test_Multiword_Checks(unittest.TestCase):


    ## Test _get_count subfunction
    #
    def test_get_count(self):
    
        # Intitialize the multi-word detector
        md = MultiWordDetector(
            threshold = 2,
            min_len = 4,
            max_len = 21)
        
        # Train the multiword detector
        md.train('chair')
        md.train('chair')
        md.train('table')
        md.train('table')
        md.train('table')
        
        assert md._get_count('chair') == 2
        assert md._get_count('table') == 3
        assert md._get_count('couch') == 0
        
        
    ## Test _identify_multi subfunction
    #
    def test_identify_multi(self):
    
        # Intitialize the multi-word detector
        md = MultiWordDetector(
            threshold = 2,
            min_len = 4,
            max_len = 21)
        
        # Train the multiword detector
        md.train('chair')
        md.train('chair')
        md.train('table')
        md.train('table')
        md.train('table')
        
        assert md._identify_multi('chairtable') == ['chair','table']
        assert md._identify_multi('chairtablecouch') ==  None
        

    ## Test whole word is two multiwords
    #
    def test_whole_password_is_two_multiwords(self):
    
        # Intitialize the multi-word detector
        md = MultiWordDetector(
            threshold = 2,
            min_len = 4,
            max_len = 21)
        
        # Train the multiword detector
        md.train('chair')
        md.train('chair')
        md.train('table')
        md.train('table')
        
        is_parsed, strings = md.parse('chairtable')
        
        assert is_parsed == True
        assert strings == ['chair', 'table']
        
    
    ## Test that word is not classified as a multiword
    #
    def test_word_is_not_multiword(self):
        # Intitialize the multi-word detector
        md = MultiWordDetector(
            threshold = 2,
            min_len = 4,
            max_len = 21)
        
        # Train the multiword detector
        md.train('chair')
        md.train('chair')
        md.train('table')
        md.train('table')
        
        is_parsed, strings = md.parse('couch')
        
        assert is_parsed == False
        assert strings == ['couch']
        
        
    ## Test that word is not classified as a multiword even though it is a base word
    #
    def test_word_is_not_multiword_even_when_a_single_base_word(self):
        # Intitialize the multi-word detector
        md = MultiWordDetector(
            threshold = 2,
            min_len = 4,
            max_len = 21)
        
        # Train the multiword detector
        md.train('chair')
        md.train('chair')
        md.train('table')
        md.train('table')
        
        is_parsed, strings = md.parse('chair')
        
        assert is_parsed == True
        assert strings == ['chair']
    
    
        