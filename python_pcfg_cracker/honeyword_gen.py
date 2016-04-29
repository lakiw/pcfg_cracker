#!/usr/bin/env python3

########################################################################################
#
# Name: Honeyword Generator
#  --Generate honeywords, (synthetic passwords), from a PCFG grammar
#
#  Written by Matt Weir
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
#  honeyword_gen.py
#
#########################################################################################

##--Including this to print error message if python < 3.0 is used
from __future__ import print_function
import sys
###--Check for python3 and error out if not--##
if sys.version_info[0] < 3:
    print("This program requires Python 3.x", file=sys.stderr)
    sys.exit(1)
    
import argparse
import os  ##--Used for file path information

#Custom modules
from pcfg_manager.file_io import load_grammar
from pcfg_manager.core_grammar import PcfgClass, print_grammar
from pcfg_manager.ret_types import RetType


#########################################################################################
# Holds the command line values
# Also holds the default values if you don't want to enter them every time you run this
#########################################################################################
class CommandLineVars:
    def __init__(self):
        self.rule_name = "Default"
        self.num_honeywords = 1
        #Debugging printouts
        #-They actually are initialized false under parse_command_line regardless of the value here
        self.verbose = False  
        
       
####################################################
# Simply parses the command line
####################################################
def parse_command_line(command_line_results):
    parser = argparse.ArgumentParser(description='Honeyword Generator: Generates honeywords, (synthetic passwords), from a PCFG grammar')
    parser.add_argument('--rule','-r', help='The rule set to use. Default: (%(default)s)',metavar='RULE_SET',required=False, default= command_line_results.rule_name)
    parser.add_argument('--verbose','-v', help='Verbose prints. Only use for debugging otherwise it will make parsing the output harder',dest='verbose', action='store_true')
    parser.add_argument(
        '--num_honeywords',
        '-n', 
        help='Number of honeywords to generate. Default: (%(default)s)',
        metavar='NUM_HONEYWORDS', 
        required=False,
        type=int, 
        default=command_line_results.num_honeywords)
    try:
        args=parser.parse_args()
        command_line_results.rule_name = args.rule
        command_line_results.verbose = args.verbose
        command_line_results.num_honeywords = args.num_honeywords
    except:
        return RetType.COMMAND_LINE_ERROR

    ##--Perform some sanity checks on the input
    if command_line_results.num_honeywords <= 0:
        print("Error, you need to have a value greater than 0", file=sys.stderr)
        return RetType.COMMAND_LINE_ERROR

    return RetType.STATUS_OK 

    
###################################################################################
# Prints the startup banner when this tool is run
###################################################################################
def print_banner(program_details):
    print('',file=sys.stderr)
    print ("Honeyword Generator version " + program_details['Version'], file=sys.stderr)
    print ("Written by " + program_details['Author'], file=sys.stderr)
    print ("Sourcecode available at " + program_details['Source'], file=sys.stderr)
    print('',file=sys.stderr)
    return RetType.STATUS_OK  


####################################################################################
# ASCII art for displaying an error state before quitting
####################################################################################
def print_error():
    print('',file=sys.stderr)
    print('An error occured, shutting down',file=sys.stderr)
    print('',file=sys.stderr)
    print(r' \__/      \__/      \__/      \__/      \__/      \__/          \__/',file=sys.stderr)
    print(r' (oo)      (o-)      (@@)      (xx)      (--)      (  )          (OO)',file=sys.stderr)
    print(r'//||\\    //||\\    //||\\    //||\\    //||\\    //||\\        //||\\',file=sys.stderr)
    print(r'  bug      bug       bug/w     dead      bug       blind      bug after',file=sys.stderr)
    print(r'         winking   hangover    bug     sleeping    bug     whatever you did',file=sys.stderr)
    print('',file=sys.stderr)
    return RetType.STATUS_OK

  
##################################################################
# Main function, not that exciting
##################################################################
def main():
    
    ##--Information about this program--##
    program_details = {
        'Program':'honeyword_gen.py',
        'Version': '3.1',
        'Author':'Matt Weir',
        'Contact':'cweir@vt.edu',
        'Source':'https://github.com/lakiw/pcfg_cracker'
    }
       
     ##--Print out banner
    print_banner(program_details)
    
    ##--Parse the command line ---##
    command_line_results = CommandLineVars()
    if parse_command_line(command_line_results) != RetType.STATUS_OK:
        return RetType.QUIT
   
    ##--Specify where the rule file is located
    rule_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)),'Rules', command_line_results.rule_name)   
   
    ##--Initialize the grammar--##
    grammar = []
    ret_value = load_grammar(rule_directory, grammar)
    if ret_value != RetType.STATUS_OK:
        print ("Error loading the PCFG grammar, exiting",file=sys.stderr)
        print_error()
        return ret_value
 
    pcfg = PcfgClass(grammar)

    ##--Generate the honeywords--##
    print("Generating Honeywords", file=sys.stderr)
    print("--------------------------------", file=sys.stderr)
    # First find the start index
    start_index = pcfg.start_index()
    if start_index == -1:
        print("Error with the grammar, could not find the start index", file=sys.stderr)
        return RetType.ERROR_QUIT
    for i in range(0,command_line_results.num_honeywords):
        parse_tree = pcfg.random_grammar_walk(start_index)
        print(parse_tree)
    
      
    return RetType.STATUS_OK
    

if __name__ == "__main__":
    main()