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
import os  ##--Used for file path information


#Custom modules
from pcfg_manager.file_io import load_grammar
from pcfg_manager.core_grammar import PcfgClass
from pcfg_manager.priority_queue import PcfgQueue, QueueItem, test_queue
from pcfg_manager.ret_types import RetType


#########################################################################################
# Holds the command line values
# Also holds the default values if you don't want to enter them every time you run this
#########################################################################################
class CommandLineVars:
    def __init__(self):
        self.rule_name = "Default"
        #Debugging printouts
        self.verbose = False  
        self.queue_info = False
        ##--temporary value---
        self.input_dictionary = "passwords.lst"


####################################################
# Simply parses the command line
####################################################
def parse_command_line(command_line_results):
    parser = argparse.ArgumentParser(description='PCFG_Cracker: Used to generate password guesses for use in other cracking programs')
    parser.add_argument('--rule','-r', help='The rule set to use. Default is \"Default\"',metavar='RULE_SET',required=False, default= command_line_results.rule_name)
    parser.add_argument('--verbose','-v', help='Verbose prints. Only use for debugging otherwise it will generate junk guesses',dest='verbose', action='store_true')
    parser.add_argument('--queue_info','-q', help='Prints the priority queue info vs guesses. Used for debugging',dest='queue_info', action='store_true')
    try:
        args=parser.parse_args()
        command_line_results.rule_name = args.rule
        command_line_results.verbose = args.verbose
        command_line_results.queue_info = args.queue_info
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
#    import copy
#    test1 = [5,0,[[10,0,[8,0,[]]],[2,1,[]]]]
    
#    test2 = [5,0,[[10,0,[8,0,[]]],[2,0,[]]]]
    
#    test1[0] = 9
#    test1[0] = 5
    
#    print(test1)
#    print(test2)
#    if test1 == test2:
#        print("match")
#    return
    
    
    ##--Information about this program--##
    program_details = {
        'Program':'pcfg_manager.py',
        'Version': '3.0 Alpha',
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
    
    ##--Initialize the priority queue--##
    p_queue = PcfgQueue()
    ret_value = p_queue.initialize(pcfg)
    if ret_value != RetType.STATUS_OK:
        print ("Error initalizing the priority queue, exiting",file=sys.stderr)
        print_error()
        return ret_value
    
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
        print(str(queue_item.probability) + " : " + str(queue_item.parse_tree))
        num_preterminals = num_preterminals +1
        guess_start_time = time.perf_counter()
        num_guesses = num_guesses + len(pcfg.list_terminals(queue_item.parse_tree))
        
        guess_stop_time = time.perf_counter() - guess_start_time
        if command_line_results.queue_info == True:
            if num_preterminals % 1000 == 0:
                print ("PQueue:" + str(len(p_queue.p_queue)),file=sys.stderr)
                print ("Total number of Pre Terminals: " + str (num_preterminals),file=sys.stderr)
                print ("PQueueTime " + str(p_queue_stop_time),file=sys.stderr)
                print ("Guesses:" + str(num_guesses),file=sys.stderr)
                print ("GuessTime " + str(guess_stop_time),file=sys.stderr)
                print ("Average num of guesses per preterm: " + str(num_guesses // num_preterminals),file=sys.stderr)
                print ("Total Time " + str(time.perf_counter() - total_time_start),file=sys.stderr)
                print ("Number of guesses a second: " + str(num_guesses // (time.perf_counter() - total_time_start)),file=sys.stderr)
                print ("Current probability: " + str(p_queue.max_probability),file=sys.stderr)
                #print ("Parse Tree : " + str(queue_item.parse_tree))
                print ()

        else:
            for guess in pcfg.list_terminals(queue_item.parse_tree):
                try:
                    print(guess)
                except UnicodeEncodeError:
                    print("UNICODE_ERROR")
        p_queue_start_time = time.perf_counter()
        queue_item_list = []        
        ret_value = p_queue.next_function(pcfg, queue_item_list)
        if len(queue_item_list) > 0:
            queue_item = queue_item_list[0]
        p_queue_stop_time = time.perf_counter() - p_queue_start_time
    #ret_value = test_queue(pcfg)
   
    print ("Final number of Pre Terminals: " + str (num_preterminals),file=sys.stderr)
    return RetType.STATUS_OK
    

if __name__ == "__main__":
    main()