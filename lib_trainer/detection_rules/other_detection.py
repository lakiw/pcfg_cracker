#!/usr/bin/env python3


"""

This file contains the functionality to identify "other" strings

Note: This is the last categorization, so anything not already will been
classified as "other". In general this will be what is usually labeled as
special characters. E.g. '!@#$%^&....' but it is labeled other to support
different languages and encodings.

"""


def other_detection(section_list):
    """
    Finds other strings in the password

    Returns:

        other_list: A list of other strings that were detected

    """

    other_list = []

    ## Do a pass through and detect other strings
    #
    # Walk through each section and parse it individually
    # Using an index since it lets me split items up while parsing the
    # whole list
    #
    index = 0
    while index < len(section_list):

        # Skip sections that have been processed earlier, for example
        # by keyboard walk detection
        if section_list[index][1] is None:

            section_list[index] = (section_list[index][0],'O' + str(len(section_list[index][0])) )
            other_list.append(section_list[index][0])

        index += 1

    return other_list
