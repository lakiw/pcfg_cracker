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
#    base_directory: The directory to load the ruleset from
#
#    version: The version of the guess generator, used to tell if ruleset is
#             valid for this version
#
# Output:
#    grammar: A loaded PCFG Grammar, minus the (S)tart item and base structures
#
#             Mostly terminals, but some can be transforms like capitalizatoin
#             masks.
#
#             Takes the form of a dictionary with the variable name, and
#             a sub-dictionary of the form:
#                {
#                   'values':['11','51'],
#                   'prob':0.3
#                }
#
#    base_structures:    A list of (base structures, prob) tuples in 
#                        probability order
#
#             For example [('D2L2',0.3), ('D4L3',0.2) ...]
#
#    ruleset_info: A dictionary containing general information about the ruleset
#
def load_grammar(rule_name, base_directory, version, skip_brute):

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
        
    # Holds the base structures
    base_structures = []
    if not _load_base_structures(base_structures, base_directory, skip_brute):
        raise Exception
    
    return grammar, base_structures, ruleset_info
    

## Loads the OMEN keyspace information from file
#
# This is useful for status outputs to let users know how many guesses
# are generated for each OMEN level
#
# Will not catch exceptions. Passes file execeptions up to calling code
#
# Input:
#    base_directory: The base directory to load the rules from
#
# Returns:
#    omen_keyspace: A dictionary indexed by omen levels with the value being
#                   the keyspace. Initially empty
#                   Example:
#                   {'1':5000, '2':300012, '3':981138888}
#    
def load_omen_keyspace(base_directory):
    filename = os.path.join(base_directory,"Omen","omen_keyspace.txt")

    omen_keyspace = {}
    
    # Try to open the file
    with open(filename, 'r') as file:
        # Read though all the lines in the file
        for value in file:
        
            # Split up the tab seperated items and then save their values
            split_values = value.rstrip().split("\t") 
            
            level = int(split_values[0])
            keyspace = int(split_values[1])
            
            omen_keyspace[level] = keyspace
    
    return omen_keyspace    
                
                

## Loads the base structures for the grammar
#
# Input:
#
#    base_structures: A list to return the data in
#             Entries take the form of a dictionary with the following fields:
#                 'prob': The probability of the base structure
#                 'replacements': A list of the individual transitions.
#                      Aka: ['A2','D3', 'K5']
#
#    base_directory: The base directory to load the rules from
#
# Output:
#    True: Config was loaded and parsed correctly
#
#    False: Config failed to load 
#
def _load_base_structures(base_structures, base_directory, skip_brute):
    
    filename = os.path.join(base_directory,"grammar","grammar.txt")
    
    # Try to open the file
    try:
        with open(filename, 'r') as file:
        
            # If skip_brute is enabled, find out what probability is
            # assigned to brute force guesses if any
            
            # This is the maximum probability the grammar is compared against
            # Need to specify this because if we remove brute force structures
            # the total prob needs to be reduced so everything else can be
            # normalized against the new total prob.
            total_prob= 1.0
            
            if skip_brute:
                for value in file:
                    # Split up the tab seperated items and then save their values
                    split_values = value.rstrip().split("\t") 
                    
                    # Found the brute force section, record probabilty and break
                    # out of the loop
                    if split_values[0] == 'M':
                        total_prob = total_prob - float(split_values[1])
                        
                        # Reset the file pointer and exit
                        file.seek(0)
                        break
            
            # Read though all the lines in the file
            for value in file:
            
                # Split up the tab seperated items and then save their values
                split_values = value.rstrip().split("\t") 
                
                value = split_values[0]
                prob = float(split_values[1]) / total_prob
                
                new_base = {
                    'prob':prob,
                    'replacements':[]
                }
                
                ## Split up the replacements and save them
                #
                # Note, splitting on digits, and all transistions are only
                # one alpha character long
                for item in value:
                    if item.isalpha():
                        new_base['replacements'].append(item)
                    else:
                        new_base['replacements'][-1] += item
                
                # Save the base structure
                #
                # Note if we are skipping Markov attacks, don't save that 
                if not skip_brute or 'M' not in new_base['replacements']:
                    base_structures.append(new_base)             
            
    except IOError as error:
        print (error,file=sys.stderr)
        print ("Error opening file " + filename ,file=sys.stderr)
        return False
        
    except Exception as error:
        print (error,file=sys.stderr)
        return False
        
    ## Add in case mangling to all the alpha characters
    for base in base_structures:
        replacement = base['replacements']
        
        i=0
        while i < len(replacement):
            # It is an alpha string
            if replacement[i][0] == 'A':
                # Find the length of the alpha string, (though it is a string)
                len_str = replacement[i][1:]
                # Insert the case mangling
                replacement.insert(i+1,'C' + len_str)
        
            i += 1
            

    return True
    

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
        
    # Load the capitalziaton masks
    if not _load_from_multiple_files(grammar, config['CAPITALIZATION'], base_directory, encoding):
        print("Error loading capitalization masks")
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

    # Load OMEN level probabilities
    full_path = os.path.join(base_directory, "Omen", "pcfg_omen_prob.txt")
    grammar['M'] = []     
    if not _load_from_file(grammar['M'], full_path, encoding):
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
        
        # Get the UUID to aid in saving/restarting cracking sessions
        ruleset_info['uuid'] = config.get('TRAINING_DATASET_DETAILS','uuid')
        
    except IOError as msg:
        print("Could not open the config file for the ruleset specified. The rule directory may not exist",file=sys.stderr)
        print("Ruleset: " + str(base_directory))
        return False
    except configparser.Error as msg:
        print("Error occured parsing the configuration file: " + str(msg),file=sys.stderr)
        return False  
        
    return True
    
    
## Loads grammar information from multiple files for length specified terminals
#
# Return Values:
#
#     True: If everything was loaded ok
#
#     False: If an error occured loading the ruleset
#
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
    
    
## Loads grammar information from a file
#
# Return Values:
#
#     True: If everything was loaded ok
#
#     False: If an error occured loading the ruleset
#
def _load_from_file(grammar_section, filename, encoding):
    
    # Try to open the file
    try:
        with codecs.open(filename, 'r', encoding= encoding, errors= 'surrogateescape') as file:
            
            # Used to group different items of the same probability together
            prev_prob = -1.0
            
            # Read though all the lines in the file
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
                
                value = split_values[0]
                prob = float(split_values[1])
                
                # If another item had the same probabilty value
                if prob == prev_prob:
                    grammar_section[-1]['values'].append(value)
                  
                # If this is the first item with this probability    
                else:
                    prev_prob = prob
                    
                    item = {
                        'values': [value],
                        'prob': prob
                    }
                    
                    grammar_section.append(item)
                                  
    except IOError as error:
        print (error,file=sys.stderr)
        print ("Error opening file " + filename ,file=sys.stderr)
        return False
        
    except Exception as error:
        print (error,file=sys.stderr)
        return False

    return True   