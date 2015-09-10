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
    


#####################################################################################################
# This code is hackish as hell. I just want to get something working as a proof of concept so I can
# see the performance of this tool with a non-trivial grammar
#####################################################################################################
def loadBaseStructures(g_vars,c_vars,pcfg):
    baseDir = os.path.join(sys.path[0],c_vars.ruleDirectory, c_vars.ruleName, "Grammar")
    try:
        inputFile = open(os.path.join(baseDir,"Grammar.txt"),'r')
    except:
        print ("Could not open config file: " + "Grammar.txt")
        print( os.path.join(baseDir,"Grammar.txt"))
        return g_vars.RETValues['File_IO_Error']
    
    cheatSheet = []
    ##--parse line and insert it into the pcfg
    for fullLine in inputFile:
        ##--Dont' want to mess with keyboard combos yet
        if 'K' not in fullLine:
            ###-break apart the line----###
            curGrammar = fullLine.split('\t')
            line = curGrammar[0]
            probability = float(curGrammar[1])
        
            ##--Change stuctures like LLLLDD to [[L,4],[D,2]]
            structure = []
            lastChar = line[0]
            runLen =1 
            for cPos in range(1,len(line)):
                if line[cPos]==lastChar:
                    runLen = runLen + 1
                else:
                    structure.append([lastChar,runLen])
                    lastChar = line[cPos]
                    runLen = 1
            ##--Now take care of the last character
            structure.append([lastChar,runLen])
        
            ##---Now insert into the grammar
            pcfg.grammar[0]['replacements'].append({'isTerminal':False,'pos':[],'prob':probability,'function':'transparent'})
            ##---Update the 'pos' links for the base structure
            ##---valuePos references the position in the grammar, cheetsheet has one lesss item since it doesn't have 'S'
            for value in structure:
                if value not in cheatSheet:
                    cheatSheet.append(value)
                    valuePos = len(cheatSheet)
                else:
                    valuePos = cheatSheet.index(value) + 1
                pcfg.grammar[0]['replacements'][-1]['pos'].append(valuePos)
    inputFile.close()
    ##--Read in the input dictionary-----
    inputDictionary = []
    try:
        inputFile = open(os.path.join(sys.path[0],c_vars.inputDictionary),'r')
        for line in inputFile:
            lineLen = len(line.rstrip())
            while lineLen >= len(inputDictionary):
                inputDictionary.append([])
            inputDictionary[lineLen].append(line.rstrip().lower())
        inputFile.close()
    except Exception as e:
        print ("Could not open dictionary file: " + c_vars.inputDictionary)
        print (e)
        return g_vars.RETValues['File_IO_Error']

    ##---Now fill in the values for the terminal structures--------------##
    for index, value in enumerate(cheatSheet):
        if value[0]=='L':
            if len(inputDictionary)<=value[1] or len(inputDictionary[value[1]])==0:
                probability = 1
                pcfg.grammar.append({'name':"L"+str(value[1]),'replacements':[{'isTerminal':True,'prob':probability,'terminal':[],'function':'copy'}]})
            else:
                probability = 1 / len(inputDictionary[value[1]])
                pcfg.grammar.append({'name':"L"+str(value[1]),'replacements':[{'isTerminal':True,'prob':probability,'terminal':list(inputDictionary[value[1]]),'function':'copy'}]})
        else:
            inputDir="Holder"
            if value[0] == 'D':
                inputDir = "Digits"
            else:
                inputDir = "Special"
            baseDir = os.path.join(sys.path[0],c_vars.ruleDirectory, c_vars.ruleName, inputDir)
            try:
                inputFile = open(os.path.join(baseDir,str(value[1])+".txt"),'r')
                pcfg.grammar.append({'name':value[0]+str(value[1]),'replacements':[]})
                ##--Now add the new line
                prevProb = -1
                for line in inputFile:
                    curTransform = line.split('\t')
                    curValue = curTransform[0]
                    probability = float(curTransform[1])
                    if probability == prevProb:
                        pcfg.grammar[-1]['replacements'][-1]['terminal'].append(curValue)
                    else:
                        prevProb=probability
                        pcfg.grammar[-1]['replacements'].append({'isTerminal':True,'function':'copy','prob':probability,'terminal':[]})
                        pcfg.grammar[-1]['replacements'][-1]['terminal'].append(curValue)
                inputFile.close()  
            except Exception as e:
                print ("Could not open grammar file: " + os.path.join(baseDir,str(value[1])+".txt"))
                print(e)
                return g_vars.RETValues['File_IO_Error']
                 
    #print(str(pcfg.grammar).encode(sys.stdout.encoding, errors='replace') )        
    return g_vars.RETValues['STATUS_OK']
        
##############################################################
# Top level function to read the rules for the grammar
##############################################################
def loadRules(g_vars,c_vars,pcfg):
    ##--Read the top level rules config file --#
    config = configparser.ConfigParser()
    baseDir = os.path.join(sys.path[0],c_vars.ruleDirectory, c_vars.ruleName)
    parseConfig(g_vars,c_vars,baseDir,config)
    
    ##---initialize 'S' for the grammar-----#
    pcfg.grammar.append({'name':'S','replacements':[]})
    
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