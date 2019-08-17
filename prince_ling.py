#!/usr/bin/env python3


################################################################################
#
# Name: PRINCE-LING
#  -- PRINCE Language Indexed N-Grams
#
#  -- Uses data from the PCFG trainer to make wordlists optimized for use
#     in PRINCE stlye attacks
#
#  Written by Matt Weir
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
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#
#  Contact Info: cweir@vt.edu
#
#  prince_ling.py
#
################################################################################


# Including this to print error message if python < 3.0 is used
from __future__ import print_function
import sys
# Check for python3 and error out if not
if sys.version_info[0] < 3:
    print("This program requires Python 3.x", file=sys.stderr)
    sys.exit(1)
    
import argparse
import os  
import traceback
from collections import Counter

# Local imports
from lib_princeling.banner_info import print_banner
from lib_guesser.pcfg_grammar import PcfgGrammar
from lib_princeling.wordlist_generation import create_prince_wordlist


## Parses the command line
#
# Responsible for parsing the command line.
#
# If you have any command line options that you want to add, they go here.
#
# All results are returned as a dictionary in 'program_info'
#
# If successful, returns True, returns False if value error, program exits if
# argparse catches a problem.
#
def parse_command_line(program_info):

    # Keeping the title text to be generic to make re-using code easier
    parser = argparse.ArgumentParser(
        description= program_info['name'] +
        ', version: ' + 
        program_info['version']
    )
        
    ## Standard options
    #
    # The rule name to use for generating the wordlist
    parser.add_argument(
        '--rule',
        '-r',
        help = 'Name of PCFG ruleset to generate the PRINCE wordlist. Default is ' + 
        program_info['rule_name'],
        metavar = 'RULESET_NAME',
        required = False,
        default = program_info['rule_name']
    )
    
    # The output file to save results too 
    parser.add_argument(
        '--output',
        '-o',
        help = 'The output file to save results to. If not specified will output to stdout',
        metavar = 'OUTPUT_FILENAME',
        required = False,
        default = program_info['output_file']
    )
    
    # Max size of wordlist to generate
    parser.add_argument(
        '--size',
        '-s',
        help = 'The maximum size of wordlist to generate. If not specified, will create words from terminals until grammar is exhausted',
        metavar = 'MAX_SIZE',
        required = False,
        default = program_info['max_size'],
        type = int, 
    )
    
    # Parse all the args and save them    
    args=parser.parse_args() 
    
    # Standard Options
    program_info['rule_name'] = args.rule
    program_info['output_file']= args.output
    program_info['max_size'] = args.size
    
    ## Sanity checking of values
    #
    # Check to make sure limit makes sense
    if program_info['max_size']!= None and program_info['max_size'] <= 0:
        print("Error, max size must be greater than 0")
        return False
        
    return True
    
    
## Main function, starts everything off
#    
def main():

    # Information about this program
    program_info = {
    
        # Program and Contact Info
        'name':'PRINCE-LING',
        'version': '4.0.1',
        'author':'Matt Weir',
        'contact':'cweir@vt.edu',
        
        # Standard Options
        'rule_name':'Default',
        'output_file':None,
        'max_size':None,
        
    }
    
    print_banner()
    print("Version: " + str(program_info['version']),file=sys.stderr)
    print()
    
    # Parsing the command line
    if not parse_command_line(program_info):
        # There was a problem with the command line so exit
        print("Exiting...",file=sys.stderr)
        return
        
    # Get the base directory to load all of the rules from
    #
    # Don't want to use the relative path since who knows where someone is 
    # invoking this script from
    #
    # Also aiming to make this OS independent/
    #
    base_directory = os.path.join(
                        os.path.dirname(os.path.realpath(__file__)),
                        'Rules',
                        program_info['rule_name']
                        )     
    
    ## Create the grammar
    #
    # Note, if the ruleset can not be loaded, (for example it doesn't exist),
    # it will throw an exception.
    try:
        print("Loading Ruleset: " + str(program_info['rule_name']),file=sys.stderr)
        print('',file=sys.stderr)
        pcfg = PcfgGrammar(
            program_info['rule_name'], 
            base_directory,
            program_info['version'],
            base_structure_folder = "Prince",
            )
        
    except Exception as msg:
        print(msg)
        print("Exiting")
        return
        
    create_prince_wordlist(pcfg, program_info['max_size'], base_directory, program_info['output_file'])
    
        
if __name__ == "__main__":
    main() 