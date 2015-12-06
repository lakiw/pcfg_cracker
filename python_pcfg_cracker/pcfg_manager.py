#!/usr/bin/env python3

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


import sys
import argparse
import time

#Custom modules
from lib.file_io import load_config, load_rules
from lib.core_grammar import PcfgClass, test_grammar
from lib.priority_queue import PcfgQueue, QueueItem, test_queue


#########################################################################################
# Holds the command line values
# Also holds the default values if you don't want to enter them every time you run this
#########################################################################################
class CommandLineVars:
    def __init__(self):
        self.config_file = ""
        self.rule_name = "Default"
        self.rule_directory = "Rules"
        #Debugging printouts
        self.verbose = True  
        ##--temporary value---
        self.input_dictionary = "passwords.lst"

############################################################################################
# Guess they aren't technically global...
############################################################################################
class GlobalVars:               
    def __init__(self):
        self.max_dic_word = 32
        ##--I know, having detailed retvalues doesn't add a lot for a program like this, but it satisfies some sort of OCD itch of mine
        self.ret_values = {'STATUS_OK':0,'FILE_IO_ERROR':1, 'QUEUE_EMPTY':2, 'WEIRD_ERROR':3, 'QUEUE_FULL_ERROR':4}
        
        ##--The current QueueItem we are working on
        self.q_item = QueueItem()

####################################################
# Simply parses the command line
####################################################
def parse_command_line(c_vars):
    parser = argparse.ArgumentParser(description='PCFG_Cracker version 3.0. Used to generate password guesses for use in other cracking programs')
    parser.add_argument('--config','-c', help='The configuration file to use',metavar='CONFIG_FILE',required=False, default=c_vars.config_file)
    parser.add_argument('--feature', dest='feature', action='store_true')
    parser.add_argument('--verbose','-v', help='Verbose prints. Only use for debugging otherwise it will generate junk guesses',dest='verbose', action='store_false')
    args=vars(parser.parse_args())
    c_vars.config_file = args['config']
    c_vars.verbose = args['verbose']
    return 0 


##################################################################
# Main function, not that exciting
##################################################################
def main():
    c_vars = CommandLineVars()
    g_vars = GlobalVars()
    pcfg = PcfgClass()
    
    ##--Initialize the priority queue--##
    p_queue = PcfgQueue()
    p_queue.initialize(pcfg)
    ##--Parse the command line ---##
    parse_command_line(c_vars)
    if c_vars.verbose == True:
        print ("PCFG_Cracker version 3.0")
        
    ##--Parse the main config file----#
    ret_value = load_config(g_vars,c_vars)
    if ret_value != g_vars.ret_values['STATUS_OK']:
        print ("Error reading config file, exiting")
        return ret_value
    
    ##--Load the rules file---##
    ret_value = load_rules(g_vars,c_vars,pcfg)
    if ret_value != g_vars.ret_values['STATUS_OK']:
        print ("Error reading Rules file, exiting")
        return ret_value

    ##--Going to break this up eventually into it's own function, but for now, process the queue--##
    ret_value = p_queue.next_function(g_vars,c_vars,pcfg)
    num_preterminals = 0
    num_guesses = 0
    p_queue_start_time = 0
    p_queue_stop_time = 0
    guess_start_time = 0
    guess_stop_time = 0
    total_time_start = time.perf_counter()
    while ret_value == g_vars.ret_values['STATUS_OK']:
#       print(str(g_vars.q_item.probability) + " : " + str(g_vars.q_item.parse_tree))
        num_preterminals = num_preterminals +1
        guess_start_time = time.perf_counter()
        num_guesses = num_guesses + len(pcfg.list_terminals(g_vars.q_item.parse_tree))
        
        guess_stop_time = time.perf_counter() - guess_start_time
        if num_preterminals % 10000 == 0:
            print ("PQueue:" + str(len(p_queue.p_queue)))
#            print ("Total number of Pre Terminals: " + str (num_preterminals))
#            print ("PQueueTime " + str(p_queue_stop_time))
#            print ("Guesses:" + str(num_guesses))
#            print ("GuessTime " + str(guess_stop_time))
#            print ("Average num of guesses per preterm: " + str(num_guesses // num_preterminals))
#            print ("Total Time " + str(time.perf_counter() - total_time_start))
#            print ("Number of guesses a second: " + str(num_guesses // (time.perf_counter() - total_time_start)))
            print ("Current probability: " + str(p_queue.max_probability))
        for guess in pcfg.list_terminals(g_vars.q_item.parse_tree):
            print(guess)
        p_queue_start_time = time.perf_counter()  
        ret_value = p_queue.next_function(g_vars,c_vars,pcfg)
        p_queue_stop_time = time.perf_counter() - p_queue_start_time
    #ret_value = test_queue(g_vars,c_vars,pcfg)
    #ret_value = test_grammar(g_vars,c_vars,pcfg)
   
    
    return g_vars.ret_values['STATUS_OK']
    

if __name__ == "__main__":
    main()