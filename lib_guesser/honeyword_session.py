#!/usr/bin/env python3


"""
Name: PCFG_Cracker Honeyword Generation Code

Description: Manages generating Honeywords

Making this a class to help support different guess generation
modes in the future

"""


import sys
import time
import threading # Used only for the "check for user input" threads
import random


class HoneywordSession:
    """
    Used to manage a Honeyword generation session
    """

    def __init__(self, pcfg, mode):
        """
        Basic initialization function
        """

        # Save the grammar for easy reference
        self.pcfg = pcfg

        # Save the mode so we know if we are generating random honeywords or
        # doing a repeatable cracking session
        self.mode = mode

        # Initialize the random seed

        # If this is a random walk, make it deterministic to allow reproducability of runs
        if self.mode == "random_walk":
            self.random_seed = 1

        # Generating honeywords so we want this to be random every time we run it
        else:
            self.random_seed = random.randint(0,1000000000000)

    def run(self, limit=0):
        """
        Starts the cracking session and starts generating guesses
        """

        print ("Starting to generate honeyword guesses",file=sys.stderr)

        # Variable to keep track of guesses created in current run.
        num_guess_current = 0

        # Keep running while the p_queue.next_function still has items in it
        while True:

            # Intialize the random number generator
            # I realize doing this every time isn't effecient, but it makes
            # restoring a session easeir.
            random.seed(self.random_seed)
            
            ## Generate the next honeyword pt_item by performing a random walk
            #

            pt_item = self.pcfg.random_walk()

            try:
                num_generated_guesses = self.pcfg.create_guesses(pt_item['pt'], is_honeyword=True, limit=limit)
                num_guess_current += num_generated_guesses

                # Check if a limit was defined
                if limit:
                    limit = limit - num_generated_guesses
                    if limit <= 0:
                        break

            # The receiving program is no longer accepting guesses
            # Usually occurs after all passwords have been cracked
            except OSError:
                break

            # Update the seed to the next one
            self.random_seed += 1

        return