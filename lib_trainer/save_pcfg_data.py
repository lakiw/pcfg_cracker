#!/usr/bin/env python3


"""
Saves data relating to the PCFG cracker to disk

This also calls functions to calculate the statistics and apply prob smoothing

"""


import os
import codecs

# Local imports
from .calculate_probabilities import calculate_probabilities


def calculate_and_save_counter(filename, item_counter, encoding):
    """
    Saves data for an individual Python Counter of pcfg data

    Inputs:
        filename: (String) The full path and filename to save the data to disk

        item_counter: (Counter) The counter containing all of the data for this
        particular item to save.

        encoding: (String) The encoding to save the data as. Aka 'ascii'

    Returns:
        True: If it completed successfully

        False: If any errors occured

    """

    prob_list = calculate_probabilities(item_counter)

    # Note, if there is no items, just write an empty file anyways. That
    # will simplify the logic in the pcfg_manager than needs to use these
    # rules
    #
    try:
        with codecs.open(filename, 'w', encoding= encoding) as datafile:
            for item in prob_list:
                datafile.write(str(item[0]) + '\t' + str(item[1])+'\n')

    except Exception as msg:
        print("Exception : " + str(msg))
        return False

    return True


def save_indexed_counters(folder, counter_list, encoding):
    """
    Cleans up a rules directory and saves length indexed Python counter objects

    Inputs:
        folder: (String) The full path to the folder to save the data to

        counter_list: (List[Counter]) A list of length indexed counters

        encoding: (String) The encoding to save the data as. Aka 'ascii'

    Returns:
        True: If it completed successfully

        False: If any errors occured

    """

    # Delete files in this folder if they already exist
    #
    # I know, I could delete the whole folder structure in Rules instead, but
    # I want to reduce the potential damage if I mess this up so I'm not
    # deleting directories
    try:
        for root, dirs, files in os.walk(folder):
            for filename in files:
                os.unlink(os.path.join(root, filename))
    except Exception as msg:
        print("Exception : " + str(msg))
        return False

    # Loop through all the different length indexed items and save each one
    for index, item in counter_list.items():
        filename = os.path.join(folder, str(index) + ".txt")
        if not calculate_and_save_counter(filename, item, encoding):
            return False

    return True


def save_pcfg_data(base_directory, pcfg_parser, encoding, save_sensitive):
    """
    Saves data stored in a pcfg_parser to disk

    This is the top level function to call to save all of the pcfg data to disk

    Inputs:

        base_directory: The base directory to save the data to

        pcfg_parser: Contains all of the statistics in Python counters

        encoding: The encoding to save the data as

    Returns:
        True: If it completed successfully

        False: If any errors occured

    """

    ## Save keyboard data
    #

    folder = os.path.join(base_directory, "Keyboard")

    if not save_indexed_counters(folder, pcfg_parser.count_keyboard, encoding):
        return False

    ## Save e-mail data
    #

    folder = os.path.join(base_directory, "Emails")

    email_grouping = {'email_providers':pcfg_parser.count_email_providers}

    # Only save them if the user specified to save sensitive data
    if save_sensitive:
        email_grouping['full_emails'] = pcfg_parser.count_emails

    if not save_indexed_counters(folder, email_grouping, encoding):
        return False

    ## Save website data
    #

    folder = os.path.join(base_directory, "Websites")

    # Delete files in this folder if they already exist

    website_grouping = {
        'website_hosts':pcfg_parser.count_website_hosts,
        'website_prefixes': pcfg_parser.count_website_prefixes}

    # Only save raw websites if the user specified to save sensitive data
    if save_sensitive:
        website_grouping['website_urls'] = pcfg_parser.count_website_urls

    if not save_indexed_counters(folder, website_grouping, encoding):
        return False

    ## Save year data
    #
    folder = os.path.join(base_directory, "Years")

    year_grouping = {'1': pcfg_parser.count_years}

    if not save_indexed_counters(folder, year_grouping, encoding):
        return False

    ## Save context sensitive data
    #
    folder = os.path.join(base_directory, "Context")

    context_grouping = {'1':pcfg_parser.count_context_sensitive}

    if not save_indexed_counters(folder, context_grouping, encoding):
        return False

    ## Save Alpha strings
    #
    folder = os.path.join(base_directory, "Alpha")

    if not save_indexed_counters(folder, pcfg_parser.count_alpha, encoding):
        return False

    ## Save Capitalization Masks
    #
    folder = os.path.join(base_directory, "Capitalization")

    if not save_indexed_counters(folder, pcfg_parser.count_alpha_masks, encoding):
        return False

    ## Save Digits
    #
    folder = os.path.join(base_directory, "Digits")

    if not save_indexed_counters(folder, pcfg_parser.count_digits, encoding):
        return False

    ## Save Other
    #
    folder = os.path.join(base_directory, "Other")

    if not save_indexed_counters(folder, pcfg_parser.count_other, encoding):
        return False

    ## Save Base Structures
    #
    folder = os.path.join(base_directory, "Grammar")

    grammar_grouping = {
        'grammar': pcfg_parser.count_base_structures,
        'raw_grammar':pcfg_parser.count_raw_base_structures
        }

    # Note, saving these as ASCII since there may not be representations for
    # the base structure categories in the training file encoding
    if not save_indexed_counters(folder, grammar_grouping, 'ASCII'):
        return False

    ## Save PRINCE data
    #
    folder = os.path.join(base_directory, "Prince")

    prince_grouping = {
        'grammar':pcfg_parser.count_prince,
    }

    # Note, saving these as ASCII since there may not be representations for
    # the base structure categories in the training file encoding
    if not save_indexed_counters(folder,prince_grouping, 'ASCII'):
        return False

    return True
