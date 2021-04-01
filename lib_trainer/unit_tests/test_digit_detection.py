#!/usr/bin/env python3


#######################################################
# Unit tests for digit string detection
#
#######################################################


import unittest
import unittest.mock


## Functions and classes to tests
#
from ..detection_rules.digit_detection import digit_detection


## Responsible for testing digit string detection
#
# Note:
# + = positive test, (valid input handling)
# - = stress test, (invalid input handling) 
#
# ==Current Tests==
# + Test whole string is a digit string
# + Test 1 character digit string
# + Test alpha string followed by a digit
# + Test digit followed by an alpha string
# + Test no digit strings
# + Test digit followed by alpha followed by another digit string
# + Test digit detection of a '0' to make sure None isn't causing issues
#
class Test_Digit_Checks(unittest.TestCase):


    ## Test the whole word is a digit string
    #
    def test_whole_word_is_digit_string(self):
    
        section_list = [('1234',None)]
        
        found_digit_strings = digit_detection(section_list)
        
        assert found_digit_strings == ['1234']
        assert section_list == [('1234','D4')]
    
    
    ## Test 1 character digit string
    #
    def test_one_character_digit_string(self):
    
        section_list = [('1',None)]
        
        found_digit_strings = digit_detection(section_list)
        
        assert found_digit_strings == ['1']
        assert section_list == [('1','D1')]
        
        
    ## Test alpha string followed by a digit
    #
    def test_alpha_string_followed_by_a_digit(self):
    
        section_list = [('chair1234',None)]
        
        found_digit_strings = digit_detection(section_list)
        
        assert found_digit_strings == ['1234']
        assert section_list == [('chair',None),('1234','D4')]
        
        
    ## Test digit followed by an alpha string
    #
    def test_digit_followed_by_a_alpha_string(self):
    
        section_list = [('1234chair',None)]
        
        found_digit_strings = digit_detection(section_list)
        
        assert found_digit_strings == ['1234']
        assert section_list == [('1234','D4'),('chair',None)]
        
        
    ## Test no digit strings
    #
    def test_no_digit_strings(self):
    
        section_list = [('chair',None)]
        
        found_digit_strings = digit_detection(section_list)
        
        assert found_digit_strings == []
        assert section_list == [('chair',None)]   
        
        
    ## Test digit string followed by a alpha followed by another digit string
    #
    def test_digit_string_followed_by_alpha_followed_by_digit_string(self):
    
        section_list = [('1234chair5678',None)]
        
        found_digit_strings = digit_detection(section_list)
        
        assert found_digit_strings == ['1234','5678']
        assert section_list == [('1234','D4'),('chair',None),('5678','D4')]


    ## Test digit detection of a 0
    #
    def test_zero_string(self):
    
        section_list = [('0',None)]
        
        found_digit_strings = digit_detection(section_list)
        
        assert found_digit_strings == ['0']
        assert section_list == [('0','D1')]          