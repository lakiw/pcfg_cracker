#!/usr/bin/env python3


"""

Logic to create the PRINCE wordlist

Top level function is:
    create_prince_wordlist(pcfg, max_size)

"""


import sys

# Local Imports
from lib_guesser.priority_queue import PcfgQueue


def create_prince_wordlist(pcfg, max_size):
    """
    This is basically a stripped down version of the normal PCFG guesser

    You give it a specialized PCFG grammar tailored for generating PRINCE
    style guesses, and it outputs the guesses generated for this.

    Note: The PCFG grammar for PRINCE generally is typically only one
    transision, (or two if it has case mangling), so it should be
    pretty quick and not expand the size of the pqueue since each
    node will generally have only one child, (or two if case mangling).

    Note: The grammar itself contains information about where the
    guesses generated will be saved (either stdout, or to a file)

    Inputs:
        pcfg: The PCFG grammar

        max_size: the maximum number of guesses/wordlist items
        to generate using this tool

    Returns:
        None
    """

    pqueue = PcfgQueue(pcfg)

    # Number of words generated
    num_generated_guesses = 0

    print("creating wordlist",file=sys.stderr)

    # Keep running while the p_queue.next_function still has items in it
    while max_size is None or num_generated_guesses < max_size:

        ## Get the next item from the pqueue
        pt_item = pqueue.next()

        # If the pqueue is empty, there are no more guesses to make
        if pt_item is None:
            break

        # Create the words for the dictionary
        try:
            num_generated_guesses += pcfg.create_guesses(pt_item['pt'])

        # The receiving program is no longer accepting guesses
        except OSError:
            break

    print ("Done generating the PRINCE wordlist.",file=sys.stderr)
