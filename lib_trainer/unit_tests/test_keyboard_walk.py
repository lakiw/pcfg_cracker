#!/usr/bin/env python3


#######################################################
# Unit tests for the Keyboard_Walk detection
#
#######################################################


import unittest
import unittest.mock


## Functions and classes to tests
#
from ..detection_rules.keyboard_walk import detect_keyboard_walk


## Responsible for testing the the Keyboard Walk Detection
#
# Note:
# + = positive test, (valid input handling)
# - = stress test, (invalid input handling) 
#
# ==Current Tests==
# + Test single keyboard walk
# + Test two keyboard walks
# + Test no keyboard walkds
# + Test keyboard walk and no keyboard walk
# + Test no keyboard walk and keyboard walk
#
class Test_Keyboard_Walk_Checks(unittest.TestCase):

    ## Test the full password is a keyboard walk
    #
    def test_single_keyboard_walk(self):
        section_list, found_list, keyboard_list = detect_keyboard_walk("1qaz")
        
        assert section_list == [('1qaz', 'K4')]
        assert found_list == ['1qaz']

        
    ## Test two back to back keyboard walks
    #
    def test_single_keyboard_walk(self):
        section_list, found_list, keyboard_list = detect_keyboard_walk("1qaz2wsx")
      
        assert section_list == [('1qaz', 'K4'),('2wsx', 'K4')]
        assert found_list == ['1qaz','2wsx']
        
        
    ## Test no keyboard walks
    #
    def test_no_keyboard_walks(self):
        section_list, found_list, keyboard_list = detect_keyboard_walk("test123test123")

        assert section_list == [('test123test123', None)]
        assert found_list == []

        
    ## Test keyboard walk and non-keyboard walk
    #
    def test_keyboard_walk_no_keyboard_walk(self):
        section_list, found_list, keyboard_list = detect_keyboard_walk("1qaztest123")

        assert section_list == [('1qaz', 'K4'),('test123', None)]
        assert found_list == ['1qaz']
        
    
    ## Test non-keyboard walk and then keyboard-walk
    #
    def test_no_keyboard_walk_keyboard_walk(self):
        section_list, found_list, keyboard_list = detect_keyboard_walk("test1231qaz")
        
        assert section_list == [('test123', None),('1qaz', 'K4')]
        assert found_list == ['1qaz']
        
        
    ## Test invalid keyboard walk + some non-keyboard walks
    #
    def test_invalid_keyboard_walk_and_non_keyboard_walk(self):
        section_list, found_list, keyboard_list = detect_keyboard_walk("tty789test")

        assert section_list == [("tty789test", None)]
        assert found_list == []
