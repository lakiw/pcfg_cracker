#!/usr/bin/env python3


"""

Responsible for running the top level training session

Moving this here to get it out of the main() function

"""

import sys
import traceback
from collections import Counter

# Local imports
from lib_trainer.trainer_file_input import TrainerFileInput

from lib_trainer.omen.alphabet_generator import AlphabetGenerator
from lib_trainer.omen.alphabet_lookup import AlphabetLookup
from lib_trainer.omen.omen_file_output import save_omen_rules_to_disk
from lib_trainer.omen.evaluate_password import find_omen_level
from lib_trainer.omen.evaluate_password import calc_omen_keyspace

from lib_trainer.detection_rules.multiword_detector import MultiWordDetector

from lib_trainer.pcfg_password_parser import PCFGPasswordParser

from lib_trainer.config_file import save_config_file
from lib_trainer.save_pcfg_data import save_pcfg_data
from lib_trainer.print_statistics import print_statistics

from lib_trainer.trainer_file_input import get_confirmation


def run_trainer(program_info, base_directory):
    """
    Currently runs three passes through the training dataset and generates
    the resulting grammar.

    This function is also responsible for saving the grammar to disk

    Variables:
        program_info: A dictionary containing all of the command line
        option results

        base_directory: The base directory to save the resulting grammar to


    Return:
        True: If the operations completed sucessfully
        False: If any errors occured
    """

    ## Perform the first pass of the training list
    #
    # This pass is responsible for the following:
    #
    # -Identifying number of passwords trained on
    # -Identifying OMEN alphabet
    # -Duplicate password detection, (duplicates are good!)
    #
    print("-------------------------------------------------")
    print("Performing first pass on the training passwords")
    print("-------------------------------------------------")
    print("")

    # Initialize the file input to read passwords from
    file_input = TrainerFileInput(
                    program_info['training_file'],
                    program_info['encoding'])

    # Initialize the alphabet generator to learn the alphabet
    alpha_gen = AlphabetGenerator(program_info['alphabet_size'], program_info['ngram'])

    # Intitialize the multi-word detector
    multiword_detector = MultiWordDetector(
                            threshold = 5,
                            min_len = 4,
                            max_len = 21)

    # Used for progress_bar
    num_parsed_so_far = 0
    print("Printing out status after every million passwords parsed")
    print("------------")

    ## Loop until we hit the end of the file
    try:
        password = file_input.read_password()
        while password:

            # Print status indicator if needed
            num_parsed_so_far += 1
            if num_parsed_so_far % 1000000 == 0:
                print(str(num_parsed_so_far//1000000) +' Million')

            # Save statistics for the alphabet
            alpha_gen.process_password(password)

            # Train multiword detector
            multiword_detector.train(password)

            # Get the next password
            password = file_input.read_password()

    except Exception as msg:
        print("Exception: " + str(msg))
        return False

    # Save the learned alphabet
    program_info['alphabet'] = alpha_gen.get_alphabet()

    # Record how many valid passwords there were
    num_valid_passwords = file_input.num_passwords

    if num_valid_passwords == 0:
        print()
        print("Error, no valid passwords were found when attempting to train ruleset.")
        return False

    # Print some basic statistics after first loop
    print()
    print("Number of Valid Passwords: " + str(num_valid_passwords))
    print("Number of Encoding Errors Found in Training Set:" + str(file_input.num_encoding_errors))
    print()

    # Perform duplicate detection and warn user if no duplicates were found
    if not file_input.duplicates_found:
        print()
        print("WARNING:")
        print("    No duplicate passwords were detected in the first " +
            str(file_input.num_to_look_for_duplicates) + " parsed passwords")
        print()
        print("    This may be a problem since the training program needs to know frequency")
        print("    info such as '123456' being more common than '629811'")
        if get_confirmation("Do you want to exit and try again with a different training set (RECOMENDED)"):
            return False

    ## Perform second loop through training data
    #
    # This pass is responsible for the following:
    #
    # -Learning OMEN NGRAMs
    # -Training the PCFG grammar
    #
    print("-------------------------------------------------")
    print("Performing second pass on the training passwords")
    print("-------------------------------------------------")
    print("")

    # Re-Initialize the file input to read passwords from
    file_input = TrainerFileInput(
                    program_info['training_file'],
                    program_info['encoding'])

    # Reset progress_bar
    num_parsed_so_far = 0
    print("Printing out status after every million passwords parsed")
    print("------------")

    # Initialize OMEN lookup tables
    omen_trainer = AlphabetLookup(
        alphabet = program_info['alphabet'],
        ngram = program_info['ngram'],
        max_length = program_info['max_len']
        )

    # Initialize the PCFG Password parse
    pcfg_parser = PCFGPasswordParser(multiword_detector)

    ## Loop until we hit the end of the file
    try:
        password = file_input.read_password()
        while password:

            # Print status indicator if needed
            num_parsed_so_far += 1
            if num_parsed_so_far % 1000000 == 0:
                print(str(num_parsed_so_far//1000000) +' Million')

            # Parse OMEN info
            omen_trainer.parse(password)

            # Parse the pcfg info
            pcfg_parser.parse(password)

            # Get the next password
            password = file_input.read_password()

    except Exception as msg:
        traceback.print_exc(file=sys.stdout)
        print("Exception: " + str(msg))
        return False

    print()
    print("-------------------------------------------------")
    print("Calculating OMEN probabilities")
    print("-------------------------------------------------")
    print()

    # Calculate the OMEN level data
    omen_trainer.apply_smoothing()

    omen_keyspace = calc_omen_keyspace(omen_trainer)

    # Add in the probability of brute force to the base structures
    if program_info['coverage'] != 0:
        # Make sure there are valid OMEN parses, otherwise no sense creating
        # a brute force rule
        if omen_keyspace.most_common(1) != []:
            # Adding the Markov/Omen numbers in as addition to the currently parsed
            # passwords vs. resetting the counts/probabilities of what was already
            # parsed
            markov_instances = (num_valid_passwords /  program_info['coverage']) - num_valid_passwords
            pcfg_parser.count_base_structures['M'] = markov_instances

    ## Perform third loop through training data
    #
    # This pass is responsible for the following:
    #
    # -Calculating probability of OMEN levels
    #  In the previous stage we calulated the keyspace for each OMEN level
    #  so by now figuring out how many passwords in the training set fall
    #  under each level we can then assign a probability to the levels.
    #
    print("")
    print("-------------------------------------------------")
    print("Performing third pass on the training passwords")
    print("-------------------------------------------------")
    print("")

    # Re-Initialize the file input to read passwords from
    file_input = TrainerFileInput(
                    program_info['training_file'],
                    program_info['encoding'])

    # Reset progress_bar
    num_parsed_so_far = 0
    print("Printing out status after every million passwords parsed")
    print("------------")

    omen_levels_count = Counter()
    ## Loop until we hit the end of the file
    try:
        password = file_input.read_password()
        while password:

            # Print status indicator if needed
            num_parsed_so_far += 1
            if num_parsed_so_far % 1000000 == 0:
                print(str(num_parsed_so_far//1000000) +' Million')

            # Find OMEN level of password
            level = find_omen_level(omen_trainer,password)
            omen_levels_count[level] += 1

            # Get the next password
            password = file_input.read_password()

    except Exception as msg:
        traceback.print_exc(file=sys.stdout)
        print("Exception: " + str(msg))
        return False

    print()
    print("-------------------------------------------------")
    print("Saving Data")
    print("-------------------------------------------------")
    print()

    # Save the configuration file
    if not save_config_file(base_directory,program_info, file_input, pcfg_parser):
        print("Error, something went wrong saving the configuration file to disk")
        return False

    # Save the OMEN data
    if not save_omen_rules_to_disk(
        omen_trainer,
        omen_keyspace,
        omen_levels_count,
        num_valid_passwords,
        base_directory,
        program_info
        ):
        print("Error, something went wrong saving the OMEN data to disk")
        return False

    # Save the pcfg data to disk
    if not save_pcfg_data(
                base_directory,
                pcfg_parser,
                program_info['encoding'],
                program_info['save_sensitive'],
            ):
        print("Error, something went wrong saving the pcfg data to disk")
        return False

    # Print statisticts to the screen
    print_statistics(pcfg_parser)

    # Everything appears to have completed successfully
    return True
