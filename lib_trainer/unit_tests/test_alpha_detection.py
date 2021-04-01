#!/usr/bin/env python3


#######################################################
# Unit tests for alpha character (letter) detection
#
#######################################################


import unittest
import unittest.mock


## Functions and classes to tests
#
from ..detection_rules.alpha_detection import alpha_detection
from ..detection_rules.multiword_detector import MultiWordDetector


## Responsible for testing alpha (letter) string detection
#
# Note:
# + = positive test, (valid input handling)
# - = stress test, (invalid input handling) 
#
# ==Current Tests==
# + Test whole string is an alpha string that is a base word
# + Test whole string is an alpha string that is not a base word
# + Test 1 character alpha string
# + Test first letter capitalized alpha string
# + Test last letter capitalized alpha string
# + Test alpha string followed by a digit
# + Test digit followed by an alpha string
# + Test no alpha strings
# + Test two word multiword alpha string
# + Test alpha followed by digit followed by another alpha string
#
class Test_Alpha_Checks(unittest.TestCase):

    ## Sets up a basic multi-word detector that many of the unit tests use
    #
    def set_up_multiword(self):
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
        
        return md


    ## Test the whole word is an alpha string that is also a base word
    #
    def test_whole_word_is_alpha_string_and_a_base_word(self):
    
        # Intitialize the multi-word detector
        md = self.set_up_multiword()
        
        section_list = [('chair',None)]
        
        found_alpha_strings, found_mask_list = alpha_detection(section_list, md)
        
        assert found_alpha_strings == ['chair']
        assert section_list == [('chair','A5')]
        assert found_mask_list == ['LLLLL']
    
    
    ## Test the whole word is an alpha string that is not a base word
    #
    def test_whole_word_is_alpha_string_and_not_a_base_word(self):
    
        # Intitialize the multi-word detector
        md = self.set_up_multiword()
        
        section_list = [('couch',None)]
        
        found_alpha_strings, found_mask_list = alpha_detection(section_list, md)
        
        assert found_alpha_strings == ['couch']
        assert section_list == [('couch','A5')]
        assert found_mask_list == ['LLLLL']
        
        
    ## Test 1 character alpha strings
    #
    def test_one_character_alpha_strings(self):
    
        # Intitialize the multi-word detector
        md = self.set_up_multiword()
        
        section_list = [('a',None)]
        
        found_alpha_strings, found_mask_list = alpha_detection(section_list, md)
        
        assert found_alpha_strings == ['a']
        assert section_list == [('a','A1')]
        assert found_mask_list == ['L']
        
        
    ## Test first character capitalized alpha strings
    #
    def test_first_character_capitalized_alpha_string(self):
    
        # Intitialize the multi-word detector
        md = self.set_up_multiword()
        
        section_list = [('Chair',None)]
        
        found_alpha_strings, found_mask_list = alpha_detection(section_list, md)
        
        assert found_alpha_strings == ['chair']
        assert section_list == [('Chair','A5')]
        assert found_mask_list == ['ULLLL']
        
        
    ## Test last character capitalized alpha strings
    #
    def test_last_character_capitalized_alpha_string(self):
    
        # Intitialize the multi-word detector
        md = self.set_up_multiword()
        
        section_list = [('chaiR',None)]
        
        found_alpha_strings, found_mask_list = alpha_detection(section_list, md)
        
        assert found_alpha_strings == ['chair']
        assert section_list == [('chaiR','A5')]
        print("FOUND MASK LIST :" + str(found_mask_list))
        assert found_mask_list == ['LLLLU']
        
        
    ## Test alpha string followed by a digit
    #
    def test_alpha_string_followed_by_a_digit(self):
    
        # Intitialize the multi-word detector
        md = self.set_up_multiword()
        
        section_list = [('chair6',None)]
        
        found_alpha_strings, found_mask_list = alpha_detection(section_list, md)
        
        assert found_alpha_strings == ['chair']
        assert section_list == [('chair','A5'),('6',None)]
        assert found_mask_list == ['LLLLL']
        
        
    ## Test digit followed by an alpha string
    #
    def test_digit_followed_by_a_alpha_string(self):
    
        # Intitialize the multi-word detector
        md = self.set_up_multiword()
        
        section_list = [('6chair',None)]
        
        found_alpha_strings, found_mask_list = alpha_detection(section_list, md)
        
        assert found_alpha_strings == ['chair']
        assert section_list == [('6',None),('chair','A5')]
        assert found_mask_list == ['LLLLL']
        
        
    ## Test no alpha strings
    #
    def test_no_alpha_strings(self):
    
        # Intitialize the multi-word detector
        md = self.set_up_multiword()
        
        section_list = [('1234',None)]
        
        found_alpha_strings, found_mask_list = alpha_detection(section_list, md)
        
        assert found_alpha_strings == []
        assert section_list == [('1234',None)]
        assert found_mask_list == []        
        
        
    ## Test two word multiword alpha string
    #
    def test_two_word_multiword(self):
    
        # Intitialize the multi-word detector
        md = self.set_up_multiword()
        
        section_list = [('chairtable',None)]
        
        found_alpha_strings, found_mask_list = alpha_detection(section_list, md)
        
        assert found_alpha_strings == ['chair','table']
        assert section_list == [('chair','A5'),('table','A5')]
        assert found_mask_list == ['LLLLL','LLLLL']
        
        
    ## Test alpha string followed by a digit followed by another alpha string
    #
    def test_alpha_string_followed_by_digit_followed_by_alpha_string(self):
    
        # Intitialize the multi-word detector
        md = self.set_up_multiword()
        
        section_list = [('chair6table',None)]
        
        found_alpha_strings, found_mask_list = alpha_detection(section_list, md)
        
        assert found_alpha_strings == ['chair','table']
        assert section_list == [('chair','A5'),('6',None),('table','A5')]
        assert found_mask_list == ['LLLLL','LLLLL']