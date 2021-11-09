#!/usr/bin/env python3


"""
Brute force generation of password guesses using Markov probabilities to
generate likely guesses first

This uses the OMEN algorithm for generating guesses
"""


import sys
import pickle # Used for saving sessions

# Local imports
from .guess_structure import GuessStructure


class MarkovCracker:
    """
    Contains all the logic for handling Markov guess generation

    Based on OMEN
    """

    def __init__(self, grammar, target_level = 1, optimizer = None):
        """
        Initializes the cracker

        If grammar is none, then the cracker will basically act as a noop

        Inputs:
            grammar: The grammar to use to generate Markov guesses

            target_level: The target OMEN level to generate guesses for

            optimizer: A TMTO option to cache words to make guess generation
            faster over time.

        """

        # Store the ruleset
        self.grammar = grammar

        # Save the optimizer
        self.optimizer = optimizer

        # This is the maximum level an item can be
        self.max_level = grammar['max_level']

        # The length of initial prob items, saving it so we don't constantly
        # have to calculate ngram - 1
        self.length_ip = grammar['ngram'] - 1

        # The first valid IP pointer
        self.start_ip = self._find_first_object(self.grammar['ip'])

        # The first valid length pointer
        self.start_length = self._find_first_object(self.grammar['ln'])

        # This is the target total level we are looking for
        self.target_level = target_level

        # The current length pointer
        self.cur_len = None

        # The current IP pointer
        self.cur_ip = None

        # The current guess structure
        self.cur_guess = None

    def _find_first_object(self, lookup_table):
        """
        Finds the first valid IP or Length object
        Throws exception if there is no valid items

        Inputs:
            lookup_table: A dictionary with keys of the OMEN levels,
            and values of either IP or length

        Returns:
            level: The lowest level at which a value was found
        """
        for level in range(0,self.max_level):
            if len(lookup_table[level]) != 0:
                return level
        print("Either the IP or LN is not valid, please report this bug on the github page", file=sys.stderr)
        raise Exception

    def next_guess(self):
        """
        Generates the "next" guess from this model

        Will return None when no more guesses are left to be created
        After that, it will "reset" so if you call it again it will start
        looping over the same guesses

        Inputs:
            None

        Returns:
            guess: If a guess exists, return it

            None: If a guess does not exist, return None
        """
        # Deal with starting off the Markov chain
        if self.cur_guess is None:

            # Set the starting IP and Length
            self.cur_len = [self.start_length, 0]
            self.cur_ip  = [self.start_ip, 0]

            # Create the guess structure
            self.cur_guess = GuessStructure(
                max_level = self.max_level,
                cp = self.grammar['cp'],
                ip = self.grammar['ip'][self.cur_ip[0]][self.cur_ip[1]],
                cp_length = self.grammar['ln'][self.cur_len[0]][self.cur_len[1]],
                target_level = self.target_level  - self.cur_len[0] - self.cur_ip[0],
                optimizer = self.optimizer,
                )

        # Grab the next guess for the current length and current target
        guess =  self.cur_guess.next_guess()

        # If guess is None, then there isn't a guess for the current length
        # so increase the length if possible
        while guess is None:

            # Attempt to increase the IP for the curent target level + length
            if not self._increase_ip_for_target(working_target = self.target_level - self.cur_len[0]):
                # Attempt to increase the length for the current target level
                if not self._increase_len_for_target():

                    # Done with all password guesses for this level, and can't increase level, exit
                    self.cur_guess = None
                    return None

            guess =  self.cur_guess.next_guess()

        return guess

    def _increase_len_for_target(self):
        """
        Increases the length for the current target level

        FYI: Should always return True if target level > max_level

        Inputs:
            None

        Returns:
            True: If it could increase the length for the target level

            False: If it could not increase the length and still generate a guess for
            the target level

        """
        level = self.cur_len[0]
        index = self.cur_len[1] + 1

        ln = self.grammar['ln']

        # Loop through all the valid levels left
        while level <= self.max_level:

            # Check to see if there is a length option for the current level
            size = len(ln[level])
            if size > index:

                # Save the new length pointer
                self.cur_len = [level, index]

                # Reset the current IP
                self.cur_ip  = [self.start_ip, 0]

                # Reset the current guess
                self.cur_guess = GuessStructure(
                    cp = self.grammar['cp'],
                    max_level = self.max_level,
                    ip = self.grammar['ip'][self.cur_ip[0]][self.cur_ip[1]],
                    cp_length = self.grammar['ln'][self.cur_len[0]][self.cur_len[1]],
                    target_level = self.target_level  - self.cur_len[0] - self.cur_ip[0],
                    optimizer = self.optimizer,
                    )
                return True

            # No valid items at this level, check if we can go up a level
            level += 1
            index = 0
            if level > self.max_level:
                return False
            elif level > self.target_level:
                return False

    def  _increase_ip_for_target(self, working_target = 0):
        """
        Increases the IP for the current target level

        Inputs:
            working_target: The target level, (minus the length value

        Returns:
            True: If it could increase the IP level

            False: If it could not increase the IP level and still generate a guess
            that fell within the target level
        """
        level = self.cur_ip[0]
        index = self.cur_ip[1] + 1

        ip = self.grammar['ip']

        # Loop through all the valid levels left
        while level <= self.max_level:

            # Check to see if there is a IP option for the current level
            size = len(ip[level])
            if size > index:

                # Save the new IP pointer
                self.cur_ip = [level, index]

                # Reset the current guess
                self.cur_guess = GuessStructure(
                    cp = self.grammar['cp'],
                    max_level = self.max_level,
                    ip = self.grammar['ip'][self.cur_ip[0]][self.cur_ip[1]],
                    cp_length = self.grammar['ln'][self.cur_len[0]][self.cur_len[1]],
                    target_level = self.target_level - self.cur_len[0] - self.cur_ip[0],
                    optimizer = self.optimizer,
                    )
                return True

            # No valid items at this level, check if we can go up a level
            level += 1
            index = 0
            if level > self.max_level:
                return False
            elif level > working_target:
                return False

    def save_session(self, file_name):
        """
        Saves a cracking session to disk

        Note: Using python pickles just to make coding it easier
        Of course that makes debugging harder, and the overall saving slower though.
        May move away from this in the future

        Inputs:
            file_name: The file to save the cracking session to

        Returns:
            None
        """
        with open(file_name, 'wb') as file:

            # Save the Markov Cracker variables here
            pickle.dump(self.target_level, file)
            pickle.dump(self.cur_ip, file)
            pickle.dump(self.cur_len, file)

            # Save the guess structure variables here, not saving the full guess structure since it
            # includes a link to the grammar itself.
            pickle.dump(self.cur_guess.parse_tree, file)
            pickle.dump(self.cur_guess.first_guess, file)

    def load_session(self, file_name, pt_item):
        """
        Restores a session from disk

        Inputs:
            file_name: The name of the file to load the session from

            pt_item: Status report item that needs to be re-initialized

        Returns:
            None
        """
        with open(file_name, 'rb') as file:

            # Reset the options for the Markov Cracker
            self.target_level = pickle.load(file)
            self.cur_ip = pickle.load(file)
            self.cur_len = pickle.load(file)

            # Reset the current guess
            parse_tree = pickle.load(file)
            first_guess = pickle.load(file)

            self.cur_guess = GuessStructure(
                cp = self.grammar['cp'],
                max_level = self.max_level,
                ip = self.grammar['ip'][self.cur_ip[0]][self.cur_ip[1]],
                cp_length = self.grammar['ln'][self.cur_len[0]][self.cur_len[1]],
                target_level = self.target_level - self.cur_len[0] - self.cur_ip[0],
                optimizer = self.optimizer
                )

            # Update the status report item with the real level
            pt_item['pt'][0][1] = self.target_level -1
            pt_item['pt'][0][2] = self.target_level -1

            self.cur_guess.parse_tree = parse_tree
            self.cur_guess.first_guess = first_guess
