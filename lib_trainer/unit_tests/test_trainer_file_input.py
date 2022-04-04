#!/usr/bin/env python3


#######################################################
# Unit tests for reading in input from a training file
#
#######################################################


import unittest
import unittest.mock
import codecs


## Functions and classes to tests
#
from ..trainer_file_input import get_confirmation
from ..trainer_file_input import detect_file_encoding
from ..trainer_file_input import check_valid
from ..trainer_file_input import TrainerFileInput


## Responsible for testing the input from a training file
#
# Note:
# + = positive test, (valid input handling)
# - = stress test, (invalid input handling) 
#
# ==Current Tests==
# + get_confirmation: returns True
# + get_confirmation: returns False
#
# + detect_file_encoding: ASCII
# + detect_file_encoding: UTF-16
# + Check Valid password: valid password
# + Check Valid password: invalid password, blank
# + Check Valid password: invalid password, tab in password
# + Read Input Passwords (FULL): Check to make sure correct number are read
#
class Test_File_Input_Checks(unittest.TestCase):


    ## Verify get_confirmation returns True when user selects 'y'
    #
    def test_get_confirmation_returns_true(self):
        with unittest.mock.patch('builtins.input', return_value='y'):
            assert get_confirmation("test 'y' confirmation") == True
            
    
    ## Verify get_confirmation returns False when user selects 'n'
    #
    def test_get_confirmation_returns_false(self):
        with unittest.mock.patch('builtins.input', return_value='n'):
            assert get_confirmation("test 'n' confirmation") == False
            
   
    ## Verify detect_file_encoding for ASCII is overridden and returns UTF-8
    #
    def test_detect_file_encoding_ascii(self):
        
        test_data = "test1\ntest2\ntest3\n".encode('ascii')
        
        with unittest.mock.patch(
            'builtins.open', 
            unittest.mock.mock_open(read_data=test_data)
        ):
            possible_file_encodings = []     
            assert detect_file_encoding("test_file", possible_file_encodings) == True
            
            # Note, currently overriding ASCII to be utf-8 instead
            assert possible_file_encodings[0] == 'utf-8'
            
    
    ## Verify detect_file_encoding returns UTF-16
    #
    def test_detect_file_encoding_utf16(self):
        
        test_data = "test1\ntest2\ntest3\n".encode('utf16')
        
        with unittest.mock.patch(
            'builtins.open', 
            unittest.mock.mock_open(read_data=test_data)
        ):
            possible_file_encodings = []     
            assert detect_file_encoding("test_file", possible_file_encodings) == True
            assert possible_file_encodings[0] == 'UTF-16'
    

    ## Verify valid passwords are marked as valide
    #
    def test_check_valid_1(self):
        assert check_valid('password 1') == True
        
    ## Verify blank passwords are marked as invalid
    #
    def test_check_valid_2(self):
    
        # Check blank passwords
        assert check_valid('') == False

    
    ## Verify tabs in passwords are marked as invalid
    #
    def test_check_valid_2(self):
    
        assert check_valid('\tpassword') == False
        assert check_valid('pass\tword') == False
        assert check_valid('password\t') == False
        
    
    ## Verify that the right number of passwords are returned
    #
    # Also verify that duplicate detection is working
    # Input is slighly messy to simulate several failure modes
    #
    def test_read_input_passwords(self):
    
        # Set up input
        raw_test_data = "test1\n" \
            "test2\r\n" \
            "\r\n" \
            "invalid1\t" \
            "test3\n" \
            "\n" \
            "space1 \n" \
            " space2\n" \
            "sp ace3\n" \
            "duplicate\n" \
            "duplicate\r\r\n" \
            "test4"
        
        test_data = raw_test_data
        
        # Patch file open and read data
        with unittest.mock.patch(
            'codecs.open', 
            unittest.mock.mock_open(read_data=test_data)
        ):
        
            file_input = TrainerFileInput("test_file",'ascii')
        
            # Loop through all of the passwords
            password = file_input.read_password()
            while password:
                password = file_input.read_password()                     
            
        # Verify the number of passwords read and the raw results
        print("Num passwords:" + str(file_input.num_passwords))
        assert file_input.num_passwords == 8
        
        assert file_input.duplicates_found == True
            

if __name__ == '__main__':
    unittest.main()             