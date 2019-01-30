#!/usr/bin/env python3


#######################################################
# Unit tests for calculating probabilities
#
# Note, as different probability smoothing is applied
# these tests will need to be modified heavily
#
#######################################################


import unittest
import unittest.mock
from collections import Counter

## Functions and classes to tests
#
from ..calculate_probabilities import calculate_probabilities

## Responsible for testing the probability calculations for the trainer code
#
# Note:
# + = positive test, (valid input handling)
# - = stress test, (invalid input handling) 
#
# ==Current Tests==
# + Test no items in the counter
# + Test one item
# + Test two items with equal counts
# + Test two items with different counts
#
class Test_Calculate_Probabilities(unittest.TestCase):


    ## Tests no items in the counter
    #
    # Aka, makes sure there is no divide by 0 or other wackyness going on
    #
    def test_no_items_in_counter(self):
    
        # Intitialize the counter
        counter = Counter()
        
        prob_list = calculate_probabilities(counter)
        
        assert prob_list == []

    
    ## Tests one item in the counter
    #
    # Aka, makes sure the probability is 1.0
    #
    def test_one_item_in_counter(self):
    
        # Intitialize the counter
        counter = Counter()
        
        counter['chair'] = 5
        
        prob_list = calculate_probabilities(counter)

        assert prob_list == [('chair',1.0)]
        
        
    ## Test two items with equal counts
    #
    # Result should be they should each have a prob of 0.5
    #
    def test_two_items_with_same_count(self):
    
        # Intitialize the counter
        counter = Counter()
        
        counter['chair'] = 5
        counter['table'] = 5
        
        prob_list = calculate_probabilities(counter)
        
        # Need to sort the lists, because otherwise the order can vary
        validate_list = [('chair',0.5), ('table',0.5)]
        
        validate_list.sort()
        prob_list.sort()

        assert prob_list == validate_list
        
        
    ## Test two items with different counts
    #
    def test_two_items_with_different_counts(self):
    
        # Intitialize the counter
        counter = Counter()
        
        counter['chair'] = 90
        counter['table'] = 10
        
        prob_list = calculate_probabilities(counter)
        
        validate_list = [('chair',0.9), ('table',0.1)]

        assert prob_list == validate_list