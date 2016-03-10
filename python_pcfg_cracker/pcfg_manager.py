#!/usr/bin/env python3

########################################################################################
#
# Name: PCFG Manager
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


import sys
import argparse
import time

#Custom modules
from pcfg_manager.file_io import load_config, load_rules
from pcfg_manager.core_grammar import PcfgClass, test_grammar
from pcfg_manager.priority_queue import PcfgQueue, QueueItem, test_queue
from pcfg_manager.ret_types import RetType


#########################################################################################
# Holds the command line values
# Also holds the default values if you don't want to enter them every time you run this
#########################################################################################
class CommandLineVars:
    def __init__(self):
        self.rule_name = "Default"
        self.rule_directory = "Rules"
        #Debugging printouts
        self.verbose = True  
        ##--temporary value---
        self.input_dictionary = "passwords.lst"


####################################################
# Simply parses the command line
####################################################
def parse_command_line(command_line_results):
    parser = argparse.ArgumentParser(description='PCFG_Cracker: Used to generate password guesses for use in other cracking programs')
    parser.add_argument('--rule','-r', help='The rule set to use. Default is \"Default\"',metavar='RULE_SET',required=False, default= command_line_results.rule_name)
    parser.add_argument('--verbose','-v', help='Verbose prints. Only use for debugging otherwise it will generate junk guesses',dest='verbose', action='store_true')
    try:
        args=parser.parse_args()
        command_line_results.rule_name = args.rule
        command_line_results.verbose = args.verbose
    except:
        return RetType.COMMAND_LINE_ERROR

    return RetType.STATUS_OK 

    
###################################################################################
# ASCII art for the banner
###################################################################################
def print_banner(program_details):
    print('',file=sys.stderr)
    print ("PCFG_Cracker version " + program_details['Version'], file=sys.stderr)
    print ("Written by " + program_details['Author'], file=sys.stderr)
    print ("Sourcecode available at " + program_details['Source'], file=sys.stderr)
    print('',file=sys.stderr)
    return RetType.STATUS_OK    

##################################################################
# Main function, not that exciting
##################################################################
def main():
    
    ##--Information about this program--##
    program_details = {
        'Program':'pcfg_manager.py',
        'Version': '3.0',
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
    
   
    ##--Initialize the grammar--##
    pcfg = PcfgClass()
    
    ##-- Read in the config file for the current ruleset -- ##
    
    
    ##--Initialize the priority queue--##
    p_queue = PcfgQueue()
    p_queue.initialize(pcfg)
    
    
        
    ##--Parse the main config file----#
    ret_value = load_config(command_line_results)
    
    if ret_value != RetType.STATUS_OK:
        print ("Error reading config file, exiting")
        return ret_value
    
    ##--Load the rules file---##
    ret_value = load_rules(command_line_results,pcfg)
    if ret_value != RetType.STATUS_OK:
        print ("Error reading Rules file, exiting")
        return ret_value

    ##--Debugging return since I'm currently working on reading in the grammar --##
    return
    
    ##--Going to break this up eventually into it's own function, but for now, process the queue--##
    queue_item_list = []
    ret_value = p_queue.next_function(pcfg, queue_item_list)
    if len(queue_item_list) > 0:
        queue_item = queue_item_list[0]
    
    num_preterminals = 0
    num_guesses = 0
    p_queue_start_time = 0
    p_queue_stop_time = 0
    guess_start_time = 0
    guess_stop_time = 0
    total_time_start = time.perf_counter()
    while ret_value == RetType.STATUS_OK:
#       print(str(queue_item.probability) + " : " + str(queue_item.parse_tree))
        num_preterminals = num_preterminals +1
        guess_start_time = time.perf_counter()
        num_guesses = num_guesses + len(pcfg.list_terminals(queue_item.parse_tree))
        
        guess_stop_time = time.perf_counter() - guess_start_time
        if num_preterminals % 10000 == 0:
            print ("PQueue:" + str(len(queue_item.p_queue)))
#            print ("Total number of Pre Terminals: " + str (num_preterminals))
#            print ("PQueueTime " + str(p_queue_stop_time))
#            print ("Guesses:" + str(num_guesses))
#            print ("GuessTime " + str(guess_stop_time))
#            print ("Average num of guesses per preterm: " + str(num_guesses // num_preterminals))
#            print ("Total Time " + str(time.perf_counter() - total_time_start))
#            print ("Number of guesses a second: " + str(num_guesses // (time.perf_counter() - total_time_start)))
            print ("Current probability: " + str(p_queue.max_probability))
        for guess in pcfg.list_terminals(queue_item.parse_tree):
            print(guess)
        p_queue_start_time = time.perf_counter()
        queue_item_list = []        
        ret_value = p_queue.next_function(pcfg, queue_item_list)
        if len(queue_item_list) > 0:
            queue_item = queue_item_list[0]
        p_queue_stop_time = time.perf_counter() - p_queue_start_time
    #ret_value = test_queue(pcfg)
    #ret_value = test_grammar(pcfg)
   
    
    return RetType.STATUS_OK
    

if __name__ == "__main__":
    main()