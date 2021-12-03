#!/usr/bin/env python3


"""

This file contains the functionality to parse raw passwords for PCFGs

The PCFGPasswordScorer class is designed to be instantiated once and then
process one password at at time that is sent to it

Note: This class is based heavily on /lib_trainer/pcfg_password_parser

"""


from collections import Counter

# Local imports
from lib_trainer.detection_rules.keyboard_walk import detect_keyboard_walk
from lib_trainer.detection_rules.email_detection import email_detection
from lib_trainer.detection_rules.website_detection import website_detection
from lib_trainer.detection_rules.year_detection import year_detection
from lib_trainer.detection_rules.context_sensitive_detection import context_sensitive_detection
from lib_trainer.detection_rules.alpha_detection import alpha_detection
from lib_trainer.detection_rules.digit_detection import digit_detection
from lib_trainer.detection_rules.other_detection import other_detection
from lib_trainer.base_structure import base_structure_creation
from lib_trainer.detection_rules.multiword_detector import MultiWordDetector
from .omen_scorer import OmenScorer


class PCFGPasswordScorer:
    """
    Responsible for holding the Grammar and evaluating inputs against it
    """

    def __init__(self, limit = 0):
        """
        Initializes the class and all the data structures

        Inputs:
            limit: The probability limit of grammar to cut-off
            a submitted value as being categorized as a password

        Returns:
            PCFGPasswordScorer
        """

        # The encoding to use when reading in the grammar
        self.encoding = None

        # The probability limit to cut-off being categorized as a password
        self.limit = limit

        # The following counters hold the base grammar
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

        # Will actually be defined later in the
        # create_multiword_detector function
        self.multiword_detector = None

        # Will actually be defined later in the
        # create_omen_scorer function
        self.omen = None
        self.max_omen_level = 0

    def create_multiword_detector(self):
        """
        Initializes the multiword detector

        Inputs:
            None

        Returns:
            None
        """

        # Minimum length of a word that is part of a multi-word
        min_len = 4

        # Create the multi-word detector. Since we'll be training it on base words
        # that have already been extracted, can set the threshold to 1 and only
        # parse words we want to be part of a multiword
        self.multiword_detector = MultiWordDetector(threshold = 1, min_len = min_len)

        # Go through all of the alpha strings to register them as potential multi-word values
        for key, value in self.count_alpha.items():
            if key >= min_len:

                # Will go through list in reverse order so we can skip the lowest
                # occurence items and not mark them as potential base values for
                # multiwords
                prob_list = reversed(value.most_common())

                skipped = 0
                prev_prob = 0.0

                for item in prob_list:
                    if skipped < 5:
                        if item[1] > prev_prob:
                            skipped += 1
                            prev_prob = item[1]

                    else:
                        self.multiword_detector.train(item[0])

    def create_omen_scorer(self, base_directory, max_omen_level):
        """
        Initializes the OMEN level parser

        Inputs:
            base_directory: The main rules folder where the grammar is saved

            max_omen_level: The maximum OMEN level to use when evaluating abs
            potential password

        Returns:
            None
        """

        self.max_omen_level = max_omen_level

        # Create the OmenScorer object to parse using OMEN Markov
        self.omen = OmenScorer(base_directory, self.encoding, max_omen_level)

    def parse(self, password):
        """
        Parses an input value and determines if it is a password or not

        Inputs:
            password: A string that is being evaluated to see if it appears
            to be a password

        Returns:
            (password, category, probability, omen_score)

            password: The password that was passed into this via the inputs

            category: The category the input value was assigned
                category = [pewo]
                    p = password
                    e = e-mail
                    w = website
                    o = other

            probability: The PCFG probability of the input value according to
            the pcfg grammar used

            omen_score: The OMEN level at which the input value would be generated
            at. If there is no valid OMEN parsing, it will be set to '-1'
        """

        # Parse the OMEN score
        omen_score = self.omen.parse(password)

        # Since keyboard combos can look like many other parsings, filter them
        # out first
        section_list, found_walks = detect_keyboard_walk(password)

        found_emails, found_providers = email_detection(section_list)
        found_urls, found_hosts, found_prefixes = website_detection(section_list)

        # Identify if e-mails or urls were found
        if found_emails:
            category = 'e'
        elif found_urls:
            category = 'w'
        else:
            category = 'o'

        # Bail out early if e-mails or websites were found
        if category in ['e', 'w']:
            return (password, category, 0, omen_score)

        found_years = year_detection(section_list)
        found_context_sensitive_strings = context_sensitive_detection(section_list)
        found_alpha_strings, found_mask_list = alpha_detection(section_list, self.multiword_detector)
        found_digit_strings = digit_detection(section_list)
        found_other_strings = other_detection(section_list)
        is_supported, base_structure = base_structure_creation(section_list)

        # Quick bail out if the base structure is not supported
        # This shouldn't happen since we are already bailing out if there are
        # websites or e-mails, but in the future more values may be added
        # that don't translate well
        #
        if not is_supported:
            category = 'o'
            return (password, category, 0, omen_score)

        # Find the probability for all of the transitions and values
        # Start out at 100% probability
        cur_prob = 1.0

        # Note, for the Python counters if a key is not found, it returns a
        # '0' vs a KeyError exception. Since a probability of 0 is what we
        # are looking for if that happens, that's perfect. This can still
        # throw KeyError exceptions though for the length indexed counters if
        # no item at that length is found. Therefore we still need to catch
        # KeyErrors
        try:
            for item in found_walks:
                cur_prob *= self.count_keyboard[len(item)][item]

            for item in found_years:
                cur_prob *= self.count_years[item]

            for item in found_context_sensitive_strings:
                cur_prob *= self.count_context_sensitive[item]

            for item in found_alpha_strings:
                cur_prob *= self.count_alpha[len(item)][item]

            for item in found_mask_list:
                cur_prob *= self.count_alpha_masks[len(item)][item]

            for item in found_digit_strings:
                cur_prob *= self.count_digits[len(item)][item]

            for item in found_other_strings:
                cur_prob *= self.count_other[len(item)][item]

            cur_prob *= self.count_base_structures[base_structure]

        except KeyError:
            cur_prob = 0

        # Classify it as a password if the probablility is higher than the
        # PCFG cut-off limit OR the OMEN score is equal to or below the OMEN
        # cut-off limit
        #
        if cur_prob > self.limit or omen_score <= self.omen.max_omen_level:
            category = 'p'

        return (password, category, cur_prob, omen_score)
