#!/usr/bin/env python3

"""
Contains OMEN specific file IO functions to save training data to disk
"""


import os
import configparser
import codecs
from collections import Counter

from ..trainer_file_output import make_sure_path_exists


def save_omen_rules_to_disk(omen_trainer, omen_keyspace, omen_levels_count, num_valid_passwords, base_directory, program_info):
    """
    Main function called to save all OMEN data to disk

    Returns:
        True: If everything worked ok
        False: If any problems occured

    """

    encoding = program_info['encoding']

    omen_directory = os.path.join(base_directory,"Omen")

    # Create the rule directory if it does not exist already
    try:
        make_sure_path_exists(omen_directory)

    # Print out where the error occured, but then re-raise it for the calling function
    # to inform the user that the rules will not be saved
    except Exception as msg:
        print (msg)
        print("Error creating the rules directory " + omen_directory)
        return False

    ## Save the IP ngrams to disk
    #
    # Open the file for writing
    full_path = os.path.join(omen_directory, "IP.level")
    try:
        with codecs.open(full_path, 'w', encoding=encoding) as file:
            # Loop through the top (ngram-1) list that has IP
            for key, data in omen_trainer.grammar.items():
                file.write(str(data['ip_level'])+ "\t" + key + "\n")

    # Print out where the error occured, but then re-raise it for the calling function
    # to inform the user that the rules will not be saved
    except:
        print("Error creating the rules file: " + full_path)
        return False

    ## Save the EP ngrams to disk
    #
    # Open the file for writing
    full_path = os.path.join(omen_directory, "EP.level")
    try:
        with codecs.open(full_path, 'w', encoding=encoding) as file:
            # Loop through the top (ngram-1) list that has EP
            for key, data in omen_trainer.grammar.items():
                file.write(str(data['ep_level'])+ "\t" + key + "\n")

    # Print out where the error occured, but then re-raise it for the calling function
    # to inform the user that the rules will not be saved
    except:
        print("Error creating the rules file: " + full_path)
        raise

    ## Save the CP ngrams to disk
    #
    # Open the file for writing
    full_path = os.path.join(omen_directory, "CP.level")
    try:
        with codecs.open(full_path, 'w', encoding=encoding) as file:
            # Loop through the top (ngram-1) list that has IP
            for key, data in omen_trainer.grammar.items():
                # Loop through all of the final letter transitions
                for last_letter, level in data['next_letter'].items():
                    file.write(str(level[0]) + "\t" + key + last_letter +  "\n")

    # Print out where the error occured, but then re-raise it for the calling function
    # to inform the user that the rules will not be saved
    except:
        print("Error creating the rules file: " + full_path)
        raise

    ## Save the Length info to disk
    #
    # Open the file for writing
    full_path = os.path.join(omen_directory, "LN.level")
    try:
        with open(full_path, 'w') as file:
            ##--Loop through the length list
            for length, count in enumerate(omen_trainer.ln_lookup):
                print("PW Length " +str(length + 1) + " : " + str(count[1]))
                file.write(str(count[0]) + "\n")

    # Print out where the error occured, but then re-raise it for the calling function
    # to inform the user that the rules will not be saved
    except:
        print("Error creating the rules file: " + full_path)
        raise

    ## Save the config file
    #
    if not _save_config(
        file_name= "config.txt",
        directory= omen_directory,
        program_info = program_info,
    ):
        return False

    ## Save the alphabet file
    #
    if not _save_alphabet(
        file_name= "alphabet.txt",
        directory= omen_directory,
        alphabet = program_info['alphabet'],
        encoding = encoding
    ):
        return False

    ## Save the Keyspace information to disk
    #
    # Don't actually need this to generate PCFG guesses, but it's interesting
    # data that may be useful for other tools
    #
    # Open the file for writing
    full_path = os.path.join(omen_directory, "omen_keyspace.txt")
    try:
        with codecs.open(full_path, 'w', encoding=encoding) as file:
            # Loop through the keyspace dataset
            for level in reversed(omen_keyspace.most_common()):
                file.write(str(level[0])+ "\t" + str(level[1]) + "\n")

    # Print out where the error occured, but then re-raise it for the calling function
    # to inform the user that the rules will not be saved
    except:
        print("Error creating the rules file: " + full_path)
        raise

    ## Save the number of passwords each limit would crack to disk
    #
    # Don't actually need this to generate PCFG guesses, but it's interesting
    # data that may be useful for other tools
    #
    # Open the file for writing
    full_path = os.path.join(omen_directory, "omen_pws_per_level.txt")
    try:
        with codecs.open(full_path, 'w', encoding=encoding) as file:
            # Loop through the keyspace dataset
            for level in omen_levels_count.most_common():
                file.write(str(level[0])+ "\t" + str(level[1]) + "\n")

    # Print out where the error occured, but then re-raise it for the calling function
    # to inform the user that the rules will not be saved
    except:
        print("Error creating the rules file: " + full_path)
        raise


    ## Calculate and save the probability to perform each level at
    #
    # For each level find the probability associated with it
    pcfg_omen_prob = Counter()

    # Start by going through all the levels we calculated the keyspace for
    #
    # Do not need to calculate probabilities when the keyspace is too large
    for item in omen_keyspace.items():
        level = item[0]
        keyspace = item[1]

        # sanity check so we don't try to divide by 0 accidently
        if keyspace == 0:
            continue

        num_instances = omen_levels_count[level]
        percentage_cracked = num_instances / num_valid_passwords

        pcfg_omen_prob[level] = percentage_cracked/keyspace

    # Save OMEN level probabilities to disk
    full_path = os.path.join(omen_directory, "pcfg_omen_prob.txt")
    try:
        with codecs.open(full_path, 'w', encoding=encoding) as file:
            # Loop through the keyspace dataset
            for level in pcfg_omen_prob.most_common():
                file.write(str(level[0])+ "\t" + str(level[1]) + "\n")

    # Print out where the error occured, but then re-raise it for the calling function
    # to inform the user that the rules will not be saved
    except:
        print("Error creating the rules file: " + full_path)
        raise

    return True


def _save_config(file_name, directory, program_info):
    """

    Saves the main config file for this ruleset to disk

    """

    config = configparser.ConfigParser()

    ## Set up the config to contain all the data saved in config_info
    #
    # Establish the top level section
    #
    config.add_section("training_settings")

    # Add the individual keys for that section
    config.set("training_settings", "ngram", str(program_info['ngram']))
    config.set("training_settings", "encoding", program_info['encoding'])

    ##--Save the config file--##
    try:
        full_path = os.path.join(directory, file_name)
        with open(full_path, 'w') as configfile:
            config.write(configfile)
    except IOError as msg:
        print("Error writing config file :" + str(msg))
        return False

    return True


def _save_alphabet(file_name, directory, alphabet, encoding):
    """
    Saves the alphabet file to disk

    One letter per line
    Doing this so it can support different character encodings and
    multi-character sets

    """

    try:
        full_path = os.path.join(directory, file_name)
        with codecs.open(full_path, 'w', encoding=encoding) as alphafile:
            for item in alphabet:
                alphafile.write(item+'\n')
    except IOError as error:
        print (error)
        print ("Error opening file " + str(full_path))
        return False

    return True
