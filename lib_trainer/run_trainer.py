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
    Runs through the input and performs three passes on the training
    set to genetate the resulting grammar

    This function is also responsible for saving the grammar to disk

    Inputs:
        program_info: A dictionary containing all of the command line
        option results

        base_directory: The base directory to save the resulting grammar to

    Returns:
        True: If the operations completed sucessfully

        False: If any errors occured
    """

    # Perform the first pass of the training list

    # Initialize the file input to read passwords from
    file_input = TrainerFileInput(
                    program_info['training_file'],
                    program_info['encoding'])
                    
    # Used for progress_bar
    num_parsed_so_far = 0

    print("-------------------------------------------------")
    print("Performing the first pass on the training passwords")
    print("What we are learning:")
    print("A) Identify words for use in multiword detection")
    print("B) Identify alphabet for Markov chains")
    print("C) Duplicate password detection, (duplicates are good!)")
    print("-------------------------------------------------")
    print("")
    print("Printing out status after every million passwords parsed")
    print("------------")
                    
    # Initialize the alphabet generator to learn the alphabet
    ag = AlphabetGenerator(program_info['alphabet_size'], program_info['ngram'])
    
    # Intitialize the multi-word detector
    multiword_detector = MultiWordDetector(
                            threshold = 5,
                            min_len = 4,
                            max_len = 21)

    # Loop until we hit the end of the file
    try:
        password = file_input.read_password()
        while password:

            # Print status indicator if needed
            num_parsed_so_far += 1
            if num_parsed_so_far % 1000000 == 0:
                print(str(num_parsed_so_far//1000000) +' Million')

            # Save statistics for the alphabet
            ag.process_password(password)
            
            # Train multiword detector
            multiword_detector.train(password)

            # Get the next password
            password = file_input.read_password()

    except Exception as msg:
        print(f"Exception: {msg}")
        return False

    # Save the learned alphabet
    program_info['alphabet'] = ag.get_alphabet()

    # Record how many valid passwords there were
    num_valid_passwords = file_input.num_passwords

    if num_valid_passwords == 0:
        print()
        print("Error, no valid passwords were found when attempting to train ruleset.")
        return False

    # Print some basic statistics after first loop
    print()
    print(f"Number of Valid Passwords: {num_valid_passwords}")
    print(f"Number of Encoding Errors Found in Training Set: {file_input.num_encoding_errors}")
    print()

    # Perform duplicate detection and warn user if no duplicates were found
    if not file_input.duplicates_found:
        print()
        print("WARNING:")
        print(f"   No duplicate passwords were detected in the first {file_input.num_to_look_for_duplicates} parsed passwords")
        print()
        print("    This may be a problem since the training program needs to know frequency")
        print("    info such as '123456' being more common than '629811'")
        print()

    # Perform second loop through training data

    # Re-Initialize the file input to read passwords from
    file_input = TrainerFileInput(
                    program_info['training_file'], 
                    program_info['encoding'])
                    
    # Reset progress_bar
    num_parsed_so_far = 0

    print("-------------------------------------------------")    
    print("Performing the second pass on the training passwords")
    print("What we are learning:")
    print("A) Learning Markov (OMEN) NGRAMS")
    print("B) Training the core PCFG grammar")
    print("-------------------------------------------------")
    print("")   
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
    
    # Loop until we hit the end of the file
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
        print("Exiting...")
        return
        
    print()    
    print("-------------------------------------------------")  
    print("Calculating Markov (OMEN) probabilities and keyspace")
    print("This may take a few minutes")
    print("-------------------------------------------------")
    print()
    
    # Calculate the OMEN probabilities (done when smoothing), 
    # and then the keyspace for each level
    omen_trainer.apply_smoothing()
    omen_keyspace = calc_omen_keyspace(omen_trainer)
           
    # Perform third loop through training data
    # Re-Initialize the file input to read passwords from
    file_input = TrainerFileInput(
                    program_info['training_file'], 
                    program_info['encoding'])
                    
    # Reset progress_bar
    num_parsed_so_far = 0
    
    print("")    
    
    print("-------------------------------------------------")    
    print("Performing third pass on the training passwords")
    print("What we are learning:")
    print("A) What Markov (OMEN) probabilities the training passwords would be created at")
    print("-------------------------------------------------")
    print("")

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
        print("Exiting...")
        return    

    # Print statisticts to the screen
    print_statistics(pcfg_parser)

    # Insert OMEN/Markov into the base_structure grammar based on the coverage
    # Skip this step if coverage is 1 (aka specifically turning off OMEN)
    if program_info['coverage'] != 1:
    
        # Make sure there are valid OMEN parses, otherwise no sense creating
        # a brute force rule. Also for now, print out an error and exit. This
        # is annoying but hopefully it shouldn't happen and if it does that
        # would be really good to know. So I don't want it to fail and be ignored
        if not omen_keyspace.most_common(1):
            print("Error. The trainer was unable to create any Markov/OMEN NGrams for some reason")
            print("If you want to re-try this without using Markov/OMEN, rerun the trainer with")
            print("the argument '--coverage 1")
            print("Exiting without saving grammar")
            return False
        
        # If we only should generate guesses using OMEN/Markov delete all the other base structures
        if program_info['coverage'] == 0:
            pcfg_parser.count_base_structures.clear()
            pcfg_parser.count_base_structures['M'] = 1
            
        # Need to add a count to Markov base structure so that it happens at
        # the percentage that the coverage value suggests
        else:
            markov_instances = (num_valid_passwords / program_info['coverage']) - num_valid_passwords
            pcfg_parser.count_base_structures['M'] = markov_instances

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
    
    return True
