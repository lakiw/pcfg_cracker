#!/usr/local/bin/python3

########################################################################################
#
# Name: PCFG Manager
# Last updated: 8/21/2015
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

#Custom modules
sys.path.append('./lib')
from file_io import loadConfig, loadRules
from core_grammar import pcfgClass, testGrammar


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

############################################################################################
# Guess they aren't technically global...
############################################################################################
class globalVars:               
    def __init__(self):
        self.maxDicWord = 32
        ##--I know, having detailed retvalues doesn't add a lot for a program like this, but it satisfies some sort of OCD itch of mine
        self.RETValues = {'STATUS_OK':0,'File_IO_Error':1}

####################################################
# Simply parses the command line
####################################################
def parseCommandLine(c_vars):
    parser = argparse.ArgumentParser(description='PCFG_Cracker version 3.0. Used to generate password guesses for use in other cracking programs')
    parser.add_argument('--config','-c', help='The configuration file to use',metavar='CONFIG_FILE',required=False, default=c_vars.configFile)
    parser.add_argument('--feature', dest='feature', action='store_true')
    parser.add_argument('--verbose','-v', help='Verbose prints. Only use for debugging otherwise it will generate junk guesses',dest='verbose', action='store_true')
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
    pcfg = pcfgClass()
    
    ##--Parse the command line ---##
    parseCommandLine(c_vars)
    if c_vars.verbose == True:
        print ("PCFG_Cracker version 3.0")
        
    ##--Parse the main config file----#
    retValue = loadConfig(g_vars,c_vars)
    if retValue != g_vars.RETValues['STATUS_OK']:
        print ("Error reading config file, exiting")
        return True
    
    ##--Load the rules file---##
    retValue = loadRules(g_vars,c_vars,pcfg)
    if retValue != g_vars.RETValues['STATUS_OK']:
        print ("Error reading Rules file, exiting")
        return True
    
    retValue = testGrammar(g_vars,c_vars,pcfg)
    

if __name__ == "__main__":
    main()