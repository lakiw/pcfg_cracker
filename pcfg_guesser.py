#!/usr/bin/env python3


########################################################################################
#
# Name: PCFG Guesser
#  --Probabilistic Context Free Grammar (PCFG) Password Guessing Program
#
#  Written by Matt Weir
#  Initial backend algorithm developed by Matt Weir, Sudhir Aggarwal, and Breno de Medeiros
#  Special thanks to Bill Glodek for collaboration on original proof of concept
#  Special thanks to the National Institute of Justice and the NW3C for support with the initial reasearch
#  Huge thanks to Florida State University's ECIT lab where the original version was developed
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
#  pcfg_guesser.py
#
#########################################################################################


# Including this to print error message if python < 3.0 is used
from __future__ import print_function
import sys
# Check for python3 and error out if not
if sys.version_info[0] < 3:
    print("This program requires Python 3.x", file=sys.stderr)
    sys.exit(1)

# Global imports    
import argparse
import os
import traceback

# Local imports
from lib_guesser.banner_info import print_banner, print_error
from lib_guesser.pcfg_grammar import PcfgGrammar
from lib_guesser.cracking_session import CrackingSession

       
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
        
    ## Standard options for ruleset, etc
    #
    # The rule name to load the grammar from. Should be saved under the
    # 'Rules' folder. This rule needs to have been previously created by
    # the pcfg 'trainer.py' program.
    parser.add_argument(
        '--rule',
        '-r',
        help = 'The ruleset to use. Default is ' + 
        program_info['rule_name'],
        metavar = 'RULESET_NAME',
        required = False,
        default = program_info['rule_name']
    )

    ## Debugging and research information
    #
    parser.add_argument(
        '--queue_info',
        '-q', 
        help='Prints the priority queue info vs guesses. Used for debugging',
        dest='queue_info', 
        action='store_const', 
        const= not program_info['queue_info']
    )
        
    # Parse all the args and save them    
    args=parser.parse_args() 
    
    # Standard Options
    program_info['rule_name'] = args.rule
   
    # Debugging Options
    program_info['queue_info'] = args.queue_info

    return True 

  
## Main function, starts everything off
#    
def main():

    # Information about this program
    program_info = {
    
        # Program and Contact Info
        'name':'PCFG Guesser',
        'version': '4.0',
        'author':'Matt Weir',
        'contact':'cweir@vt.edu',
        
        # Standard Options
        'rule_name':'Default',
        
        # Debugging Options
        'queue_info': False,

    }
      
    print_banner()
    print("Version: " + str(program_info['version']),file=sys.stderr)
    print('',file=sys.stderr)
    
    # Parsing the command line
    if not parse_command_line(program_info):
        # There was a problem with the command line so exit
        print("Exiting...")
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
            debug = False
            )
        
    except Exception as msg:
        traceback.print_exc(file=sys.stdout)
        print("Exception: " + str(msg))
        print("Exiting")
        return
    
    
    # Initalize the cracking session
    current_cracking_session = CrackingSession(pcfg = pcfg)
    
    # Setup is done, now start generating rules
    print ("Starting to generate password guesses",file=sys.stderr)
    print ("Press [ENTER] to display a status output",file=sys.stderr)
    
    current_cracking_session.run(print_queue_info = program_info['queue_info'])
    
    
if __name__ == "__main__":
    main()
