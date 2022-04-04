#!/usr/bin/env python3


#######################################################
# Unit tests for year_detection
#
#######################################################


import unittest
import unittest.mock


## Functions and classes to tests
#
from ..detection_rules.year_detection import year_detection


## Responsible for testing the year detection
#
# Note:
# + = positive test, (valid input handling)
# - = stress test, (invalid input handling) 
#
# ==Current Tests==
# + Test whole password being a year
# + Test two years in a password seperated by a string
# + Test non-year 4 digit number is not classified as a year
# + Test digit before date so don't classify it as a year
# + Test digit after date so don't classify it as a year
# + Test 1920 followed by 2019
# + Test 2019 followed by 1920
#
class Test_Year_Checks(unittest.TestCase):

    ## Test whole password being a year
    #
    def test_whole_password_is_a_year(self):
    
        section_list = [('2019',None)]
        found_years = year_detection(section_list)
        
        assert found_years == ['2019']
        assert section_list == [('2019','Y1')]
        
        
    ## Test two years in a password seperated by a string
    #
    def test_two_years(self):
    
        section_list = [('2018pass2019',None)]
        found_years = year_detection(section_list)
        
        assert found_years == ['2018','2019']
        assert section_list == [('2018','Y1'),('pass',None),('2019','Y1')]
        
        
    ## Test non-year 4 digit number that is not classified as a year
    #
    def test_non_year_digits(self):
    
        section_list = [('1234',None)]
        found_years = year_detection(section_list)
        
        assert found_years == []
        assert section_list == [('1234',None)]
    

    ## Test 5 digits where the last four digits are a year so don't classify it
    #
    def test_five_digits_start(self):
    
        section_list = [('12019',None)]
        found_years = year_detection(section_list)
        
        assert found_years == []
        assert section_list == [('12019',None)]
        
        
    ## Test 5 digits where the first four digits are a year so don't classify it
    #
    def test_five_digits_end(self):
    
        section_list = [('20191',None)]
        found_years = year_detection(section_list)
        
        assert found_years == []
        assert section_list == [('20191',None)]
        
        
    ## Test 1920 followed by 2019
    #
    def test_1920_then_2019(self):
    
        section_list = [('1920pass2019',None)]
        found_years = year_detection(section_list)
        
        assert found_years == ['1920','2019']
        assert section_list == [('1920','Y1'),('pass',None),('2019','Y1')]
        
        
    ## Test 2019 followed by 1920
    #
    def test_2019_then_1920(self):
    
        section_list = [('2019pass1920',None)]
        found_years = year_detection(section_list)
        assert found_years == ['1920','2019']
        assert section_list == [('2019','Y1'),('pass',None),('1920','Y1')]