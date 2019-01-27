#!/usr/bin/env python3


#######################################################
# Unit tests for base structure creation
#
#######################################################


import unittest
import unittest.mock


## Functions and classes to tests
#
from ..base_structure import base_structure_creation


## Responsible for testing base structure creation
#
# Note:
# + = positive test, (valid input handling)
# - = stress test, (invalid input handling) 
#
# ==Current Tests==
# + Test one item for base structure
# + Test two items for base structure
# + Test not supported base structure
#
class Test_Base_Structure_Checks(unittest.TestCase):


    ## Test one item is a base structure
    #
    def test_one_item_base_structure(self):
    
        section_list = [('chair','A5')]
        
        is_supported, base_structure = base_structure_creation(section_list)
        
        assert is_supported == True
        assert base_structure == "A5"
        
        
    ## Test two items for a base structure
    #
    def test_two_item_base_structure(self):
    
        section_list = [('chair','A5'),('1234','D4')]
        
        is_supported, base_structure = base_structure_creation(section_list)
        
        assert is_supported == True
        assert base_structure == "A5D4"
        
        
    ## Test unsupported base structure
    #
    def test_unsupported_base_structure(self):
    
        section_list = [('chair','A5'),('www.reusablesec.blogspot.com', 'W')]
        
        is_supported, base_structure = base_structure_creation(section_list)
        
        assert is_supported == False
        assert base_structure == "A5W"
    