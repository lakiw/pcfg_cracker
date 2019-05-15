#!/usr/bin/env python3


#############################################################################
# This file contains the functionality to parse raw passwords for PCFGs
#
# The PCFGPasswordParser class is designed to be instantiated once and then
# process one password at at time that is sent to it
#
#############################################################################


# Global imports
import sys
import configparser
import os
import copy
import traceback

# Local imports
from .grammar_io import load_grammar
from .omen.optimizer import Optimizer
from .omen.input_file_io import load_rules
from .omen.markov_cracker import MarkovCracker


## Responsible for holding the PCFG Grammar
#
class PcfgGrammar:

    ## Initializes the class and all the data structures
    #
    # Input:
    #
    #    rule_name: The name of the ruleset to load the grammar from
    #
    #    version: The version of the PCFG Guesser. Used to determine if
    #             this program can load a ruleset that may be generated from
    #             an older version of the trainer
    #
    def __init__(self, rule_name, base_directory, version, debug = False):
        
        ## Debugging and Status Information
        #
        self.encoding = None
        self.rulename = rule_name
        self.debug = debug
        
        ## If an exception occurs, pass it back up the stack
        self.grammar, self.base, ruleset_info = load_grammar(rule_name, base_directory, version)
        
        ## Initailize and load the OMEN grammar and settings
        #
        # Dictionary that will contain the OMEN Grammar
        self.omen_grammar = {}
     
        omen_directory = os.path.join(base_directory, "Omen")
        
        # Load the OMEN rules from disk
        if not load_rules(omen_directory, self.omen_grammar):
            print("Error reading the OMEN ruleset", file=sys.stderr)
            raise Exception
       
        # Initialize the OMEN TMTO optimizer
        self.omen_optimizer = Optimizer(max_length = 4)
        
        
    ## Generates Guesses From a Pase Tree
    #
    # This is mostly a wrapper to hide the recursive calls from the calling
    # function
    #
    # Input Values:
    #   pt: The parse tree, which is a list of tuples
    #
    # Return Value:
    #   num_guesses: The number of guesses generated
    #
    def create_guesses(self, pt):
        return self._recursive_guesses('',pt)
        
        
    ## Initalizes and returns a set of parse trees from the base structures
    #
    # This is used to initailize a cracking session by returning a set of
    # the most probable parse trees for each base structure    
    #
    # Note, these will *NOT* be in true probability order. That will be up
    # to whatever makes use of this list to sort them as desired
    #
    # Return Values
    #
    # pt_list: A list of the parse tree items. This is a dictionary with
    #          the following keys:
    #          'prob': The probability of the parse tree (float)
    #          'pt': The parse tree, which is a list of tuples indexed into the
    #                grammar
    #          'base_prob': The probability of the base structure
    # 
    def initalize_base_structures(self):
        pt_list = []
        
        # Loop through all of the base structures to initalize them
        for item in self.base:
            pt_item = {
                'base_prob': item['prob'],
                'pt': []
            }
            
            # Create the pt from the base structure
            for replacement in item['replacements']:
                pt_item['pt'].append((replacement,0))
                
            # Calculate the probability
            pt_item['prob'] = self._find_prob(pt_item['pt'], pt_item['base_prob'])
            
            pt_list.append(pt_item)
            
        return pt_list
        
        
    ## Actually generates Guesses from a Parse Tree
    #
    # Recursivly generates guesses from a parse tree
    #
    def _recursive_guesses(self, cur_guess, pt):
        
        num_guesses = 0
        
        # Get the transistion category for the current rule, aka 'A' for alpha
        category = pt[0][0][0]
        
        # Get the type for the transistion, Aka A10 for 10 letter long alpha
        type = pt[0][0]
        
        # Get he index into the transition, aka the 2nd most probable A10
        index = pt[0][1]
        
        # If it is a Markov guess
        if category == 'M':
            # Get the level
            level = int(self.grammar[type][index]['values'][0])
            
            mc = MarkovCracker(self.omen_grammar, level, self.omen_optimizer)
            
            guess = mc.next_guess()
            while guess != None:
                num_guesses += 1
                
                # Output the results
                self.print_guess(cur_guess + guess)

                guess = mc.next_guess()

        # If it is a capitalization mask
        elif category == 'C':
            
            mask_len = len(self.grammar[type][index]['values'][0])
            
            # Split off the part of the word we need to modify with the mask
            start_word = [cur_guess[:- mask_len]]
            end_word = cur_guess[- mask_len:]
            
            for mask in self.grammar[type][index]['values']:

                # Apply the capitalization mask
                new_end = []
                index = 0
                for item in mask:
                    if item == 'L':
                        new_end.append(end_word[index])
                    else:
                        new_end.append(end_word[index].upper())
                    index += 1
                    
                # Recombine the capitalization mask with what came before
                new_guess = ''.join(start_word + new_end)
                
                # Figure out if the guess is ready to be printed out or if
                # there is more to do
                if len(pt) == 1:
                    num_guesses += 1
                    self.print_guess(new_guess)

                else:
                    num_guesses += self._recursive_guesses(new_guess, pt[1:]) 
            
        # If it is any striaght replacement, (digits, letters, etc)    
        else:
            for item in self.grammar[type][index]['values']:
                new_guess = cur_guess + item
                
                # Figure out if the guess is ready to be printed out or if
                # there is more to do
                if len(pt) == 1:
                    num_guesses += 1
                    self.print_guess(new_guess)

                else:
                    num_guesses += self._recursive_guesses(new_guess, pt[1:])                             
                
        return num_guesses
        

    ## General code to print out a guess to stdout
    #
    # Need to have error handling and want to centerlize all the calls to this so I don't\t
    # accidently forget some printout somewhere else
    #
    def print_guess(self, guess):
        if self.debug == False:
            try:
                print(guess)
            ##--While I could silently replace/ignore the Unicode character for now I want to know if this is happening
            except UnicodeEncodeError as msg:
                #print("UNICODE_ERROR: " + str(msg),file=sys.stderr) 
                pass                            
            except:
                print('',file=sys.stderr)
                print("Consumer, (probably the password cracker), stopped accepting input.",file=sys.stderr)
                print("Halting guess generation and exiting",file=sys.stderr)
                raise OSError
    
    
    ## Finds the children for a given parse tree
    #
    # Uses the Deadbeat Dad algorithm to determine if a child node should
    # be taken care of by the current parent node
    #
    # Input Variables
    #    pt_item: A parse tree item. It is a dictionary with the following keys
    #        'prob': The probability of the parse tree (float)
    #        'pt': The parse tree, which is a list of tuples indexed into the
    #              grammar
    #        'base_prob': The probability of the base structure
    #
    # Return Values:
    #    children_list: A list of all the children, formated as pt_item(s)
    #
    def find_children(self, pt_item):
        
        parent_prob = pt_item['prob']
        parent_pt = pt_item['pt']
        
        # The return values
        children_list = []
        
        # Go through all the possible children
        for pos, item in enumerate(parent_pt):
            
            parent_type = item[0]
            parent_index = item[1]
                             
            # If true, there are no children at this level
            if len(self.grammar[parent_type]) == parent_index +1:
                continue
            
            # Create the child node
            child = copy.copy(parent_pt)
            child[pos] = (child[pos][0], child[pos][1]+1)
            
            # Check to see if the child belongs to this parent
            if self._are_you_my_child(child, pt_item['base_prob'], pos, parent_prob):
            
                # Testing, just add the child back
                child_item = {
                    'pt':child,
                    'base_prob': pt_item['base_prob'],
                    'prob': self._find_prob(child, pt_item['base_prob'])
                }
                children_list.append(child_item)
            
        return children_list
            
    
    ## Given a child and a potential parent, returns if that child is the
    #  responsibility of the parent
    #
    # Uses the Deadbeat Dad algorithm to determine if a child node should
    # be taken care of by the current parent node
    #
    # Input Variables
    #    child: The child's parse tree, which is a list of tuples indexed 
    #           into the grammar
    #
    #    base_prob: The probaiblity of the base structure
    #
    #    parent_pos: The edit position of the calling parent
    #
    #    parent_prob: The probabilty of the calling parent
    #
    # Return Values:
    #    True: The calling parent should take care of this child
    #
    #    False: The calling parent is not responsible of this child
    #
    def _are_you_my_child(self, child, base_prob, parent_pos, parent_prob):
    
        ## Basic description of Deadbeat Dad algorithm
        #
        # 1) Create all potential parents, (besides calling parents), along
        #    with calculating their probabilities
        #
        # 2a) If any potential parent's probabilty is less than calling parent's
        #    probability, return False. Those low probability parents will
        #    be called later and then generate the child. This is true because
        #    children are always less probable than parents
        #
        # 2b) In the case of a tie between parents probability, the parent with
        #     the lowest 'parent_pos' will be responsible for child
        #
        
        # Go through all the possible parents
        for pos, item in enumerate(child):
            
            # No sense calculating the calling parent
            if pos == parent_pos:
                continue
                
            # Skip if there is no parent at this position
            if item[1] == 0:
                continue
            
            # Create the new parent
            new_parent = copy.copy(child)
            new_parent[pos] = (new_parent[pos][0], new_parent[pos][1]-1)
            
            # Calculate new parent's probability
            new_parent_prob = self._find_prob(new_parent, base_prob)
            
            # Check if the new parent should take care of the child
            if new_parent_prob < parent_prob:
                return False
            elif new_parent_prob == parent_prob:
                if pos < parent_pos:
                    return False
    
        return True

    
    ## Finds the probability of a parse tree
    #
    # Input Variables
    #    pt: The parse tree, which is a list of tuples indexed into the
    #        grammar
    #
    #    base_prob: The probability of the base structure
    #
    # Return Values:
    #    prob: The probability of the parse tree according to the grammar
    #
    def _find_prob(self, pt, base_prob):    
        
        # Initialize the final probabilty as that of the base_probability
        # Will update this later with all of the individual transistion probs
        prob = base_prob
    
        for item in pt:
            type = item[0]
            index = item[1]
            prob *= self.grammar[type][index]['prob']
            
        return prob    
        