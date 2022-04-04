#!/usr/bin/env python3


"""
This file contains the logic to calculate probabilities for a given Counter

This also includes the logic to perform probability smoothing.

Note: Probability smoothing is currently not implimented
"""


def apply_probability_smoothing(counter):
    """
    Apply probability smoothing

    This is a way to smooth probabilities between different items to help
    the actual password cracker making use of them.

    For example, if 'chair' was seen 100000 times, and 'table' was seen 100001
    times, it would be nice to treat them as the same probability to reduce
    the amount of work the pcfg cracker needs to perform

    Currently this is a no-op / placeholder and does not actually do anything

    Variables:

        counter: A Python Counter object containing all the items to calculate
        probabilities for
    """
    return


def calculate_probabilities(counter):
    """
    Calculated the probabiilty for items stored in a Python Counter

    Variables:

        counter: A Python Counter object containing all the items to calculate
        probabilities for

    Returns:

        prob_list: A Python List containing ('value','probability) pairs
        ordered from hightest probabilty to lowest probability

    """

    # Apply probability smoothing to the counts in the counter
    #
    # Doing this to the raw counts vs. the probabilities since dealing with
    # floats is a pain and is a lot slower
    #
    # If you want to avoid doing probability smoothing at all, then comment
    # out this step
    #
    apply_probability_smoothing(counter)

    # A sum of all the items in the counter
    total_count = sum(counter.values())

    # Get a listing of the elements orderd by most common
    prob_list = counter.most_common()

    # Assign a probability to all the elements vs a raw count
    for index, value in enumerate(prob_list):
        prob_list[index] = (value[0],value[1]/total_count)

    return prob_list
