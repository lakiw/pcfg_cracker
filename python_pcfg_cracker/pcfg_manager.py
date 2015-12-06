#!/usr/local/bin/python3

########################################################################################
#
# Name: PCFG Manager
# Last updated: 12/06/2015
#  --Probabilistic Context Free Grammar (PCFG) Password Guessing Program
#
#  Written by Matt Weir
#  Backend algorithm developed by Matt Weir, Sudhir Aggarwal, and Breno de Medeiros
#  Special thanks to Bill Glodek for work on an earlier version
#  Special thanks to the National Institute of Justice and the NW3C for support with the initial reasearch
#  Huge thanks to Florida State University's ECIT lab where this was developed
#  And the list goes on and on... And thank you whoever is reading this. Be good!
#
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#
#  Contact Info: cweir@vt.edu
#
#  pcfg_manager.py
#
#########################################################################################

from __future__ import print_function
import sys
import argparse
import time

#Custom modules
sys.path.append('./lib')
from file_io import loadConfig, loadRules
from core_grammar import PcfgClass, test_grammar
from priority_queue import pcfgQueue, queueItem, testQueue


#########################################################################################
# Holds the command line values
# Also holds the default values if you don't want to enter them every time you run this
#########################################################################################
class commandLineVars:
    def __init__(self):
        self.configFile = ""
        self.ruleName = "Default"
        self.ruleDirectory = "Rules"
        #Debugging printouts
        self.verbose = True  
        ##--temporary value---
        self.inputDictionary = "passwords.lst"

############################################################################################
# Guess they aren't technically global...
############################################################################################
class globalVars:               
    def __init__(self):
        self.maxDicWord = 32
        ##--I know, having detailed retvalues doesn't add a lot for a program like this, but it satisfies some sort of OCD itch of mine
        self.RETValues = {'STATUS_OK':0,'File_IO_Error':1, 'QUEUE_EMPTY':2, 'WEIRD_ERROR':3, 'QUEUE_FULL_ERROR':4}
        
        ##--The current queueItem we are working on
        self.qItem = queueItem()

####################################################
# Simply parses the command line
####################################################
def parseCommandLine(c_vars):
    parser = argparse.ArgumentParser(description='PCFG_Cracker version 3.0. Used to generate password guesses for use in other cracking programs')
    parser.add_argument('--config','-c', help='The configuration file to use',metavar='CONFIG_FILE',required=False, default=c_vars.configFile)
    parser.add_argument('--feature', dest='feature', action='store_true')
    parser.add_argument('--verbose','-v', help='Verbose prints. Only use for debugging otherwise it will generate junk guesses',dest='verbose', action='store_false')
    args=vars(parser.parse_args())
    c_vars.configFile = args['config']
    c_vars.verbose = args['verbose']
    return 0 


##################################################################
# Main function, not that exciting
##################################################################
def main():
    c_vars = commandLineVars()
    g_vars = globalVars()
    pcfg = PcfgClass()
    
    ##--Initialize the priority queue--##
    pQueue = pcfgQueue()
    pQueue.initialize(pcfg)
    ##--Parse the command line ---##
    parseCommandLine(c_vars)
    if c_vars.verbose == True:
        print ("PCFG_Cracker version 3.0")
        
    ##--Parse the main config file----#
    retValue = loadConfig(g_vars,c_vars)
    if retValue != g_vars.RETValues['STATUS_OK']:
        print ("Error reading config file, exiting")
        return retValue
    
    ##--Load the rules file---##
    retValue = loadRules(g_vars,c_vars,pcfg)
    if retValue != g_vars.RETValues['STATUS_OK']:
        print ("Error reading Rules file, exiting")
        return retValue

    ##--Going to break this up eventually into it's own function, but for now, process the queue--##
    retValue = pQueue.nextFunction(g_vars,c_vars,pcfg)
    numpre_terminals = 0
    numGuesses = 0
    pQueueStartTime = 0
    pQueueStopTime = 0
    guessStartTime = 0
    guessStopTime = 0
    totalTimeStart = time.perf_counter()
    while retValue == g_vars.RETValues['STATUS_OK']:
#       print(str(g_vars.qItem.probability) + " : " + str(g_vars.qItem.parseTree))
        numpre_terminals = numpre_terminals +1
        guessStartTime = time.perf_counter()
        numGuesses = numGuesses + len(pcfg.list_terminals(g_vars.qItem.parseTree))
        
        guessStopTime = time.perf_counter() - guessStartTime
        if numpre_terminals % 10000 == 0:
            print ("PQueue:" + str(len(pQueue.pQueue)))
#            print ("Total number of Pre Terminals: " + str (numpre_terminals))
#            print ("PQueueTime " + str(pQueueStopTime))
#            print ("Guesses:" + str(numGuesses))
#            print ("GuessTime " + str(guessStopTime))
#            print ("Average num of guesses per preterm: " + str(numGuesses // numpre_terminals))
#            print ("Total Time " + str(time.perf_counter() - totalTimeStart))
#            print ("Number of guesses a second: " + str(numGuesses // (time.perf_counter() - totalTimeStart)))
            print ("Current probability: " + str(pQueue.maxProbability))
        for guess in pcfg.list_terminals(g_vars.qItem.parseTree):
            print(guess)
        pQueueStartTime = time.perf_counter()  
        retValue = pQueue.nextFunction(g_vars,c_vars,pcfg)
        pQueueStopTime = time.perf_counter() - pQueueStartTime
    #retValue = testQueue(g_vars,c_vars,pcfg)
    #retValue = test_grammar(g_vars,c_vars,pcfg)
   
    
    return g_vars.RETValues['STATUS_OK']
    

if __name__ == "__main__":
    main()