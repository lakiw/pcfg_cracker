#!/usr/bin/env python3


"""
This file contains the functionality to parse raw passwords for PCFGs

The PCFGPasswordParser class is designed to be instantiated once and then
process one password at at time that is sent to it

"""


# Global imports
import sys
import os
import copy
import codecs
import random

# Local imports
from .grammar_io import load_grammar, load_omen_keyspace
from .omen.optimizer import Optimizer
from .omen.input_file_io import load_rules
from .omen.markov_cracker import MarkovCracker


class PcfgGrammar:
    """
    Responsible for holding all the information about the PCFG Grammar
    """

    def __init__(self,
        rule_name,
        base_directory,
        version,
        save_file = None,
        skip_brute = False,
        skip_case = False,
        debug = False,
        base_structure_folder = "Grammar"):
        """
        Initializes the class and all the data structures

        Inputs:
            rule_name: The name of the ruleset to load the grammar from

            base_directory: The directory to load the rule from

            version: The version of the PCFG Guesser. Used to determine if
                    this program can load a ruleset that may be generated from
                    an older version of the trainer

            save_file: The file to save results to

            skip_brute: If brute force values should be saved or not

            skip_case: If case mangling should be saved. If False, all alpha characters
                    are saved as lowercase

            debug: A boolean that specifies if a debugging run is occuring or not

            base_structure_folder: Used to specify which base structure folder to use.
                    This is useful for future options where there may be multiple
                    different base structure folders for a given ruleset to target
                    specific password complexity requirements

        Returns:
            PcfgGrammar
        """

        # Debugging and Status Information
        self.rulename = rule_name
        self.debug = debug
        self.ruleset_info = None

        # If an exception occurs below, don't catch it here, pass it back up the stack
        self.grammar, self.base, self.ruleset_info = load_grammar(
            rule_name,
            base_directory,
            version,
            skip_brute,
            skip_case,
            base_structure_folder
            )

        self.encoding = self.ruleset_info['encoding']

        # Initailize and load the OMEN grammar and settings

        # Dictionary that will contain the OMEN Grammar
        self.omen_grammar = {}

        omen_directory = os.path.join(base_directory, "Omen")

        # Load the OMEN rules from disk
        if not load_rules(omen_directory, self.omen_grammar):
            print("Error reading the OMEN ruleset", file=sys.stderr)
            raise Exception

        # Initialize the OMEN TMTO optimizer
        self.omen_optimizer = Optimizer(max_length = 4)

        self.omen_keyspace = load_omen_keyspace(base_directory)

        # Used to track status during an OMEN guessing session
        self.omen_guess_num = 0

        # Used to tell long running guess generators, (like OMEN), that
        # the user wants to exit the program
        self.should_exit = False

        # If this exited in the middle of an OMEN guessing session
        self.omen_exit = False

        # Base filename for save files
        self.save_file = save_file

        # Filename to save guesses to if not outputting to stdout
        self.output_filename = None
        
        # The file handler for saving guesses to a file if desired
        self.output_file = None


    def create_guesses(self, pt, is_honeyword=False, limit=None):
        """
        Generates Guesses From a Parse Tree

        This is mostly a wrapper to hide the recursive calls from the calling
        function. Will print guesses to stdout.

        Inputs:
            pt: The parse tree, which is a list of tuples

            is_honeyword: (bool) If this is a honeyword generation. If true
            only one password guess will be generated.

            limit: (None/Int) If it is not None, limit is a number that decrements
            which specifies how many guesses remain to be generated. Ignored if None

        Returns:
            num_guesses: The number of guesses generated
        """

        if not is_honeyword:
            return self._recursive_guesses('', pt, limit)
        
        else:
            return self._honeyword_recursive_guess('', pt, limit)


    def initalize_base_structures(self):
        """
        Initalizes and returns a set of parse trees from the base structures

        This is used to initailize a cracking session by returning a set of
        the most probable parse trees for each base structure

        Note, these will *NOT* be in true probability order. That will be up
        to whatever makes use of this list to sort them as desired

        Inputs:
            None

        Returns:
            pt_list: A list of the parse tree items. This is a dictionary with
            the following keys:

            .. code-block:: python
            
                {
                    'prob': The probability of the parse tree (float),
                    'pt': The parse tree, which is a list of tuples indexed into the grammar,
                    'base_prob': The probability of the base structure,
                }

        """

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


    def _recursive_guesses(self, cur_guess, pt, limit=None):
        """
        Recursivly generates guesses from a parse tree
        Will print out guesses to stdout

        Inputs:
            cur_guess: The current guess being generated

            pt: The parse tree, which is a list of tuples. Will recursivly work though the pt to
            fill out parts to cur_guess.

            limit: (None/Int) If it is not None, limit is a number that decrements
            which specifies how many guesses remain to be generated. Ignored if None

        Returns:
            num_guesses: The number of guesses generated
        """

        num_guesses = 0

        # Get the transistion category for the current rule, aka 'A' for alpha
        category = pt[0][0][0]

        # Get the type for the transistion, Aka A10 for 10 letter long alpha
        pt_type = pt[0][0]

        # Get he index into the transition, aka the 2nd most probable A10
        index = pt[0][1]

        # If it is a Markov guess
        if category == 'M':
            # Get the level
            level = int(self.grammar[pt_type][index]['values'][0])

            markov_cracker = MarkovCracker(self.omen_grammar, level, self.omen_optimizer)

            # Initalize counter used for status reports and save files
            self.omen_guess_num = 0

            return self.omen_generate_guesses(markov_cracker, limit)

        # If it is a capitalization mask
        elif category == 'C':

            mask_len = len(self.grammar[pt_type][index]['values'][0])

            # Split off the part of the word we need to modify with the mask
            start_word = [cur_guess[:- mask_len]]
            end_word = cur_guess[- mask_len:]

            for mask in self.grammar[pt_type][index]['values']:

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

                    # Check the limit
                    if limit:
                        limit = limit - 1
                        if limit <= 0:
                            return num_guesses

                else:
                    num_guesses += self._recursive_guesses(new_guess, pt[1:], limit)
                    if limit:
                        limit = limit - num_guesses
                        if limit <= 0:
                            return num_guesses

        # If it is any striaght replacement, (digits, letters, etc)
        else:
            for item in self.grammar[pt_type][index]['values']:
                new_guess = cur_guess + item

                # Figure out if the guess is ready to be printed out or if
                # there is more to do
                if len(pt) == 1:
                    num_guesses += 1
                    self.print_guess(new_guess)

                    # Check the limit
                    if limit:
                        limit = limit - 1
                        if limit == 0:
                            return num_guesses

                else:
                    num_guesses += self._recursive_guesses(new_guess, pt[1:], limit)
                    
                    if limit:
                        limit = limit - num_guesses
                        if limit <= 0:
                            return num_guesses

        return num_guesses


    def _honeyword_recursive_guess(self, cur_guess, pt, limit = None):
        """
        Recursivly generates a single random guess from a parse tree
        from all of the possible guesses it could generate

        Will print out guesses to stdout

        Inputs:
            cur_guess: The current guess being generated

            pt: The parse tree, which is a list of tuples. Will recursivly work though the pt to
            fill out parts to cur_guess.

            limit: (None/Int) If it is not None, limit is a number that decrements
            which specifies how many guesses remain to be generated. Ignored if None

        Returns:
            num_guesses: The number of guesses generated. Will be 0 or 1.
        """

        num_guesses = 0

        # Get the transistion category for the current rule, aka 'A' for alpha
        category = pt[0][0][0]

        # Get the type for the transistion, Aka A10 for 10 letter long alpha
        pt_type = pt[0][0]

        # Get he index into the transition, aka the 2nd most probable A10
        index = pt[0][1]

        # If it is a Markov guess
        if category == 'M':
            # Not currently supported for honeywords
            return 0

        # If it is a capitalization mask
        elif category == 'C':

            mask_len = len(self.grammar[pt_type][index]['values'][0])

            # Split off the part of the word we need to modify with the mask
            start_word = [cur_guess[:- mask_len]]
            end_word = cur_guess[- mask_len:]

            mask = random.choice(self.grammar[pt_type][index]['values'])

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
                
                # Check the limit
                if limit:
                    limit = limit - 1
                    if limit <= 0:
                        return num_guesses

            else:
                num_guesses += self._honeyword_recursive_guess(new_guess, pt[1:], limit)
                
                if limit:
                    limit = limit - num_guesses
                    if limit <= 0:
                        return num_guesses

        # If it is any striaght replacement, (digits, letters, etc)
        else:
            item = random.choice(self.grammar[pt_type][index]['values'])
            new_guess = cur_guess + item

            # Figure out if the guess is ready to be printed out or if
            # there is more to do
            if len(pt) == 1:
                num_guesses += 1
                self.print_guess(new_guess)
                # Check the limit
                if limit:
                    limit = limit - 1
                    if limit <= 0:
                        return num_guesses

            else:
                num_guesses += self._honeyword_recursive_guess(new_guess, pt[1:], limit)
                if limit:
                    limit = limit - num_guesses
                    if limit <= 0:
                        return num_guesses

        return num_guesses


    def omen_generate_guesses(self, markov_cracker, limit=None):
        """
        Generates OMEN Guesses

        Will print guesses out to stdout

        Making this its own functions so that the load/restore and generate guesses
        from a normal session options can re-use this code

        limit: (None/Int) If it is not None, limit is a number that decrements
        which specifies how many guesses remain to be generated. Ignored if None

        Inputs:
            markov_cracker: An OMEN MarkovCracker instance

        Returns:
            num_guesses: The number of guesses generated for this OMEN session
        """

        num_guesses = 0
        guess = markov_cracker.next_guess()
        while guess is not None:
            num_guesses += 1

            # Output the results
            self.print_guess(guess)
            # Check the limit
            if limit:
                limit = limit - 1
                if limit <= 0:
                    return num_guesses

            # Update counter used for status reports and save files
            self.omen_guess_num += 1

            # Check to see if the user wanted to exit the program
            if self.should_exit:
                self.omen_exit = True
                print("Saving OMEN guess generation status",file=sys.stderr)

                # Note, need to add the new extension onto omen session
                # files for now
                markov_cracker.save_session(self.save_file[:-4] + ".omn")
                return num_guesses

            # Get next guess
            guess = markov_cracker.next_guess()

        return num_guesses


    def print_guess(self, guess):
        """
        General code to print out a guess to stdout

        If an error occurs will pass back OSError

        Need to have error handling and want to centerlize all the calls to this so I don't
        accidently forget some printout somewhere else

        Inputs:
            guess: The string to print out to stdout

        Returns:
            None
        """

        if not self.debug:
            try:
                print(guess)
            # While I could silently replace/ignore the Unicode character for now I
            # want to provide a good spot to debug if this is happening
            except UnicodeEncodeError:
                pass
            except:
                print('',file=sys.stderr)
                print("The consumer, probably the password cracker, has stopped",file=sys.stderr)
                print("accepting input.",file=sys.stderr)
                print("Halting guess generation and exiting",file=sys.stderr)
                raise OSError


    def find_children(self, pt_item):
        """
        Finds the children for a given parse tree

        Uses the Deadbeat Dad algorithm to determine if a child node should
        be taken care of by the current parent node

        Inputs:
            pt_item: A parse tree item. It is a dictionary with the following keys
                'prob': The probability of the parse tree (float)

                'pt': The parse tree, which is a list of tuples indexed into the
                 grammar

                'base_prob': The probability of the base structure

        Returns:
            children_list: A list of all the children, formated as pt_item(s)
        """

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


    def _are_you_my_child(self, child, base_prob, parent_pos, parent_prob):
        """
        Given a child and a potential parent, returns if that child is the
        responsibility of the parent

        Uses the Deadbeat Dad algorithm to determine if a child node should
        be taken care of by the current parent node

        Inputs:
            child: The child's parse tree, which is a list of tuples indexed
            into the grammar

            base_prob: The probaiblity of the base structure

            parent_pos: The edit position of the calling parent

            parent_prob: The probabilty of the calling parent

        Returns:
            True: The calling parent should take care of this child

            False: The calling parent is not responsible of this child
        """

        # Basic description of Deadbeat Dad algorithm
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


    def _find_prob(self, pt, base_prob):
        """
        Finds the probability of a parse tree

        Inputs:
            pt: The parse tree, which is a list of tuples indexed into the
            grammar

            base_prob: The probability of the base structure

        Returns:
            prob: The probability of the parse tree according to the grammar
        """

        # Initialize the final probabilty as that of the base_probability
        # This will be updated later with all of the individual transistion probs
        prob = base_prob

        for item in pt:
            pt_type = item[0]
            index = item[1]
            prob *= self.grammar[pt_type][index]['prob']

        return prob


    def get_status(self, pt, cur_guess = ''):
        """
        Returns current status for a Parse Tree

        Inputs:
            pt: The parse tree, which is a list of tuples

            cur_guesses: The begining of a guess
            Use default (don't specify) if you are calling it directly

        Returns:
            guess_status: Dictionary with the following keys depending on if
            is is an OMEN parse tree or not

            .. code-block:: python

                -Omen PT: {
                    'pt':[('M',1)],
                    'level':"12",
                    'keyspace':123953343,
                    'guess_num':19533,
                    }

                -Non-Omen:{
                    'pt':[('A3',10),('D2',1)]
                    'first_guess': 'cat12'
                    }
        """

        # Get the transistion category for the current rule, aka 'A' for alpha
        category = pt[0][0][0]

        # Get the type for the transistion, Aka A10 for 10 letter long alpha
        pt_type = pt[0][0]

        # Get he index into the transition, aka the 2nd most probable A10
        index = pt[0][1]

        # If it is a Markov guess
        if category == 'M':
            # Get the level
            level = int(self.grammar[pt_type][index]['values'][0])

            return {
                'pt':pt,
                'level': level,
                'keyspace': self.omen_keyspace[level],
                'guess_num': self.omen_guess_num,
                }

        # If it is a capitalization mask
        elif category == 'C':

            mask_len = len(self.grammar[pt_type][index]['values'][0])

            # Split off the part of the word we need to modify with the mask
            start_word = [cur_guess[:- mask_len]]
            end_word = cur_guess[- mask_len:]

            mask = self.grammar[pt_type][index]['values'][0]

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

        # If it is any striaght replacement, (digits, letters, etc)
        else:
            item = self.grammar[pt_type][index]['values'][0]
            new_guess = cur_guess + item

        # Figure out if the guess is ready to be printed out or if
        # there is more to do
        if len(pt) == 1:
            return {
                'pt':pt,
                'first_guess': new_guess
                }

        else:
            return self.get_status(pt[1:],cur_guess = new_guess)


    def restore_prob_order(self, pt_item, max_prob, min_prob, save_function):
        """
        Walks through the pt_item restoring children using save_function

        This is currently a launch function that initializes and then
        kicks off the recursive restore. I eventually need to come back to this
        and create a non-recursive version of this since it's caused some problems
        when restoring longer sessions from large grammars. The problem is
        it will hit Python's recursion limit and crash. I'm minimizing this by
        increasing Python's recursion limit but that fix does not bring me joy.

        Inputs:
            pt_item: A pt_item to parse

            max_prob: (float): The maximum probability of an item to restore. Items
            with a higher probability will not be restored. This is to avoid
            re-guessing passwords that have already been guessed

            min_prob: (float): The minimum probability of an item to restore. Items
            with a lower probability will not be restored. This is to minimize
            the size of the saved/restored values by not adding items that will
            likely never be guessed

            save_function: The function to call to save valid children

        Returns:
            True: It was successful

            False: An error was encountered
        """
        recursion_depth = 10**6
        try:
            sys.setrecursionlimit(recursion_depth)
            self._recursive_restore_prob_order(pt_item, max_prob, min_prob, save_function)
        except RecursionError:
            print ("Recursion error with restorting the save file",file=sys.stderr)
            print (f"Max recusion depth of {recursion_depth} exceeded",file=sys.stderr)
            print (f"Please open a bug/issue on the project github page since the",file=sys.stderr)
            print (f"programmer obviously made some bad assumptions. That might",file=sys.stderr)
            print (f"give them incentive to program a non-recursive restore...",file=sys.stderr)
            return False

        return True


    def _recursive_restore_prob_order(self, pt_item, max_prob, min_prob, save_function, left_index=0):
        """
        Walks through the pt_item restoring children using save_function

        Note: This works recursivly with the first call being passed the base_item
        which is the most probable pt parsing

        Inputs:
            pt_item: A pt_item to parse

            max_prob: (float): The maximum probability of an item to restore. Items
            with a higher probability will not be restored. This is to avoid
            re-guessing passwords that have already been guessed

            min_prob: (float): The minimum probability of an item to restore. Items
            with a lower probability will not be restored. This is to minimize
            the size of the saved/restored values by not adding items that will
            likely never be guessed

            save_function: The function to call to save valid children

            left_index: The index to find children at. The orig calling function should
            not use this

        Returns:
            None
        """    

        parent_prob = pt_item['prob']
        parent_pt = pt_item['pt']
        parent_len = len(parent_pt)

        # Too low probability, stop this parsing
        if parent_prob < min_prob:
            return

        # If this node might be inserted into the queue
        elif parent_prob <= max_prob:
            # Check to make sure none of this child's parents are in the queue
            if not self.is_parent_around(pt_item, max_prob):
                # Save the node and exit, since we don't need to check its
                # children
                save_function(pt_item)

            return

        # Only find children the left of left_index + left_index itself
        for pos in range(left_index, parent_len):

            item = parent_pt[pos]

            parent_type = item[0]
            parent_index = item[1]

            # If true, there are no children at this level
            if len(self.grammar[parent_type]) == parent_index +1:
                continue

            # Create the child node
            child = copy.copy(parent_pt)
            child[pos] = (child[pos][0], child[pos][1]+1)

            child_item = {
                    'pt':child,
                    'base_prob': pt_item['base_prob'],
                    'prob': self._find_prob(child, pt_item['base_prob'])
                }

            # Call the function again for the child
            self._recursive_restore_prob_order(child_item, max_prob, min_prob, save_function, left_index = pos)


    def is_parent_around(self, pt_item, max_prob):
        """
        Used as part of the Deadbeat Dad algorithm to identify if a child's parent
        node is currently in the pqueue or not. If so, this child does not need
        to be inserted into the pqueue.

        Inputs:
            pt_item: The parse tree of the child

            max_prob: The maximum probabilty of the parse tree. If the parent is still around
            it needs to be of a lower probability than max_prob.

        Returns:
            True: There is a parent node still in the pqueue

            False: There is no parent tree in the pqueue
        """

        child = pt_item['pt']

        for pos, item in enumerate(child):

            # Skip if there is no parent at this position
            if item[1] == 0:
                continue

            # Create the new parent
            new_parent = copy.copy(child)
            new_parent[pos] = (new_parent[pos][0], new_parent[pos][1]-1)

            # Calculate new parent's probability
            new_parent_prob = self._find_prob(new_parent, pt_item['base_prob'])

            # Check if the new parent should take care of the child
            if new_parent_prob < max_prob:
                return True

        return False


    def restore_omen(self, omen_guess_num, pt_item):
        """
        Restores an OMEN guessing session and starts generating OMEN guesses.

        Will continue the guessing session and eventually print guesses out to stdout
        by calling omen_generate_guesses()

        Inputs:
            omen_guess_num: Where it is in the OMEN guess generation for the OMEN level

            pt_item: The parse tree that specifies the OMEN level

        Returns:
            Int: The number of guesses generated


        """

        # Initialize, then restore the markovcracker
        markov_cracker = MarkovCracker(self.omen_grammar, 1, self.omen_optimizer)
        markov_cracker.load_session(self.save_file[:-4]+'.omn', pt_item)

        # Initalize counter used for status reports and save files
        self.omen_guess_num = omen_guess_num

        return self.omen_generate_guesses(markov_cracker)


    def save_to_file(self, filename):
        """
        Sets the PCFG grammar to output guesses to a file vs. stdout

        Note: If filename = None, then will continue to use the standard stdout
        option for guess generation, which is nice when parsing inputs
        from the command line

        Additional Note: Not currently using this in the main pcfg cracker
        but leaving this in for other tool use.

        Inputs:
            filename: The name of the file to save guesses to

        Returns:
            None
        """

        self.output_filename = filename

        # If a file was specified to write the data to, open it for writing
        if self.output_filename:
            self.output_file = codecs.open(
                self.output_filename,
                'w',
                encoding= self.encoding,
            )

            # Overload the print_guess function
            self.print_guess = self.write_guess_to_file


    def write_guess_to_file(self, guess):
        """
        Saves the actual guess to file. Used to overload the normal print_guess to stdout function

        Inputs:
            guess: The password guess to save to file

        Returns:
            None
        """
        self.output_file.write(guess)
        self.output_file.write('\n')


    def shutdown(self):
        """
        Cleanup function when shutting down to ensure that any output files
        are properly closed

        Inputs:
            None

        Returns:
            None

        """
        if self.output_filename:
            self.output_file.close()


    def random_walk(self):
        """
        Performs a weighted random walk of the grammar and returns a pt_item

        Inputs:
            None

        Returns:
            pt_item: The parse tree that specifies the item found in the walk

        """

        # Initialize the pt_item
        pt_item = {
            'base_prob': 1.0,
            'pt': []
        }

        # First find the base structure
        prob_target = random.random()
        cur_prob = 0
        for item in self.base:
            cur_prob += item['prob']

            # Found the matching base structure to select
            if cur_prob >= prob_target:
                for replacement in item['replacements']:
                    pt_item['pt'].append((replacement,0))

                break

        # Now go through each item and perform a random walk for it as well
        for pointer, item in enumerate(pt_item['pt']):
            prob_target = random.random()
            cur_prob = 0
            pt_type = item[0]
            max_index = len(self.grammar[pt_type])
            
            for index in range (0, max_index):
                cur_prob += self.grammar[pt_type][index]['prob'] * len(self.grammar[pt_type][index]['values'])
                if cur_prob >= prob_target:
                    pt_item['pt'][pointer] = (item[0], index)
                    break
        
        # Calculate the probability
        pt_item['prob'] = self._find_prob(pt_item['pt'], pt_item['base_prob'])

        return pt_item