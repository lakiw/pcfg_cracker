#!/usr/bin/env python3


#######################################################
# Unit tests for "other" string detection
#
# This is the default catch-all classification of strings
# not otherwise classified
#
#######################################################


import unittest
import unittest.mock


## Functions and classes to tests
#
from ..detection_rules.other_detection import other_detection


## Responsible for testing other string detection
#
# Note:
# + = positive test, (valid input handling)
# - = stress test, (invalid input handling) 
#
# ==Current Tests==
# + Test whole string is a other string
# + Test 1 character other string
# + Test alpha string followed by a other string
# + Test other string followed by an alpha string
# + Test no other strings
# + Test other string followed by alpha followed by another other string
#
class Test_Other_Checks(unittest.TestCase):


    ## Test the whole word is a other string
    #
    def test_whole_word_is_other_string(self):
    
        section_list = [('!@#$',None)]
        
        found_other_strings = other_detection(section_list)
        
        assert found_other_strings == ['!@#$']
        assert section_list == [('!@#$','O4')]
    
    
    ## Test 1 character other string
    #
    def test_one_character_digit_string(self):
    
        section_list = [('!',None)]
        
        found_other_strings = other_detection(section_list)
        
        assert found_other_strings == ['!']
        assert section_list == [('!','O1')]
        
        
    ## Test alpha string followed by an other string
    #
    def test_alpha_string_followed_by_an_other(self):
    
        section_list = [('chair','A5'),('!@#$',None)]
        
        found_other_strings = other_detection(section_list)
        
        assert found_other_strings == ['!@#$']
        assert section_list == [('chair','A5'),('!@#$','O4')]
        
        
    ## Test other string followed by an alpha string
    #
    def test_other_followed_by_a_alpha_string(self):
    
        section_list = [('!@#$',None),('chair','A5')]
        
        found_other_strings = other_detection(section_list)
        
        assert found_other_strings == ['!@#$']
        assert section_list == [('!@#$','O4'),('chair','A5')]
        
        
    ## Test no other strings
    #
    def test_no_other_strings(self):
    
        section_list = [('chair','A5')]
        
        found_other_strings = other_detection(section_list)
        
        assert found_other_strings == []
        assert section_list == [('chair','A5')]   
        
        
    ## Test other string followed by a alpha followed by another other string
    #
    def test_other_string_followed_by_alpha_followed_by_other_string(self):
    
        section_list = [('!@#$',None),('chair','A5'),('%^&*',None)]
        
        found_other_strings = other_detection(section_list)
        
        assert found_other_strings == ['!@#$','%^&*']
        assert section_list == [('!@#$','O4'),('chair','A5'),('%^&*','O4')]
        

