#!/usr/bin/env python3

########################################################################################
#
# Name: PCFG_Cracker core grammar code
# Description: Holds the top level code for manipulating the pcfg.
#              For example the deadbeat dad "next" function, memory management, etc
#
#########################################################################################

import sys   #--Used for printing to stderr
import random  #--Used for generating honeywords
import itertools #--Used for walking a pcfg

from .markov_cracker import MarkovCracker, MarkovIndex
from .guess_generation import GuessGeneration


##########################################################################################
# Main class of this program as it represents the central grammar of the pcfg cracker
# I'm trying to keep the actual grammar as generic as possible.
# You can see a sample grammar in sample_grammar.py, but I'm really trying to keep this
# generic enough to support things like recursion.
#
# Each transition is represented by a python dictionary of the form:
#   'name':'START' //Human readable name. Used for status messages and debugging
#   'replacements': [List of all the replacements] //the transitions that are allowed for this pre-terminal
#
# Each replacement is represented by a python dictionary and a single non-termial can mix and
# match what types of replacements it supports. That being said, the logic on how to actually fill
# out certain replacements may require certain chaining. Aka as it is currently set up, a capitalization
# replacement needs to occur after a dictionary word replacement
# Here are some example fields for a replacement
#   'is_terminal':False //Required. I guess I don't need to use this field if I structured some things differently but it says if there are any future transitions or not
#   'pos':[5,3]  //Required for non-terminals. Acts like pointers into the grammar for what future replacements should be applied to this section.
#                //You can have multiple replacements for example A->AB or A->BC
#   'prob':0.00021 //Required for non-terminals. The probability this transition occurs at. Please note the probability is associated with the transition itself AND the number of terminals
#                  //For example, to save space multiple terminals that have the same probability can be lumped together, but if they each have the same probability the probability here reflects that
#                  //---EXAMPLE, let's say the training found that D2-> 11, 15, 83, all with a probability of 0.2. Then the probability here will be 0.2
#                  //---EXAMPLE#2, let's say that there is a L3 transition that was discovered in training at 0.8 probability. At runtime it is pointed into an input dictionary containing 10 words.
#                  //---------     that probabilty then should be 0.8/10 = 0.08.
#   'values ':["pas","cat","dog","hat"]  //dictionary of pre-terminals that should be applied for this transition. 
#    or
#   'values':['2','3','4']  //A listing of terminals to apply. Since they are terminals there are no futher transitions
#
#   Note, there are also functions that deal with the nitty gritty about how to actually perform the transitions. Eventually I'd like to move them to a plug-in archetecture, but currently
#   they are hardcoded
#   'function':'Shadow'  //Used for pre-terminals like dictionary words where you want to send the current list of words to the next transition so it can do things like apply capitalization rules
#   'function':'Copy'    //Used for terminals to do a straight swap of the contents. like have a D->'1'
#   'function':'Capitalization'  //Used to capitalize words passed in by the previous 'shadow' function
#   'function':'Transparent'  //There is no list of words associated with this transition. Instead you are just pushing new transitions into the stack. Aka S->AB
#   'function':'Markov'  //Used to bruteforce strings. Currently using the --JtR Markov mode
#     ----'values':['1:11']  ///The range at which to create Markov guesses for
#
#    Considering how I'm still designing/writing this code, the above is almost certainly going to change
#
##########################################################################################
class PcfgClass:
    ########################################################
    # Initialize the class, not really doing anything here
    ########################################################
    def __init__(self, grammar=[], markov_cracker = None):
        ###---The actual grammar. It'll be loaded up later
        self.grammar = grammar
        self.markov_cracker = markov_cracker
    
    
    ##############################################################################
    # Returns an index into the starting postion for this grammar
    # It assumes the start index is listed as type "START"
    # Returns -1 if there is an error
    ##############################################################################
    def start_index(self):
        ##--sanity check--##
        if len(self.grammar)==0:
            return -1
            
        ##--quick shortcut--##
        if self.grammar[-1]['type'] == 'START':
            return len(self.grammar) - 1
        ##--Gotta go the long way through this--##
        else:
            for index in range(0,len(self.grammar)):
                if self.grammar[-1]['type'] == 'START':
                    return index
                    
        ##--Couldn't find it, return an error
        return -1
        
        
    ##############################################################################
    # Top level function used to return all the terminals / password guesses
    # associated with the pre_terminal passed it
    # Returns the number of guesses generated, and the [first guess, last guess]
    # The return values are for performance modeling and status reports to the user
    ##############################################################################
    def list_terminals(self,pre_terminal, print_output=True):
              
        ##--The total number of password guesses
        num_guesses = 0
        
        guess_generation = GuessGeneration(self.grammar, self.markov_cracker, pre_terminal)
        
        guess = guess_generation.get_first_guess()
        
        ##--If there are no guesses to generate--##
        ##--This *shouldn't happen unless the grammar is weird
        ##  but grammars can be weird sometimes
        if guess == None:
            return 0, []
        
        ##--Save the first guess for status outputs
        first_and_last_guess = [guess, guess]
               
        ##--Now generate all of the other guesses
        while guess != None:
            ##--Moving the printing of the guesses into this function--##
            ##--  I'm not entirely happy putting this in the core grammar but passing them
            ##--  back as a list doesn't work for pre_terminals that generate millions of guesses
            ##--  This current structure of generating the terminal list and then printing guesses is a transition
            ##--  change until I can code up a "next" function for all the guesses and get rid of the full "list_terminals" function completly
            self.print_guess(guess, print_output)
            
            ##--Save the last guess for status outputs
            first_and_last_guess[-1] = guess
            
            ##--Increment the number of guesses generated
            num_guesses += 1
            
            guess = guess_generation.get_next_guess()
        
        return num_guesses, first_and_last_guess
       

    ###############################################################################################
    # General code to print out a guess to stdout
    # Need to have error handling and want to centerlize all the calls to this so I don't\t
    # accidently forget some printout somewhere else
    ###############################################################################################
    def print_guess(self, guess, print_output = True):
        if print_output == True:
            try:
                print(guess)
            ##--While I could silently replace/ignore the Unicode character for now I want to know if this is happening
            except UnicodeEncodeError as msg:
                #print("UNICODE_ERROR: " + str(msg),file=sys.stderr) 
                pass                            
            except:
                print("Consumer, (probably the password cracker), stopped accepting input.",file=sys.stderr)
                print("Halting guess generation and exiting",file=sys.stderr)
                raise
     
    ##############################################################################################
    # Used to find the probability of a parse tree in the graph
    ##############################################################################################
    def find_probability(self,pt):
        ##--Start at 100%
        current_prob = self.grammar[pt[0]]['replacements'][pt[1]]['prob']
        if len(pt[2]) != 0:
            for x in range(0,len(pt[2])):
                child_prob = self.find_probability(pt[2][x])
                current_prob =current_prob * child_prob
        return current_prob
        
        
    ###############################################################################################
    # Used to find if a node is ready to be printed out or not
    ###############################################################################################
    def find_is_terminal(self,pt):
        if len(pt[2])==0:
            if self.grammar[pt[0]]['replacements'][pt[1]]['is_terminal'] == False:
                return False
        else:
            for x in range(0,len(pt[2])):
                if self.find_is_terminal(pt[2][x]) == False:
                    return False
        return True
   
   
    ###################################################################
    # Copies a parse tree
    # Meant to be a faster replacement than the generic copy.deepcopy()
    # Only works on nodes of the form [index_in_grammar, index_in_node, [[pt1],[pt2],...]]
    #                                 [index_in_grammar, index_in_node, []]
    ###################################################################
    def copy_node(self,pt):
        retnode = []
        ##--Sanity check to make sure things don't go off the rails
        if len(pt) != 3:
            print ("Error copying parse tree", file=sys.stderr)
            print(pt, file=sys.stderr)
            return None
        
        ##--copying the first two items is easy
        retnode.append(pt[0])
        retnode.append(pt[1])
        ##--If there is no additional replacements
        if len(pt[2]) == 0:
            retnode.append([])
        ##--If there are additional replacements, loop through them
        ##--and add them recursivly
        else:
            item_node = []
            for item in pt[2]:  
                item_node.append(self.copy_node(item))
            retnode.append(item_node)
        return retnode
        

    ################################################################################################################################################
    # Used to return all the children according the the deadbeat dad "next" algorithm
    # Moving this funcitonality from the priority queue to the core grammar to achive some speed ups and reduce copy instructions
    #
    # The deadbead dad "next" algorithm is described in http://diginole.lib.fsu.edu/cgi/viewcontent.cgi?article=5135
    # In a nutshell, imagine the parse tree as a graph with the 'S' node at top
    # The original "next" function inserted every child parse through it by incrementing the counter by one to the left
    # so the node (1,1,1) would have the children (2,1,1), (1,2,1), and (1,1,2).
    # The child (1,2,1) would only have the children (1,3,1) and (1,2,2) though.
    # This was to prevent any duplicate entries being pushing into the queue
    # The problem was this was *very* memory intensive
    #
    # The deadbeat dad algorithm instead looks at all the potential parents of *every* child node it could create
    # If any of those parents have lower probability than the current node, it "abandons" that child for the other parent to take care of it
    # Only the parent with the lowest probability inserts the child into the queue. That is because that parent knows there are no other parents
    # that will appear later. I know the name is unfortunate, but it really sums up the approach.
    # Basically we're trading computation time for memory. Keeping the queue small though saves computation time too though so
    # in longer runs this approach should be a clear winner compared to the original next function
    # In the case of a tie where two parents have the same probability, the "leftmost" parent on the parse tree is chosen.
    ################################################################################################################################################
    def deadbeat_dad(self,pt=[]):
        
        ##-- The list of all children to return
        my_children_list = []
        ret_value = self.dd_find_children(pt,pt, my_children_list)
        return my_children_list
     
    
    ###################################################################################################################################################
    # Recursivly find all the children for a given parent using the deadbeat dad algorithm
    # --cur_node is the part of the parent we are currently looking at/modifying to find children
    # --parent is the original parent 
    # --parent_prob is the probability of the parent
    # --my_children_list is a list of all the children for this parent
    ###################################################################################################################################################    
    def dd_find_children(self, cur_node, this_parent, my_children_list):
        
        #########################################################################################################
        # First check to see if we can increment the current node
        # --Only increment and expand if the transition options are blank, aka (x,y,[]) vs (x,y,[some values])
        # --So (1,2,[]) => (1,3,[])
        # --But if it is (1,2,[[5,0,[]]]) do not increment it
        #
        # After that we need to also create children for the expastion
        # --So (1,2,[]) => (1,2,[[5,0,[]]])
        #########################################################################################################
        if len(cur_node[2])==0:
            numReplacements = len(self.grammar[cur_node[0]]['replacements'])
            #Takes care of the incrementing if there are children for the current node. Aka(1,2,[]) => (1,3,[])
            if numReplacements > (cur_node[1]+1):
                ##--Make this a child node
                cur_node[1] = cur_node[1] + 1   
                ##--An id to identify the calling node as the parent                
                cur_node.append(True) 
                if self.dd_is_my_parent(this_parent, is_expansion=False):
                    ##--Remove the id  
                    del cur_node[3]
                    my_children_list.append(self.copy_node(this_parent))
                else:
                    ##--Remove the id  
                    del cur_node[3]
                ##--Replace the parent's value    
                cur_node[1] = cur_node[1] - 1

                
            #Now take care of the expansion. Aka (1,2,[]) => (1,2,[[5,0,[]]])
            if self.grammar[cur_node[0]]['replacements'][0]['is_terminal'] != True:
                #--First fill out the expansion for the new child
                new_expansion = []
                for x in self.grammar[cur_node[0]]['replacements'][cur_node[1]]['pos']:
                    new_expansion.append([x,0,[]])
                
                ##--Make this a child node
                cur_node[2] = new_expansion
                ##--An id to identify the calling node as the parent                
                cur_node.append(True) 
                
                if self.dd_is_my_parent(this_parent, is_expansion=True):
                    ##--Remove the id  
                    del cur_node[3]
                    my_children_list.append(self.copy_node(this_parent))
                else:
                    ##--Remove the id  
                    del cur_node[3]
                    
                ##--Replace the parent's value 
                cur_node[2] = []
                
                
        ###-----Next check to see if there are any nodes to the right that need to be checked
        ###-----This happens if the node is a pre-terminal that has already been expanded
        ###-----Ex: [5,2,[[1,2,[]],[3,1,[]]]] => [5,2,[[1,3,[]],[3,1,[]]]] + [5,2,[[1,2,[]],[3,2,[]]]] + [5,2,[[1,2,[....]],[3,1,[]]]] + [5,2,[[1,2,[]],[3,1,[....]]]]
        else:    
            for x in range(0,len(cur_node[2])):
                #Doing it recursively!
                self.dd_find_children(cur_node[2][x], this_parent, my_children_list)

        return True
    
    
    #################################################################################################
    # Returns true if the calling parent is this child node's lowest probability parent
    # Ties are determined by the parent that occurs leftmost in the expansion
    # --child : The child node to check
    # --is_expansion: If the child created from an expansion from the orig_parent_node. Aka [5,1,[]] -> [5,1,[[2,0,[]],[3,0,[]]]]
    #################################################################################################
    def dd_is_my_parent(self, child, is_expansion = False, index = [0]):
        ##--Didn't want to do this recursivly, so keeping track of which parts of the parse tree haven't been processed in cur_parse_tree
        cur_parse_tree = [child]
        new_index = 0
        ##--Using the min difference between child and parent probability to determine lowest prob parent
        ##--Setting it to 2 so if a difference is 1 from a transition, (shouldn't happend but weirder things occur with floats), the first instance of it is caught
        min_diff = 2
        found_orig_parent = False
        
        ##--Walk through all of the transitions for that child
        while cur_parse_tree:
            
            ##--Get the current transition we are looking at
            cur_node = cur_parse_tree.pop(-1)
            ##--If there are no expansions to the right of this. Aka it looks like [5,1,[])
            if len(cur_node[2])==0:
                #Check to see if there is a parent for this replacement. Aka [5,1,[]] has a parent of [5,0,[]]
                if cur_node[1] != 0:
                    parent_prob_diff = self.grammar[cur_node[0]]['replacements'][cur_node[1] -1]['prob'] - self.grammar[cur_node[0]]['replacements'][cur_node[1]]['prob']

                    if parent_prob_diff < min_diff:
                        ##--If len(cur_node) == 4, then this was the parent node that called this function
                        if (len(cur_node)==4) and (is_expansion == False):
                            found_orig_parent = True
                        elif (found_orig_parent):
                            return False 
                        min_diff = parent_prob_diff
                    ##--The current node is the calling parent but isn't the lowest probability parent    
                    elif (len(cur_node)==4)  and (is_expansion == False):
                        return False
               
            else:
                empty_list_parent = True
                ##---Now go through the expanded parse tree and see if there are any parents from them
                ##---Aka [5,1,[[8,2,[]]]] has a parent of [5,1,[[8,1.[]]]]
                ##---While [5,1,[[8,0,[]]]] parent will be [5,1,[]]
                for x in range(0,len(cur_node[2])):
                    if (cur_node[2][x][1] != 0) or (len(cur_node[2][x][2])!=0):
                        empty_list_parent = False
                        cur_parse_tree.append(cur_node[2][x])

                ###--If there were no parents from the expanded parse tree check the non-expanded version as a possible parent
                if empty_list_parent:
                    new_expansion_prob = 1
                    for index in range(0, len(cur_node[2])):
                        new_expansion_prob *= self.grammar[cur_node[2][index][0]]['replacements'][0]['prob']

                    parent_prob_diff = 1 - new_expansion_prob
                    
                    if parent_prob_diff < min_diff:
                        if (len(cur_node)==4) and (is_expansion == True):
                            found_orig_parent = True
                        elif (found_orig_parent):
                            return False   
                        min_diff = parent_prob_diff
                        
                    elif (len(cur_node)==4) and (is_expansion == True):
                        return False

            new_index = new_index + 1
        return True
    
    
    ####################################################################################################################################
    # Used to see if a parent of the current node is in the queue or not using the deadbeat dad algorithm
    # Slightly less computationally expensive then running the full deadbead dad next function
    ####################################################################################################################################
    def is_parent_in_queue(self,current_parse_tree, cur_node, max_probability):
        ##--Check the curnode's direct parent
        if cur_node[1] != 0:
            cur_node[1] = cur_node[1] - 1
            if self.find_probability(current_parse_tree) < max_probability:
                cur_node[1] = cur_node[1] + 1
                return True
            cur_node[1] = cur_node[1] + 1
    
        ##--Now check the expanded parse tree, aka the [2,0,[]],[3,0,[]] in [1,0,[[2,0,[]],[3,0,[]]]]
        if len(cur_node[2]) != 0:
            ##--if true when this is done, we can test the empty parse tree as a possible parent
            parent_has_no_expanded_pt = True
            for item in cur_node[2]:
                if item[1] != 0 or len(item[2]) != 0:
                    parent_has_no_expanded_pt = False
                    if self.is_parent_in_queue(current_parse_tree, item, max_probability):
                        return True
            ##--Now check the empty list parent
            if parent_has_no_expanded_pt:
                temp_holder = cur_node[2]
                cur_node[2] = []
                if self.find_probability(current_parse_tree) < max_probability:
                    cur_node[2] = temp_holder
                    return True
                cur_node[2] = temp_holder
        
        return False
        
     
    #=================================================================================================================================================#
    # The following functions are to support honeyword operations
    #=================================================================================================================================================#

    ###################################################################################################################################################
    # Performs a random walk of the grammar and returns a parse tree
    # The random walk is weighted by probability. Therefore if there are two choices and one is 90% and the other is 10% the random walk will take
    # the 90% path 90% of the time on average.
    # This is used to help pick parse trees for honeyword generation
    # This function works recursivly, call it with the root node
    # ---AKA: cur_index = self.start_index()
    # -cur_index = current index to start the walk from
    # -Returns the parse tree generated
    ###################################################################################################################################################
    def random_grammar_walk(self, cur_index):
        ##--Find the random number to do the walk with
        random_number = random.random()

        ##--Now find which transition that random number refers to
        cur_transition = -1 #--Initialation value, also denotes an error occured if it is still -1 at the end
        #--Order the probabilities with the first one starting at 0. So if two probs were 90%, and 10%, first would be from 0-90%
        #--Second one would be from 90-100. The upper transition prob is "less than"
        transition_prob = 0
        for i in range(0,len(self.grammar[cur_index]['replacements'])):
            #-The probability of the current transition
            #-Markov is weird since we need to look up the keyspace parameter for it vs looking in the values field
            if self.grammar[cur_index]['replacements'][i]['function'] == 'Markov':
                for item in self.grammar[cur_index]['replacements'][i]['values']:
                    transition_prob += self.grammar[cur_index]['replacements'][i]['prob'] * float(self.markov_cracker.keyspace[item])
            #-Need to calculate it differently if it has values or not, (multiple repalcements packed in the same index)
            elif 'values' in self.grammar[cur_index]['replacements'][i]:
                transition_prob = transition_prob + (self.grammar[cur_index]['replacements'][i]['prob'] * len(self.grammar[cur_index]['replacements'][i]['values']))
            else:
                transition_prob = transition_prob + self.grammar[cur_index]['replacements'][i]['prob']
            ##--This is the transition to take on the random walk
            if random_number < transition_prob:
                cur_transition = i
                break

        ##--Error check to make sure some transition was found--##
        if cur_transition == -1:
            ##--Due to rounding errors this can occur, if it looks like a rounding error, just set it to the first value--##
            if random_number > 0.999:
                cur_transition = 0
            ##--This is outside the bounds I'd expect a rounding error. Print details so I can track it down
            else:
                print("transition prob:" + str(transition_prob),file=sys.stderr)
                print("random number:" + str(random_number),file=sys.stderr)
                print("cur_index:" + str(cur_index),file=sys.stderr)
                print(self.grammar[cur_index]['name'],file=sys.stderr)
                print(self.grammar[cur_index]['replacements'][0],file=sys.stderr)
                print("Error with random walk, the probabilities of all the transitions was less than one in the grammar",file=sys.stderr)
                print("I'd appreciate if you left a bug report on the github page with the above info")
                value = input("Hit Enter")
                return None

        ##--Create the parse tree
        parse_tree = [cur_index,cur_transition,[]]

        ##--Check if it is a terminal
        if self.grammar[cur_index]['replacements'][cur_transition]['is_terminal']:
            ##-return the parse tree
            return parse_tree

        ##-Not a terminal, we need to fill out the replacements
        for i in range(0,len(self.grammar[cur_index]['replacements'][cur_transition]['pos'])):
            child_node = self.random_grammar_walk(self.grammar[cur_index]['replacements'][cur_transition]['pos'][i])
            ##--Error handling to pass errors back up the recursive chain
            if child_node == None:
                return None
            parse_tree[2].append(child_node)

        return parse_tree


    ##############################################################################################################################
    # Generates a random terminal from a parse tree
    # Used for honeyword creation
    ##############################################################################################################################
    def gen_random_terminal(self,pt):
        guess_generation = GuessGeneration(self.grammar, self.markov_cracker, pt)
        guess = guess_generation.get_random_guess()
        return guess


    #=================================================================================================================================================#
    # The following functoins are not currently being used but I'm keeping them around since they may be useful in the future for
    # debugging or development
    #=================================================================================================================================================#

    ####################################################################################################################################################
    # Compares two parse trees and sees if they are the same
    # If they are the same returns True
    # If they are not, returns False
    ####################################################################################################################################################
    def cmp_parse_trees(self, node1, node2):
        if node1[0] != node2[0]:
            return False
        if node1[1] != node2[1]:
            return False
        if len(node1[2]) != len(node2[2]):
            return False
        for index in range(0,len(node1[2])):
            if not self.cmp_parse_trees(node1[2][index],node2[2][index]):
                return False
        return True
     
     
    ##################################################################################################
    # Prints out the parse tree in a human readable fashion
    # Used for debugging but may end up using this for status prints as well
    ##################################################################################################
    def print_parse_tree(self,pt=[]):
        ret_string = ''
        if len(pt[2])==0:
            ret_string += self.grammar[pt[0]]['name']
            ret_string += "[" + str(pt[1] + 1) + " of " + str(len(self.grammar[pt[0]]['replacements'])) + "]"
            if self.grammar[pt[0]]['replacements'][pt[1]]['is_terminal'] == True:
                ret_string += "->terminal"
            else:
                ret_string += "->incomplete"
        else:
            ret_string += self.grammar[pt[0]]['name'] 
            ret_string += "[" + str(pt[1] + 1) + " of " + str(len(self.grammar[pt[0]]['replacements'])) + "]"
            ret_string += "-> ("
            for x in range(0,len(pt[2])):
                ret_string += self.print_parse_tree(pt[2][x])
                if x != len(pt[2])-1:
                    ret_string +=" , "
            ret_string += ")"
        
        return ret_string
        
    
    #################################################################
    # Finds all the children of the parse tree and returns them as a list
    # Not currently being used by anything but it's nice functionality to have
    #################################################################
    def find_children(self,pt):
        #basically we want to increment one step if possible
        #First check for children of the current nodes
        ret_list = []
        ##--Only increment and expand if the transition options are blank, aka (x,y,[]) vs (x,y,[some values])
        if len(pt[2])==0:
            numReplacements = len(self.grammar[pt[0]]['replacements'])
            #Takes care of the incrementing if there are children
            if numReplacements > (pt[1]+1):
                #Return the child
                ret_list.append(self.copy_node(pt))
                ret_list[0][1] = pt[1] + 1
                
            #Now take care of the expansion
            if self.grammar[pt[0]]['replacements'][0]['is_terminal'] != True:
                new_expansion = []
                for x in self.grammar[pt[0]]['replacements'][pt[1]]['pos']:
                    new_expansion.append([x,0,[]])
                ret_list.append(self.copy_node(pt))
                ret_list[-1][2] = new_expansion
        ###-----Next check to see if there are any nodes to the right that need to be checked
        ###-----This happens if the node is a pre-terminal that has already been expanded
        else:    
            for x in range(0,len(pt[2])):
                #Doing it recursively!
                temp_list = self.find_children(pt[2][x])
                #If there were any children, append them to the main list
                for y in temp_list:
                    ret_list.append(self.copy_node(pt))
                    ret_list[-1][2][x] = y
        
        return ret_list

        
    ######################################################################
    # Returns a list of all the parents for a child node / parse-tree
    # Not currently being used by anything but it's nice functionality to 
    ######################################################################    
    def findMyParents(self,pt):
        ret_list = []
        ##--Only expand up if the transition options are blank, aka (x,y,[]) vs (x,y,[some values])
        if len(pt[2])==0:
            #Check the curnode if is at least one other parent
            if pt[1] != 0:     
                ret_list.append(self.copy_node(pt))
                ret_list[0][1] = pt[1] - 1
        else:
            ###---Used to tell if we need to include the non-expanded parse tree as a parent
            parent_size = len(ret_list)
            
            ##---Now go through the expanded parse tree and see if there are any parents from them
            for x in range(0,len(pt[2])):
                #Doing it recursively!
                temp_list = self.findMyParents(pt[2][x])
                #If there were any parents, append them to the main list
                if len(temp_list) != 0:
                    for y in temp_list:
                        tempValue = self.copy_node(pt)
                        tempValue[2][x] = y
                        ret_list.append(tempValue)
            ###--If there were no parents from the expanded parse tree add the non-expanded version as a parent
            if parent_size == len(ret_list):
                ret_list.append(self.copy_node(pt))
                ret_list[0][2] = []
                            
        return ret_list
    
    
#####################################################################
# Debug human readable output of the grammar
# Used for troubleshooting and testing
#####################################################################    
def print_grammar(grammar)   :
    print("Current grammar:",file=sys.stderr)
    print("[",file=sys.stderr)
    for index, item in enumerate(grammar):
        print("("+str(index) +")\t{",file=sys.stderr)
        for key in item.keys():
            if key != 'replacements':
                print("\t\t" + str(key) + ": " + str(item[key])+",",file=sys.stderr)
            else:
                print("\t\treplacements: [",file=sys.stderr) 
                for rep in item['replacements']:
                    print("\t\t\t{",file=sys.stderr)
                    for rep_key in rep.keys():
                        print("\t\t\t\t" + str(rep_key)+": " +str(rep[rep_key]) + ",",file=sys.stderr)
                    print("\t\t\t},",file=sys.stderr)
                
                print("\t\t],",file=sys.stderr)
        print("\t},",file=sys.stderr)
    print("]",file=sys.stderr)
        