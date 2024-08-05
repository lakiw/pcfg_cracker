#!/usr/bin/env python3


"""

This file contains the functionality to load rules/grammar from a saved file

"""


import sys
import os
import configparser
import json
import codecs
from collections import Counter


def load_grammar(grammar, rule_directory):
    """
    Loads the grammar from a ruleset.

    Note, not using the normal pcfg_guesser grammar loader since that
    doesn't load info that we will need for essentially 're-stemming' the
    input words to score

    Inputs:
        grammar: The pcfg grammar object to save the results in

        rule_directory: The file directory of the rule/grammar

    Returns:
        True: If the grammar was loaded sucessfully

        False: If an error occured
    """

    # Read the top level config file for the grammar
    config = configparser.ConfigParser()

    try:
        config.read_file(open(os.path.join(rule_directory,"config.ini")))

        # Find the encoding for the config file
        grammar.encoding = config.get('TRAINING_DATASET_DETAILS','encoding')

        # Load the values for the grammar

        # Load Years
        filename = os.path.join(rule_directory, 'Years', '1.txt')
        if not _load_from_file(grammar.count_years, filename, grammar.encoding):
            return False

        # Load context sensitive replacements
        filename = os.path.join(rule_directory, 'Context', '1.txt')
        if not _load_from_file(grammar.count_context_sensitive, filename, grammar.encoding):
            return False

        # Load base structures
        filename = os.path.join(rule_directory, 'Grammar', 'grammar.txt')
        if not _load_from_file(grammar.count_base_structures, filename, grammar.encoding):
            return False

        # Load keyboard structures
        if not _load_from_multiple_files(grammar.count_keyboard, config['BASE_K'], rule_directory, grammar.encoding):
            return False

        # Load alpha strings
        if not _load_from_multiple_files(grammar.count_alpha, config['BASE_A'], rule_directory, grammar.encoding):
            return False

        # Load alpha string masks (aka capitalizatoin masks)
        if not _load_from_multiple_files(grammar.count_alpha_masks, config['CAPITALIZATION'], rule_directory, grammar.encoding):
            return False

        # Load digits
        if not _load_from_multiple_files(grammar.count_digits, config['BASE_D'], rule_directory, grammar.encoding):
            return False

        # Load "other" structures. E.g. punctuation
        if not _load_from_multiple_files(grammar.count_other, config['BASE_O'], rule_directory, grammar.encoding):
            return False

    except IOError as msg:
        print("Could not open the config file for the ruleset specified. The rule directory may not exist")
        print(f"Ruleset: {rule_directory}")
        return False
    except configparser.Error as msg:
        print(f"Error occured parsing the configuration file: {msg}")
        return False

    return True


def _load_from_multiple_files(grammar_counter, config, rule_directory, encoding):
    """
    Loads grammar information from multiple files for length specified terminals

    Inputs:
        grammar_counter: Python Counter. Used to keep track of terminals of specified length

        config: The ruleset/grammar's config file which is used to identify what files
        to load.

        rule_directory: The base directory where the ruleset/grammar is located

        encoding: What file encoding to load the ruleset/grammar as.

    Returns:
        True: If everything was loaded ok

        False: If an error occured loading the ruleset
    """

    directory = config.get('directory')

    filenames = json.loads(config.get('filenames'))

    for file in filenames:
        full_path = os.path.join(rule_directory, directory, file)

        length = int(file.split('.')[0])

        grammar_counter[length] = Counter()

        if not _load_from_file(grammar_counter[length], full_path, encoding):
            return False

    return True


def _load_from_file(grammar_counter, filename, encoding):
    """
    Loads grammar information from a file

    Inputs:
        grammar_counter: Python Counter. Used to keep track of terminals of specified length

        filename: The full path + filename to load from

        encoding: What file encoding to load the ruleset/grammar as.

    Returns:
        True: If everything was loaded ok

        False: If an error occured loading the ruleset
    """

    # Try to open the file
    try:
        with codecs.open(filename, 'r', encoding= encoding, errors= 'surrogateescape') as file:

            # Read though all the lines in the fil
            for value in file:

                # There "shouldn't" be encoding errors in the rules files, but
                # might as well check to be on the safe side
                try:
                    value.encode(encoding)

                except UnicodeEncodeError as msg:
                    if msg.reason == 'surrogates not allowed':
                        num_encoding_errors = num_encoding_errors + 1
                    else:
                        print("Hmm, there was a weird problem reading in a line from the rules file",file=sys.stderr)
                        print('',file=sys.stderr)
                    continue

                # Split up the tab seperated items and then save their values
                split_values = value.rstrip().split("\t")
                grammar_counter[split_values[0]] = float(split_values[1])

    except IOError as error:
        print (error,file=sys.stderr)
        print ("Error opening file " + filename ,file=sys.stderr)
        return False

    except Exception as error:
        print (error,file=sys.stderr)
        return False

    return True
