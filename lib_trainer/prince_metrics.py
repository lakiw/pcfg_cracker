#!/usr/bin/env python3


"""
This file contains logic for extracting data that will be useful for
generating wordlists to use in an optimized PRINCE guessing session

Note: While PRINCE is not a PCFG based guess generator, the data generated
by this trainer can be useful for supporting other attack modes

Note 2: This is mostly a placeholder as all it does now is update the
count_prince Counter with each parsed section. The plan is eventually to
add additional logic in here that may be useful for optimizing a PRINCE
dictionary. For example, certain objects may be weighted to make them more or
less likely.
"""


def prince_evaluation(count_prince, section_list):
    """
    Save any statistics that would be useful to generating PRINCE wordlists

    Note: This should be called after all the individual sections of an input
    password has already been parsed

    Variables:
        count_prince: (Counter) A Python Counter object that holds all the
        sections that will be saved for PRINCE metrics

        section_list: (List) A list containing all of the base_structure
        sections for the parsed password

    Returns:
        None: No return value

    """

    #Loop through the section list and add it to the PRINCE counts
    for item in section_list:
        count_prince[item[1]] += 1
