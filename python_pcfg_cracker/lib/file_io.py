#!/usr/bin/env python3

########################################################################################
#
# Name: PCFG_Cracker File IO code
# Description: Holds most of the file IO code used when loading
#              dictionaries, rules, and config files
#
#########################################################################################

import sys
import string
import struct
import os
import configparser

#Used for debugging and development
from sample_grammar import s_grammar


##############################################################
# Loads the basic config file
# This contains a lot of information about the basic configuration
# that you may want to keep outside of the Rule files
##############################################################
def load_config(g_vars,c_vars):
    return g_vars.ret_values['STATUS_OK']
    


#####################################################################################################
# This code is hackish as hell. I just want to get something working as a proof of concept so I can
# see the performance of this tool with a non-trivial grammar
#####################################################################################################
def load_base_structures(g_vars,c_vars,pcfg):
    base_dir = os.path.join(sys.path[0],c_vars.rule_directory, c_vars.rule_name, "Grammar")
    try:
        input_file = open(os.path.join(base_dir,"Grammar.txt"),'r')
    except:
        print ("Could not open config file: " + "Grammar.txt")
        print( os.path.join(base_dir,"Grammar.txt"))
        return g_vars.ret_values['FILE_IO_ERROR']
    
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
            pcfg.grammar[0]['replacements'].append({'is_terminal':False,'pos':[],'prob':probability,'function':'transparent'})
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
        return g_vars.ret_values['FILE_IO_ERROR']

    ##---Now fill in the values for the terminal structures--------------##
    for index, value in enumerate(cheat_sheet):
        if value[0]=='L':
            if len(input_dictionary)<=value[1] or len(input_dictionary[value[1]])==0:
                probability = 1
                pcfg.grammar.append({'name':"L"+str(value[1]),'replacements':[{'is_terminal':True,'prob':probability,'terminal':[],'function':'copy'}]})
            else:
                probability = 1 / len(input_dictionary[value[1]])
                pcfg.grammar.append({'name':"L"+str(value[1]),'replacements':[{'is_terminal':True,'prob':probability,'terminal':list(input_dictionary[value[1]]),'function':'copy'}]})
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
                        pcfg.grammar[-1]['replacements'].append({'is_terminal':True,'function':'copy','prob':probability,'terminal':[]})
                        pcfg.grammar[-1]['replacements'][-1]['terminal'].append(curValue)
                input_file.close()  
            except Exception as e:
                print ("Could not open grammar file: " + os.path.join(base_dir,str(value[1])+".txt"))
                print(e)
                return g_vars.ret_values['FILE_IO_ERROR']
                 
    #print(str(pcfg.grammar).encode(sys.stdout.encoding, errors='replace') )        
    return g_vars.ret_values['STATUS_OK']
        
##############################################################
# Top level function to read the rules for the grammar
##############################################################
def load_rules(g_vars,c_vars,pcfg):
    ##--Read the top level rules config file --#
    config = configparser.ConfigParser()
    base_dir = os.path.join(sys.path[0],c_vars.rule_directory, c_vars.rule_name)
    parse_config(g_vars,c_vars,base_dir,config)
    
    ##---initialize 'S' for the grammar-----#
    pcfg.grammar.append({'name':'S','replacements':[]})
    
    ##--Quick and dirty rule input until I have the time to do it right--##
    ret_value = load_base_structures(g_vars,c_vars,pcfg)
    if ret_value != g_vars.ret_values['STATUS_OK']:
        return ret_value
    #processInput(g_vars,c_vars,pcfg,input)
    return g_vars.ret_values['STATUS_OK']
    
    
##############################################################
# Parses a config file
##############################################################
def parse_config(g_vars,c_vars,base_dir,config):
    ##--still working on this...
    filename = os.path.join(base_dir, "grammar.cfg")
    dataset = config.read(filename)
    if (len(dataset)==0):
        print ("Could not open config file: " + filename)
        return g_vars.ret_values['FILE_IO_ERROR']
    print (config.sections())
    return g_vars.ret_values['STATUS_OK']