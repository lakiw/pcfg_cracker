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

#Used for debugging and development
from sample_grammar import s_grammar
from pcfg_manager.ret_types import RetType


#########################################################################################
# Extracts the probabilities from tab seperated input values
#########################################################################################
def extract_probability(master_list = []):
    for position in range(0,len(master_list)):
        master_list[position] = master_list[position].split('\t')
        
        ##--If there wasn't probability info encoded, then error out
        if len(master_list[position]) != 2:
            print("Error parsing the probabilities from the training file",file=sys.stderr)
            return RetType.CONFIG_ERROR

    return RetType.STATUS_OK

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
        return RetType.FILE_IO_ERROR
    
    return RetType.STATUS_OK

########################################################################################################################
# Inserts a termininal replacement into the grammar
########################################################################################################################
def insert_terminal(config, grammar, rule_directory, encoding, section_type):
    try:
        #--This is a terminal transition so there are no more replacemetns to processInput
        file_type = config.get(section_type,'file_type')
        function = config.get(section_type,'function')
        ##--We need to go through all the files--##
        filenames = json.loads(config.get(section_type,'filenames'))
        cur_directory = os.path.join(rule_directory, config.get(section_type,'directory'))
    
    except configparser.Error as msg:
        print("Error occured parsing the configuration file: " + str(msg),file=sys.stderr)
        return RetType.CONFIG_ERROR
        
    for cur_file in filenames:
        full_file_path = os.path.join(cur_directory,cur_file)
                
        ##--Read in the file--##
        value_list = []
        ret_value = read_input_values(full_file_path, value_list, encoding)
        if ret_value != RetType.STATUS_OK:
            return ret_value
                    
        ##--Parse the results and extract the probabilities--##
        ret_value = extract_probability(value_list)
        if ret_value != RetType.STATUS_OK:
            return ret_value
                
                
        ##--Now insert the terminals into the grammar
        cur_section = {'name':cur_file.strip('.txt'), 'type':section_type, 'replacements':[]}
                
        ##--Need to add the replacemetns
        cur_replacement = {'function':function,'is_terminal':True, 'prob':value_list[0][1], 'terminal':[value_list[0][0]]}
        last_prob = value_list[0][1]
        for index in range(1,len(value_list)):
            ##--Now to check if the current prob is the same or different, (aka if we can add to the previous replacement or have to create another one
            if value_list[index][1] == last_prob:
                cur_replacement['terminal'].append(value_list[index][0])
                    ##--Need to create a new replacement
            elif value_list[index][1] < last_prob:
                ##--Add previous replacement to the full list
                cur_section['replacements'].append(cur_replacement)
                ##--Update new node
                last_prob = value_list[index][1]
                cur_replacement = {'function':function,'is_terminal':True, 'prob':value_list[index][1], 'terminal':[value_list[index][0]]}
            ##--Should be an error condition if the list isn't in decending probability order
            else:
                print("ERROR: The training file should be in decending probability order: " + str(section_type),file=sys.stderr)
                return RetType.CONFIG_ERROR
        ##--Update the last replacement
        cur_section['replacements'].append(cur_replacement)
        grammar.append(cur_section)
            
    return RetType.STATUS_OK
    
    
########################################################################
# Recursivly builds a grammar from a config file and a loaded ruleset
########################################################################
def build_grammar(config, grammar, rule_directory, encoding, section_type):
    
    ##--Check to make sure the section we are trying to add isn't in the grammar already--##
    ##--This helps avoid loops in grammars that have recursion built into them--##
    for x in grammar:
        if x['type'] == section_type:
            print('Recursion found in grammar for section ' + str(section_type),file=sys.stderr)
            return RetType.STATUS_OK
            
    ##--What we'll eventually push into the pcfg
    working_section = {'type':section_type,'replacements':[]}
    
    try:
        ##--Grab the function type for this section from the config file--##
        ##--Note, yes the grammar is set up for individual replacements to have their own function
        ##--but the training program is set up for one overarching function for each section. 
        ##--What I'm trying to say is in the future this may need to be changed if you want multiple functions for different replacements
        ##--Aka if you have S-> D1, D2, D3 then those repalcement functions are all the same
        ##--If you want to have S-> D1, A3 then those replacement functions would be different for each section
        function = config.get(section_type,'function')
    
        #############################################################################
        ##--How the rest of the section is parsed will depend on the function chosen
        ###############################################################################
        
        ##--If the function doesn't add anything itself but calls other replacements. Example would be base structures like A4D2 -> Test12
        if function == 'Transparent':
            ##--Add the stub of the grammar to the pcfg to avoid loops in the future--##
            grammar.append(working_section)
            replacements = json.loads(config.get(section_type,'replacements'))
            ##--Now add the replacements to the grammar before we attempt to add the links to them for this section
            for cur_replacement in replacements:
                ret_value = build_grammar(config, grammar, rule_directory, encoding, cur_replacement['Config_id'])
                if ret_value != RetType.STATUS_OK:
                    return ret_value
      
        ##--If the function loads a dictionary that is passed to additional mangling steps in later transitions            
        elif function == 'Shadow':
            ##--Add the stub of the grammar to the pcfg to avoid loops in the future--##
            grammar.append(working_section)
            replacements = json.loads(config.get(section_type,'replacements'))
            ##--Now add the replacements to the grammar before we attempt to add the links to them for this section
            for cur_replacement in replacements:
                ret_value = build_grammar(config, grammar, rule_directory, encoding, cur_replacement['Config_id'])
                if ret_value != RetType.STATUS_OK:
                    return ret_value
                    
        ##--If the function capitalizes the previous pre-terminal
        elif function == 'Capitalization':
            insert_terminal(config, grammar, rule_directory, encoding, section_type)
            
        ##--This function is a direct copy terminal. For example D2-> 99, 82, 21. There is no special processing of the previous data.
        elif function == 'Copy':
            insert_terminal(config, grammar, rule_directory, encoding, section_type)
            
        ##-- This version of the pcfg_manager doesn't support the version of the function from the training file--##
        else:
            print("Unsupported function type for the grammar: " + str(function),file=sys.stderr)
            return RetType.CONFIG_ERROR
    except configparser.Error as msg:
        print("Error occured parsing the configuration file: " + str(msg),file=sys.stderr)
        return RetType.CONFIG_ERROR
    return RetType.STATUS_OK

    
    
##############################################################
# Loads the grammar from a ruleset
##############################################################
def load_grammar(rule_directory, grammar):
    
    ##--First start by setting up, reading, and parsing the config file for the ruleset--
    config = configparser.ConfigParser()
    
    ##--Attempt to read the config from disk
    try:
        config.readfp(open(os.path.join(rule_directory,"config.ini")))
        ##--Find the encoding for the config file--##
        encoding = config.get('TRAINING_DATASET_DETAILS','encoding')
        
    except IOError as msg:
        print("Could not open the config file for the ruleset specified. The rule directory may not exist",file=sys.stderr)
        return RetType.FILE_IO_ERROR
    except configparser.Error as msg:
        print("Error occured parsing the configuration file: " + str(msg),file=sys.stderr)
        return RetType.GENERIC_ERROR      
    
    ##--Now build the grammar starting with the start transition--##
    ret_value = build_grammar(config,grammar, rule_directory, encoding, "START")
    print(grammar)
    if ret_value != RetType.STATUS_OK:
        return ret_value
    return RetType.STATUS_OK
    


#####################################################################################################
# This code is hackish as hell. I just want to get something working as a proof of concept so I can
# see the performance of this tool with a non-trivial grammar
#####################################################################################################
def load_base_structures(c_vars,pcfg):
    base_dir = os.path.join(sys.path[0],c_vars.rule_directory, c_vars.rule_name, "Grammar")
    try:
        input_file = open(os.path.join(base_dir,"Grammar.txt"),'r')
    except:
        print ("Could not open config file: " + "Grammar.txt")
        print( os.path.join(base_dir,"Grammar.txt"))
        return RetType.FILE_IO_ERROR
    
    cheat_sheet = []
    ##--parse line and insert it into the pcfg
    for full_line in input_file:
        ##--Dont' want to mess with keyboard combos yet
        if 'K' not in full_line:
            ###-break apart the line----###
            cur_grammar = full_line.split('\t')
            line = cur_grammar[0]
            probability = float(cur_grammar[1])
        
            ##--Change stuctures like LLLLDD to [[L,4],[D,2]]
            structure = []
            last_char = line[0]
            runLen =1 
            for c_pos in range(1,len(line)):
                if line[c_pos]==last_char:
                    runLen = runLen + 1
                else:
                    structure.append([last_char,runLen])
                    last_char = line[c_pos]
                    runLen = 1
            ##--Now take care of the last character
            structure.append([last_char,runLen])
        
            ##---Now insert into the grammar
            pcfg.grammar[0]['replacements'].append({'is_terminal':False,'pos':[],'prob':probability,'function':'Transparent'})
            ##---Update the 'pos' links for the base structure
            ##---valuePos references the position in the grammar, cheetsheet has one lesss item since it doesn't have 'S'
            for value in structure:
                if value not in cheat_sheet:
                    cheat_sheet.append(value)
                    valuePos = len(cheat_sheet)
                else:
                    valuePos = cheat_sheet.index(value) + 1
                pcfg.grammar[0]['replacements'][-1]['pos'].append(valuePos)
    input_file.close()
    ##--Read in the input dictionary-----
    input_dictionary = []
    try:
        input_file = open(os.path.join(sys.path[0],c_vars.input_dictionary),'r')
        for line in input_file:
            line_len = len(line.rstrip())
            while line_len >= len(input_dictionary):
                input_dictionary.append([])
            input_dictionary[line_len].append(line.rstrip().lower())
        input_file.close()
    except Exception as e:
        print ("Could not open dictionary file: " + c_vars.input_dictionary)
        print (e)
        return RetType.FILE_IO_ERROR

    ##---Now fill in the values for the terminal structures--------------##
    for index, value in enumerate(cheat_sheet):
        if value[0]=='L':
            if len(input_dictionary)<=value[1] or len(input_dictionary[value[1]])==0:
                probability = 1
                pcfg.grammar.append({'name':"L"+str(value[1]),'replacements':[{'is_terminal':True,'prob':probability,'terminal':[],'function':'Standard_Copy'}]})
            else:
                probability = 1 / len(input_dictionary[value[1]])
                pcfg.grammar.append({'name':"L"+str(value[1]),'replacements':[{'is_terminal':True,'prob':probability,'terminal':list(input_dictionary[value[1]]),'function':'Standard_Copy'}]})
        else:
            input_dir="Holder"
            if value[0] == 'D':
                input_dir = "Digits"
            else:
                input_dir = "Special"
            base_dir = os.path.join(sys.path[0],c_vars.rule_directory, c_vars.rule_name, input_dir)
            try:
                input_file = open(os.path.join(base_dir,str(value[1])+".txt"),'r')
                pcfg.grammar.append({'name':value[0]+str(value[1]),'replacements':[]})
                ##--Now add the new line
                prev_prob = -1
                for line in input_file:
                    cur_transform = line.split('\t')
                    curValue = cur_transform[0]
                    probability = float(cur_transform[1])
                    if probability == prev_prob:
                        pcfg.grammar[-1]['replacements'][-1]['terminal'].append(curValue)
                    else:
                        prev_prob=probability
                        pcfg.grammar[-1]['replacements'].append({'is_terminal':True,'function':'Standard_Copy','prob':probability,'terminal':[]})
                        pcfg.grammar[-1]['replacements'][-1]['terminal'].append(curValue)
                input_file.close()  
            except Exception as e:
                print ("Could not open grammar file: " + os.path.join(base_dir,str(value[1])+".txt"))
                print(e)
                return RetType.FILE_IO_ERROR
                 
    #print(str(pcfg.grammar).encode(sys.stdout.encoding, errors='replace') )        
    return RetType.STATUS_OK
        
