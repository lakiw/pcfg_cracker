#!/usr/bin/env python3


#############################################################################
# Responsible for loading up a PCFG grammar from disk
#
#############################################################################


# Global imports
import sys
import os
import configparser
import json
import codecs


## Main function to load up a grammar from disk
#
# Note, will pass exceptions and errors back up to the calling program
#
# Input:
#    rule_name: the name of the ruleset to load
#
# Output:
#    grammar: A loaded PCFG Grammar, minus the (S)tart item and base structures
#
#             Mostly terminals, but some can be transforms like capitalizatoin
#             masks.
#
#             Takes the form of a dictionary with the variable name, and
#             a list of (value, prob) tuples in probability order.
#
#             For example {'D2':[('11',0.3),('12',0.2),....]}
#
#    base:    A list of (base structures, prob) tuples in probability order
#
#             For example [('D2L2',0.3), ('D4L3',0.2) ...]
#
#    ruleset_info: A dictionary containing general information about the ruleset
#
def load_grammar(rule_name, base_directory, version):

    # Holds general information about the grammar
    ruleset_info = {
        'rule_name':rule_name,
        'version': version
    }
  
    config = configparser.ConfigParser()
    if not _load_config(ruleset_info, base_directory, config):
        raise Exception
        
    # Holds all of the grammar with the exception of the base structures and
    # OMEN probabilities    
    grammar = {}
    
    if not _load_terminals(ruleset_info, grammar, base_directory, config):
        raise Exception
    
    return None, None, ruleset_info


## Loads most of the terminals for the grammar
#
# This includes things like alpha strings, digits, keyboard patterns, etc
#
# Input:
#    ruleset_info: A dictionary containing some general information about the
#                  ruleset
#
#    grammar: A dictionary to return the data in
#             Takes the form of a dictionary with the variable name, and
#             a list of (value, prob) tuples in probability order.
#
#             For example {'D2':[('11',0.3),('12',0.2),....]} 
#
#    base_directory: The base directory to load the rules from
#
#    config: A Python ConfigParser object containing the master config for the
#            rules
#
# Output:
#    True: Config was loaded and parsed correctly
#
#    False: Config failed to load 
#
def _load_terminals(ruleset_info, grammar, base_directory, config):

    # Quick way to reference variables
    encoding = ruleset_info['encoding']
    
    # Load the alpha terminals
    if not _load_from_multiple_files(grammar, config['BASE_A'], base_directory, encoding):
        print("Error loading alpha terminals")
        return False
        
    # Load the digit terminals
    if not _load_from_multiple_files(grammar, config['BASE_D'], base_directory, encoding):
        print("Error loading digit terminals")
        return False
        
    # Load the 'other' terminals
    if not _load_from_multiple_files(grammar, config['BASE_O'], base_directory, encoding):
        print("Error loading other/special terminals")
        return False
        
    # Load the keyboard terminals
    if not _load_from_multiple_files(grammar, config['BASE_K'], base_directory, encoding):
        print("Error loading keyboard terminals")
        return False
    
    # Load the years
    if not _load_from_multiple_files(grammar, config['BASE_Y'], base_directory, encoding):
        print("Error loading year terminals")
        return False
    
    # Load Context Sensitive replacements
    if not _load_from_multiple_files(grammar, config['BASE_X'], base_directory, encoding):
        print("Error loading context sensitive terminals")
        return False       
        
        
    return True


## Loads the main config from a ruleset
#
# Input:
#    base_directory: the directory to load the config from
#
#    ruleset_info: A dictionary to save results in. Also will have the 'version'
#                  of the pcfg guesser, to do a quick version check
#
#    config: A Python configpaser object. Passing it in so other functions
#            can make use of this config as well
#
# Output:
#    True: Config was loaded and parsed correctly
#
#    False: Config failed to load
#
def _load_config(ruleset_info, base_directory, config):

    # Attempt to read the config from disk
    try:
        config.readfp(open(os.path.join(base_directory,"config.ini")))
        
        ## Check the version
        #
        ruleset_info['rule_version'] = config.get('TRAINING_PROGRAM_DETAILS','version')
        
        # Only checking to make sure the Major version is higher, as I haven'tart
        # made any changes yet that will invalidate using a ruleset from a minor
        # release        
        major_guesser = ruleset_info['version'].split('.')[0]
        major_rule = ruleset_info['rule_version'].split('.')[0]
        
        if major_guesser > major_rule:
            print("The ruleset you are attempting to run is not compatible with this version of the pfcg_guesser",file=sys.stderr)
            print("PCFG_Guesser Version: " + str(ruleset_info['version']),file=sys.stderr)
            print("Ruleset Version: " + str(ruleset_info['rule_version']),file=sys.stderr)
            return False
        
        # Find the encoding for the config file
        ruleset_info['encoding'] = config.get('TRAINING_DATASET_DETAILS','encoding')
        
    except IOError as msg:
        print("Could not open the config file for the ruleset specified. The rule directory may not exist",file=sys.stderr)
        print("Ruleset: " + str(base_directory))
        return False
    except configparser.Error as msg:
        print("Error occured parsing the configuration file: " + str(msg),file=sys.stderr)
        return False  
        
    return True
    
    
##############################################################
# Loads grammar information from multiple files for length specified terminals
#
# Return Values:
#
#     True: If everything was loaded ok
#
#     False: If an error occured loading the ruleset
#
##############################################################
def _load_from_multiple_files(grammar, config, base_directory, encoding):
    
    directory = config.get('directory')
    
    filenames = json.loads(config.get('filenames'))
    
    for file in filenames:
        full_path = os.path.join(base_directory, directory, file)
        
        length = int(file.split('.')[0])
        
        # Initialize the structure to hold the data
        name = config.get('name') + file.split('.')[0]
        grammar[name] = []
        
        if not _load_from_file(grammar[name], full_path, encoding):
            return False

    return True
    
    
##############################################################
# Loads grammar information from a file
#
# Return Values:
#
#     True: If everything was loaded ok
#
#     False: If an error occured loading the ruleset
#
##############################################################
def _load_from_file(grammar_section, filename, encoding):

    # Try to open the file
    try:
        with codecs.open(filename, 'r', encoding= encoding, errors= 'surrogateescape') as file:
            
            # Read though all the lines in the fil
            for value in file:

                # There "shouldn't" be encoding errors in the rules files, but
                # might as well check to be on the safe side
                try:
                    value.encode(encoding)
                    
                except UnicodeEncodeError as e:
                    if e.reason == 'surrogates not allowed':
                        num_encoding_errors = num_encoding_errors + 1
                    else:
                        print("Hmm, there was a weird problem reading in a line from the rules file",file=sys.stderr)
                        print('',file=sys.stderr)
                    continue
     
                # Split up the tab seperated items and then save their values
                split_values = value.rstrip().split("\t") 
                grammar_section.append([split_values[0],float(split_values[1])])
                                  
    except IOError as error:
        print (error,file=sys.stderr)
        print ("Error opening file " + filename ,file=sys.stderr)
        return False
        
    except Exception as error:
        print (error,file=sys.stderr)
        return False

    return True   