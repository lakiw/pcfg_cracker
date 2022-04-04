#!/usr/bin/env python3


"""
This file contains the functionality to parse raw passwords for PCFGs

The PCFGPasswordParser class is designed to be instantiated once and then
process one password at at time that is sent to it

"""


from collections import Counter

# Local imports
from .detection_rules.leet_detector import LeetDetector
from .detection_rules.keyboard_walk import detect_keyboard_walk
from .detection_rules.email_detection import email_detection
from .detection_rules.website_detection import website_detection
from .detection_rules.year_detection import year_detection
from .detection_rules.context_sensitive_detection import context_sensitive_detection
from .detection_rules.alpha_detection import alpha_detection
from .detection_rules.digit_detection import digit_detection
from .detection_rules.other_detection import other_detection
from .base_structure import base_structure_creation
from .prince_metrics import prince_evaluation


class PCFGPasswordParser:
    """
    Responsible for parsing passwords to train a PCFG grammar

    This is designed to be created once, and then to process one password at
    a time.
    """

    def __init__(self, multiword_detector):
        """
        Initializes the class and all the data structures

        Inputs:
            multiword_detector: A previously trained multi word detector
            that has had the base_words established for it

        Returns:
            PCFGPasswordParser
        """

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

        ## The following counters keep track of global running stats
        #
        self.count_keyboard = {}
        self.count_emails = Counter()
        self.count_email_providers = Counter()
        self.count_website_urls = Counter()
        self.count_website_hosts = Counter()
        self.count_website_prefixes = Counter()
        self.count_years = Counter()
        self.count_context_sensitive = Counter()
        self.count_alpha = {}
        self.count_alpha_masks = {}
        self.count_digits = {}
        self.count_other = {}
        self.count_base_structures = Counter()
        self.count_raw_base_structures = Counter()
        self.count_prince = Counter()

    def parse(self, password):
        """
        Main function called to parse an individual password

        Inputs:
            password: (String) The password to parse

        Returns:
            True: If everything worked correctly

            False: If there was a problem parsing the password
        """

        # Since keyboard combos can look like many other parsings, filter them
        # out first

        section_list, found_walks = detect_keyboard_walk(password)

        self._update_counter_len_indexed(self.count_keyboard, found_walks)

        # Identify e-mail and web sites before doing other string parsing
        # this is because they can have digits + special characters

        found_emails, found_providers = email_detection(section_list)

        for email in found_emails:
            self.count_emails[email] += 1
        for provider in found_providers:
            self.count_email_providers[provider] += 1

        found_urls, found_hosts, found_prefixes = website_detection(section_list)

        for url in found_urls:
            self.count_website_urls[url] += 1
        for host in found_hosts:
            self.count_website_hosts[host] += 1
        for prefix in found_prefixes:
            self.count_website_prefixes[prefix] += 1

        # Identify years in the dataset. This is done before other parsing
        # because parsing after this may classify years as another type

        found_years = year_detection(section_list)

        for year in found_years:
            self.count_years[year] += 1

        # Need to classify context sensitive replacements before doing the
        # straight type classifications, (alpha, digit, etc), but want to doing
        # it after other types of classifations.

        found_context_sensitive_strings = context_sensitive_detection(section_list)

        for cs_string in found_context_sensitive_strings:
            self.count_context_sensitive[cs_string] += 1

        # Identify pure alpha strings in the dataset

        found_alpha_strings, found_mask_list = alpha_detection(
            section_list,
            self.multiword_detector
            )

        self._update_counter_len_indexed(self.count_alpha, found_alpha_strings)
        self._update_counter_len_indexed(self.count_alpha_masks, found_mask_list)

        # Identify pure digit strings in the dataset

        found_digit_strings = digit_detection(section_list)

        self._update_counter_len_indexed(self.count_digits, found_digit_strings)

        # Categorize everything else as other

        found_other_strings = other_detection(section_list)

        self._update_counter_len_indexed(self.count_other, found_other_strings)

        # Calculate the counts of the individual sections for PRINCE dictionary
        # creation

        prince_evaluation(self.count_prince, section_list)

        # Now after all the other parsing is done, create the base structures

        is_supported, base_structure = base_structure_creation(section_list)

        if is_supported:
            self.count_base_structures[base_structure] += 1

        self.count_raw_base_structures[base_structure] += 1

        return True

    def _update_counter_len_indexed(self, input_counter, input_list):
        """
        Updates a Python Counter object when the item is lenght indexed

        For example, if the individual counts are broken up by length of input
        Aka A1 = 'a', A3 = 'cat', A5 = 'chair'

        Inputs:
            self: Since this is a class private function

            input_counter: (Counter) The Python Counter object to update

            input_list: (List) A list of items to update in the counter

        Returns:
            None
        """

        # Go through every item in the list to insert it in the counter
        for item in input_list:
            # First try a blind insertion into the list
            try:
                input_counter[len(item)][item] +=1

            # If that length index doesn't exist, it'll throw an exception some
            # now create it
            except:
                input_counter[len(item)] = Counter()
                input_counter[len(item)][item] +=1
