#!/usr/local/bin/python3

########################################################################################
#
# Name: PCFG_Cracker core grammar code
# Description: Holds the top level code for manipulating the pcfg.
#              For example the deadbeat dad "next" function, memory management, etc
#
#########################################################################################

from __future__ import print_function
import sys
import string
import struct
import os
import types
import time

#Used for debugging and development
from sample_grammar import s_preTerminal


##########################################################################################
# Main class of this program as it represents the central grammar of the pcfg cracker
# I'm trying to keep the actual grammar as generic as possible.
# You can see a sample grammar in sample_grammar.python, but I'm really trying to keep this
# generic enough to support things like recursion.
#
# Each transition is represented by a python dictionary of the form:
#   'name':'S' //Human readable name. Used for status messages and debugging
#   'replacements': [List of all the replacements] //the transitions that are allowed for this pre-terminal
#
# Each replacement is represented by a python dictionary and a single non-termial can mix and
# match what types of replacements it supports. That being said, the logic on how to actually fill
# out certain replacements may require certain chaining. Aka as it is currently set up, a capitalization
# replacement needs to occur after a dictionary word replacement
# Here are some example fields for a replacement
#   'isTerminal':False //Required. I guess I don't need to use this field if I structured some things differently but it says if there are any future transitions or not
#   'pos':[5,3]  //Required for non-terminals. Acts like pointers into the grammar for what future replacements should be applied to this section.
#                //You can have multiple replacements for example A->AB or A->BC
#   'prob':0.00021 //Required for non-terminals. The probability this transition occurs at. Please note the probability is associated with the transition itself and not the terminals that it is pointed to
#                  //Aka if you are pointing to a dictionary of 10,000 words, and the probabilty associated with it is .1, then the combined probability of all the created terminals would be 100.0 or 10000%.
#                  //In that case the probability probably should have been 0.001 instead
#   'pre_terminal':["pas","cat","dog","hat"]  //dictionary of pre-terminals that should be applied for this transition. Note it's just a nameing convention to differentiate pre-terminals and terminals
#   'terminal':['2','3','4']  //A listing of terminals to apply. Since they are terminals there are no futher transitions
#
#   Note, there are also functions that deal with the nitty gritty about how to actually perform the transitions. Eventually I'd like to move them to a plug-in archetecture, but currently
#   they are hardcoded
#   'function':'shadow'  //Used for pre-terminals like dictionary words where you want to send the current list of words to the next transition so it can do things like apply capitalization rules
#   'function':'copy'    //Used for terminals to do a straight swap of the contents. like have a D->'1'
#   'function':'capitalize'  //Used to capitalize words passed in by the previous 'shadow' function
#   'function':'transparent'  //There is no list of words associated with this transition. Instead you are just pushing new transitions into the stack. Aka S->AB
#   'function':'digit_bruteforce'  //Used to bruteforce digits. Much like shadow but instead of having a 'terminal' list it generates it via brute force
#     ----'input':{'length':1}  ///Has additional variables influencing how it is applied. In this case, brute force all 1 digit values
#
#    Considering how I'm still designing/writing this code, the above is almost certainly going to change
#
##########################################################################################
class pcfgClass:
    ########################################################
    # Initialize the class, not really doing anything here
    ########################################################
    def __init__(self):
        ###---The actual grammar. It'll be loaded up later
        self.grammar = []
    
    ##############################################################################
    # Top level function used to return all the terminals / password guesses
    # associated with the preTerminal passed it
    ##############################################################################
    def listTerminals(self,preTerminal):
        terminalList = []
        #First grab a list of all the preterminals. It'll take the form of nested linked lists.
        #For example expantTerminals will return something like [['cat','hat','dog'],[1,2]].
        guessCombos = self.expandTerminals(preTerminal,workingValue=[])
        #Now take the combos and generate guesses. Following the above example, create the guesses cat1,hat1,dog1,cat2,hat2,dog2
        terminalList = self.expandFinalString(guessCombos)
        return terminalList
    
    ##############################################################################
    # Used to expend a nested list of pre-terminals into actual password guesses
    # Input will be something like this: [['cat','hat','dog',Cat,Hat,Dog],[1,2]]
    # Output should be something like this: cat1,hat1,dog1,Cat1,Hat1,Dog1,cat2,hat2,dog2,Cat2,Hat2,Dog2
    ###############################################################################
    def expandFinalString(self,guessCombos):
        ##--Time to get all recursive!--
        if len(guessCombos)==1:
            return guessCombos[0]
        else:
            retStrings = []
            recursiveStrings = self.expandFinalString(guessCombos[1:])
            for frontString in guessCombos[0]:
                for backString in recursiveStrings:
                    retStrings.append(frontString + backString)
            return retStrings
        
            
            
    #################################################################################
    # Used to create a nested list of all the pre-terminals. Note the end results should
    # just be strings that can be combined together. All complex transforms need to be done
    # in this function. For example it needs to apply all capitalization mangling rules.
    ########################################################################################
    def expandTerminals(self,curSection,workingValue=[]):
        curCombo = workingValue
        ##--Overly complicated to read, I know, but it just parses the grammar and grabs the parts we care about for this section, (replacements)
        ##--Some of the craziness is I'm using the values in curSection[0,1] to represent pointers into the grammar
        curDic = self.grammar[curSection[0]]['replacements'][curSection[1]]
        ##----Now deal with the different types of transition functions----------###
        
        ##----If you are copying the actual values over, aka D1->['1','2','3','4']. This is the simplest one
        if curDic['function']=='copy':
            curCombo = curDic['terminal']
            
        ##----If you are copying over values that aren't terminals. For example L3=>['cat','hat']. They are not terminals since you still need to apply capitalization rules to them
        elif curDic['function']=='shadow':
            ##--Pass the value to the next replacement to take care of
            curCombo =  self.expandTerminals(curSection[2][0],curDic['pre_terminal'])
        ##----Capitalize the value passed in from the previous section----
        elif curDic['function']=='capitalize':
            tempCombo=[]
            for rule in curDic['terminal']:
                for word in curCombo:
                    tempWord =''
                    for letterPos in range(0,len(word)):
                        if rule[letterPos]=='U':
                            tempWord += word[letterPos].upper()
                        else:
                            tempWord += word[letterPos]
                    tempCombo.append(tempWord)
            curCombo = tempCombo
        ##---Potentially adding a new replacement. aka S->ABC. This is more of a traditional PCFG "non-terminal"
        elif curDic['function']=='transparent':
            for rule in curSection[2]:
                curCombo.append(self.expandTerminals(rule))
        return curCombo
        
    ##############################################################################################
    # Used to find the probability of a parse tree in the graph
    ##############################################################################################
    def findProbability(self,pt):
        ##--Start at 100%
        currentProb = self.grammar[pt[0]]['replacements'][pt[1]]['prob']
        if len(pt[2]) != 0:
            for x in range(0,len(pt[2])):
                childProb = self.findProbability(pt[2][x])
                currentProb =currentProb * childProb
        return currentProb
        
        
    ###############################################################################################
    # Used to find if a node is ready to be printed out or not
    ###############################################################################################
    def findIsTerminal(self,pt):
        if len(pt[2])==0:
            if self.grammar[pt[0]]['replacements'][pt[1]]['isTerminal'] == False:
                return False
        else:
            for x in range(0,len(pt[2])):
                if self.findIsTerminal(pt[2][x]) == False:
                    return False
        return True
                
###################################################################
# Function I'm using to test how the password guesses are being
# generated from a pre-terminal structure and the PCFG grammar
####################################################################                
def testGrammar(g_vars,c_vars,pcfg):
    pcfg.printTerminals(s_preTerminal)
    
        