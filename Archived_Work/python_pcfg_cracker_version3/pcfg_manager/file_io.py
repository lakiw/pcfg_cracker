#!/usr/bin/env python3

########################################################################################
#
# Name: PCFG_Cracker File IO code
# Description: Holds most of the file IO code used when loading
#              dictionaries, rules, and config files
#
#########################################################################################

import sys
import os
import configparser
import json
import codecs
from itertools import groupby

#Used for debugging
from pcfg_manager.core_grammar import print_grammar


#########################################################################################
# Extracts the probabilities from tab seperated input values
#########################################################################################
def extract_probability(master_list = []):
    for position in range(0,len(master_list)):
        master_list[position] = master_list[position].split('\t')
        
        ##--If there wasn't probability info encoded, then error out
        if len(master_list[position]) != 2:
            print("---Parsed line, (after being split by tabs---")
            print(master_list[position]) 
            print("Error parsing the probabilities from the training file",file=sys.stderr)
            return False

        #convert probablity to a float
        master_list[position][1] = float(master_list[position][1])
    return True

#########################################################################################
# Reads in all of values from an individual training file
# Doesn't do any parsing of the data beyond checking the encoding
#########################################################################################
def read_input_values(training_file, master_list =[] , encoding = 'utf-8'):

    ##-- First try to open the file--##
    try:
        with codecs.open(training_file, 'r', encoding= encoding, errors= 'surrogateescape') as file:
            
            num_encoding_errors = 0  ##The number of encoding errors encountered when parsing the input file
            
            # Read though all the passwords
            for value in file:
                ##--Note, there is a large potential for encoding errors to slip in
                ##--   I don't want to silently ignore these errors, but instead warn the user they are
                ##--   occuring so they can look at what file encoding they are using again
                try:
                    value.encode(encoding)
                except UnicodeEncodeError as e:
                    if e.reason == 'surrogates not allowed':
                        num_encoding_errors = num_encoding_errors + 1
                    else:
                        print("Hmm, there was a weird problem reading in a line from the training file",file=sys.stderr)
                        print('',file=sys.stderr)
                    continue
     
                master_list.append(value.rstrip())

            if num_encoding_errors != 0:
                print('',file=sys.stderr)
                print("WARNING: One or more values in the training set did not decode properly",file=sys.stderr)
                print("         Number of encoding errors encountered: " + str(num_encoding_errors),file=sys.stderr)
                print("         Ignoring values that contained encoding errors so it does not skew the grammar",file=sys.stderr)

                    
    except IOError as error:
        print (error,file=sys.stderr)
        print ("Error opening file " + training_file,file=sys.stderr)
        return False
    
    return True

########################################################################################################################
# Parses base structures and updates the grammar section for them
########################################################################################################################
def parse_base_structure(unformated_base,grammar_mapping, pos = []):

    ##--Split up the unformated base by value + length--##
    working_list = [''.join(g) for _, g in groupby(unformated_base, str.isalpha)]

    ##--Handle loading Markov probabilities--##
    if unformated_base == 'M':
        try:
            pos.append(grammar_mapping['M']['markov_prob'])
            return True
        except KeyError as msg:
            print("Error occured parsing the links in the Markov base structure: " + str(msg),file=sys.stderr)
            return False
    
    ##--Do a quick sanity check to make sure there are proper pairing of value digits
    if len(working_list) % 2 != 0:
        print("Error parsing base structure: " + str(unformated_base))
        return False
    
    ##--Now calculate the replacement mapping
    for index in range(0,len(working_list)//2):
        value = working_list[index*2]
        size = working_list[index*2 + 1]
        #--look up the position
        try:
            pos.append(grammar_mapping[value][size])
        except KeyError as msg:
            print("Error occured parsing the links in the base structure: " + str(msg),file=sys.stderr)
            return False
            
    return True
    
########################################################################################################################
# Inserts a termininal replacement into the grammar
########################################################################################################################
def insert_terminal(config, grammar, rule_directory, encoding, section_type, grammar_mapping = []):
    try:
        #--This is a terminal transition so there are no more replacemetns to processInput
        file_type = config.get(section_type,'file_type')
        function = config.get(section_type,'function')
        is_terminal = config.getboolean(section_type,'is_terminal')
        
        ##--We need to go through all the files--##
        filenames = json.loads(config.get(section_type,'filenames'))
        cur_directory = os.path.join(rule_directory, config.get(section_type,'directory')) 
    
    except configparser.Error as msg:
        print("Error occured parsing the configuration file: " + str(msg),file=sys.stderr)
        return False
        
    for cur_file in filenames:
        full_file_path = os.path.join(cur_directory,cur_file)
                
        ##--Read in the file--##
        value_list = []
        ret_value = read_input_values(full_file_path, value_list, encoding)
        if ret_value != True:
            return ret_value
         
        ##--Parse the results and extract the probabilities--##
        ret_value = extract_probability(value_list)
        if ret_value != True:
            print("Filename where the issue occured:")
            print(full_file_path)
            return ret_value               
                
        ##--Now insert the terminals into the grammar
        cur_section = {'name':cur_file.strip('.txt'), 'type':section_type, 'replacements':[]}
                
        ##--Need to add the replacements
        ##--If it is a Capitalization, Copy, or Shadow replacement, (they are all read in basically the same way)
        if function == 'Capitalization' or function == 'Copy' or function == 'Shadow' or function == 'Markov':
            ##--multiple replacements can share the same structure, (to limit the amount of list pushing and popping, (this is a performance tweak)
            ##--therefore initialize the structure and then loop through the rest of the values seeing if they can be instereted in this replacement
            ##--or if they have a different probability so they need their own
            ##--Note, if items are sharing a cur_replacement and are NOT terminal, they must also share the same replacement value
            cur_replacement = {'function':function,'is_terminal':is_terminal, 'prob':value_list[0][1], 'values':[value_list[0][0]]}
            ##--if position info needs to be added to this structure
            if function == 'Shadow':
                try:
                    all_replacements = json.loads(config.get(section_type,'replacements')) 
                    replacement = all_replacements[0]['Transition_id']
                    cur_replacement['pos'] = [ grammar_mapping[replacement][cur_section['name']] ]
                except KeyError as msg:
                    print("Error occured parsing the links in the config file: " + str(msg),file=sys.stderr)
                    return False
                except configparser.Error as msg:
                    print("Error occured parsing the configuration file: " + str(msg),file=sys.stderr)
                    return False
            
            last_prob = value_list[0][1]
                
            ##--Now loop through all the remaining values
            for index in range(1,len(value_list)):
                
                ##--If the probability is the same as the previous one--##
                if value_list[index][1] == last_prob:
                    cur_replacement['values'].append(value_list[index][0])
                
                ##--Need to create a new replacement       
                elif value_list[index][1] < last_prob:
                    
                    ##--Add previous replacement to the full list    
                    cur_section['replacements'].append(cur_replacement)
                    
                    ##--Update new node
                    last_prob = value_list[index][1]
                    cur_replacement = {'function':function,'is_terminal':is_terminal, 'prob':value_list[index][1], 'values':[value_list[index][0]]}
                    
                    if function == 'Shadow':
                        cur_replacement['pos'] = [ grammar_mapping[replacement][cur_section['name']] ]
                        
                ##--Should be an error condition if the list isn't in decending probability order
                else:
                    print("ERROR: The training file should be in decending probability order: " + str(section_type),file=sys.stderr)
                    return False
                    
            ##--Update the last replacement
            cur_section['replacements'].append(cur_replacement)
            grammar.append(cur_section)
        
        ##--If it is a base structure, additional pre-processing needs to be done on the structures
        ##--Also the combining of multiple base structures of the same probability into the same node doesn't work so don't use that optimization
        elif function == 'Transparent':
            for index in range(0,len(value_list)):
                cur_replacement = {'function':function,'is_terminal':False, 'prob':value_list[index][1], 'values':[value_list[index][0]], 'pos':[]}
                ret_value = parse_base_structure(value_list[index][0],grammar_mapping,cur_replacement['pos'])
                if ret_value != True:
                    print("Error parsing base structures in grammar",file=sys.stderr)
                    return False
                cur_section['replacements'].append(cur_replacement)
            grammar.append(cur_section)
        ##--Something weird is happeing so error out
        else:
            print("Invalid function type for grammar: " + str(function))
            return False
            
    return True
    

###########################################################################################
# Maps the location of replacements in the grammar to the types of replacements
#
# grammar_mapping is the main datastructure to return
# Contains a dictonary of {id:{length:index}}
# --id is the parsing id for the transition. Aka A for Alpha
# --length is the length of the transition. Aka 4 for A4 PASS
# --index is the index where the transition data is in grammar
############################################################################################
def find_grammar_mapping(config, grammar, section_type, grammar_mapping={}):
    try:
        replacements = json.loads(config.get(section_type,'replacements'))
    except configparser.Error as msg:
        print("Error occured parsing the configuration file: " + str(msg),file=sys.stderr)
        return False   
    for cur_replace in replacements:
        grammar_mapping[cur_replace["Transition_id"]] = {}
        for index, item in enumerate(grammar):
            if cur_replace["Config_id"] == item["type"]:
                grammar_mapping[cur_replace["Transition_id"]][item['name']] =index
    return True

    
########################################################################
# Recursivly builds a grammar from a config file and a loaded ruleset
########################################################################
def build_grammar(config, grammar, rule_directory, encoding, section_type, found_list = []):
    
    ##--Check to make sure the section we are trying to add isn't in the grammar already--##
    ##--This helps avoid loops in grammars that have recursion built into them--##
    for x in found_list:
        if x == section_type:
            print('Recursion found in grammar for section ' + str(section_type),file=sys.stderr)
            return True
     
    ##--Add this section to the found_list to avoid loops in the future--##
    found_list.append(section_type)
    
    try:
        ##--Grab the function type for this section from the config file--##
        ##--Note, yes the grammar is set up for individual replacements to have their own function
        ##--but the training program is set up for one overarching function for each section. 
        ##--What I'm trying to say is in the future this may need to be changed if you want multiple functions for different replacements
        ##--Aka if you have S-> D1, D2, D3 then those repalcement functions are all the same
        ##--If you want to have S-> D1, A3 then those replacement functions would be different for each section
        function = config.get(section_type,'function')
        
        ##--Grab if it is a terminal replacement or not--##
        is_terminal = config.getboolean(section_type,'is_terminal')
          
        ##--If the section is not a terminal replacement but instead leads to other replacements
        if is_terminal == False:

            replacements = json.loads(config.get(section_type,'replacements'))
            ##--Now add the replacements to the grammar before we attempt to add the links to them for this section
            for cur_replacement in replacements:
                ret_value = build_grammar(config, grammar, rule_directory, encoding, cur_replacement['Config_id'])
                if ret_value != True:
                    return ret_value    
      
            ##--All replacements should be added by now so make the mapping to be used when reading in the data
            grammar_mapping = {}
            ret_value = find_grammar_mapping(config, grammar, section_type, grammar_mapping)
            if ret_value != True:
                return ret_value 
            ##--Now actually add this section to the grammar--##
            ret_value = insert_terminal(config, grammar, rule_directory, encoding, section_type, grammar_mapping)
            if ret_value != True:
                return ret_value            
            
        ##--If this section is a terminal replacement
        else:
            ret_value = insert_terminal(config, grammar, rule_directory, encoding, section_type)
            if ret_value != True:
                return ret_value

    except configparser.Error as msg:
        print("Error occured parsing the configuration file: " + str(msg),file=sys.stderr)
        return False
    return True

    
    
##############################################################
# Loads the grammar from a ruleset
##############################################################
def load_grammar(rule_directory, grammar, config_details = {}):
    print("Loading the rules file",file=sys.stderr)
    
    ##--First start by setting up, reading, and parsing the config file for the ruleset--
    config = configparser.ConfigParser()
    
    ##--Attempt to read the config from disk
    try:
        config.readfp(open(os.path.join(rule_directory,"config.ini")))
        ##--Find the encoding for the config file--##
        encoding = config.get('TRAINING_DATASET_DETAILS','encoding')
        config_details['version'] = config.get('TRAINING_PROGRAM_DETAILS','version')
        
    except IOError as msg:
        print("Could not open the config file for the ruleset specified. The rule directory may not exist",file=sys.stderr)
        print("Ruleset: " + str(rule_directory))
        return False
    except configparser.Error as msg:
        print("Error occured parsing the configuration file: " + str(msg),file=sys.stderr)
        return False     
    
    ##--Now build the grammar starting with the start transition--##
    ret_value = build_grammar(config,grammar, rule_directory, encoding, "START")

    if ret_value != True:
        return ret_value
        
    print("Rules loaded",file=sys.stderr)
    print("",file=sys.stderr)
    return True
    

