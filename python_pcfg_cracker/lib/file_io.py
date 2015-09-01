#!/usr/local/bin/python3

########################################################################################
#
# Name: PCFG_Cracker File IO code
# Description: Holds most of the file IO code used when loading
#              dictionaries, rules, and config files
#
#########################################################################################

from __future__ import print_function
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
def loadConfig(g_vars,c_vars):
    return g_vars.RETValues['STATUS_OK']
    



def loadBaseStructures(g_vars,c_vars,pcfg):
    baseDir = os.path.join(sys.path[0],c_vars.ruleDirectory, c_vars.ruleName, "Grammar")
    try:
        inputFile = open(os.path.join(baseDir,"Grammar.txt"),'r')
    except:
        print ("Could not open config file: " + "Grammar.txt")
        print( os.path.join(baseDir,"Grammar.txt"))
        return g_vars.RETValues['File_IO_Error']
    
    for line in inputFile:
        print (line)
        
    return g_vars.RETValues['STATUS_OK']
        
##############################################################
# Top level function to read the rules for the grammar
##############################################################
def loadRules(g_vars,c_vars,pcfg):
    ##--Read the top level rules config file --#
    config = configparser.ConfigParser()
    baseDir = os.path.join(sys.path[0],c_vars.ruleDirectory, c_vars.ruleName)
    parseConfig(g_vars,c_vars,baseDir,config)
    ##--Right now just cheating and reading in a fully filled out sample grammar
    pcfg.grammar = s_grammar
    
    ##--Quick and dirty rule input until I have the time to do it right--##
    retValue = loadBaseStructures(g_vars,c_vars,pcfg)
    if retValue != g_vars.RETValues['STATUS_OK']:
        return retValue
    #processInput(g_vars,c_vars,pcfg,input)
    return g_vars.RETValues['STATUS_OK']
    
    
##############################################################
# Parses a config file
##############################################################
def parseConfig(g_vars,c_vars,baseDir,config):
    ##--still working on this...
    filename = os.path.join(baseDir, "grammar.cfg")
    dataset = config.read(filename)
    if (len(dataset)==0):
        print ("Could not open config file: " + filename)
        return g_vars.RETValues['File_IO_Error']
    print (config.sections())
    return g_vars.RETValues['STATUS_OK']