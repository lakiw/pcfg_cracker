#!/usr/bin/env python3


#############################################################################
# This file contains the functionality to parse raw passwords for PCFGs
#
# The PCFGPasswordParser class is designed to be instantiated once and then
# process one password at at time that is sent to it
#
#############################################################################


import sys

# Local imports
from .leet_detector import LeetDetector
from .keyboard_walk import detect_keyboard_walk
from .email_detection import email_detection
from .website_detection import website_detection
from .year_detection import year_detection
from .context_sensitive_detection import context_sensitive_detection
from .alpha_detection import alpha_detection
from .digit_detection import digit_detection


## Responsible for parsing passwords to train a PCFG grammar
#
class PCFGPasswordParser:


    ## Initializes the class and all the data structures
    #
    # multiword_detector: A previously trained multi word detector
    #                      that has had the base_words established for it
    #
    def __init__(self, multiword_detector):
    
        # Save the multiword detector
        self.multiword_detector = multiword_detector
        
        # Initialize Leet Speak Detector
        self.leet_detector = LeetDetector(self.multiword_detector)
        
        ## Used for debugging/statistics
        #
        # These numbers won't add up to total passwords parsed since
        # some passwords might have multiple "base words". For example
        # "pass1pass" would be counted as two single words. Likewise,
        # "123456" would have no words
        #
        self.num_single_words = 0
        self.num_multi_words = 0
        
        # Keep track of the number of leet replacements detected
        self.num_leet = 0
        
    
    ## Main function called to parse an individual password
    #
    # Returns:
    #    True: If everything worked correctly
    #    False: If there was a problem parsing the password
    #
    def parse(self, password):

        # Since keyboard combos can look like many other parsings, filter them
        # out first
        
        section_list, found_list = detect_keyboard_walk(password)
        
        # Identify e-mail and web sites before doing other string parsing
        # this is because they can have digits + special characters
        
        found_emails, found_providers = email_detection(section_list)       
        found_urls, found_hosts, found_prefixes = website_detection(section_list)
        
        # Identify years in the dataset. This is done before other parsing
        # because parsing after this may classify years as another type
        
        found_years = year_detection(section_list)
        
        # Need to classify context sensitive replacements before doing the
        # straight type classifications, (alpha, digit, etc), but want to doing
        # it after other types of classifations.
        
        found_context_sensitive_strings = context_sensitive_detection(section_list)
        
        # Identify pure alpha strings in the dataset
        
        found_alpha_strings, found_mask_list = alpha_detection(section_list, self.multiword_detector)
        
        # Identify pure digit strings in the dataset
        
        found_digit_strings = digit_detection(section_list)
        
        if found_digit_strings:
            print(str(password) + " " + str(found_digit_strings) + " : " + str(section_list))
        
        #if found_alpha_strings:
        #    print(str(password) + " " + str(found_alpha_strings) + " : " + str(section_list))
        
        #if found_urls:
        #    print(str(password) + " " + str(found_urls) + " : " + str(found_hosts))
        
        #if found_years:
        #    print(str(password) + " " + str(found_years))
        
        #if found_context_sensitive_strings:
        #    print(str(password) + " : " + str(found_context_sensitive_strings))
        
        return True