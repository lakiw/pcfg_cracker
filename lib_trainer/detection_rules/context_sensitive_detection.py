#!/usr/bin/env python3


"""
This file contains the functionality to detect context sensitive replacements

Examples include strings that contain multiple character types that have
context sensitive meaning when combined. For example ';p', '#1', '<3'

"""



def detect_context_sensitive(section):
    """
    Looks for context sensitive replacements in a section

    For example password#1 would extract '#1'

    Variables:

    section: The current section of the password to process
    This function will break up the section into multiple parts
    if a context sensitive string is found

    Returns:
        There are two return values:
        parsing, found

        parsing: A list of the sections to return
        E.g. input password is 'password#1'
        parsing should return:
        [('password',None),('#1','X')]

        found: The context sensitive string found parsing this section, or None

    """
    # Note: context sensitive matching *is* case sensitive
    working_string = section[0]
    parsing = []

    ## Context Sensitve Replacements need to be manually specified here
    #
    # Identifying new context sensitive strings automatically is a tough problem
    # Steps similar to multiword detection might be useful as an alternative
    # strategy, but that's a big lift to get working, and quite honestly would
    # likely not have that big of an impact in the final grammar due to the
    # rareness of context sensitive strings used by users beyond what is specified
    # below
    #
    context_sensitive_replacements = [
        ";p",
        ":p",
        "*0*",
        "#1",
        "No.1",
        "no.1",
        "No.",
        "i<3",
        "I<3",
        "<3",
        "Mr.",
        "mr.",
        "MR.",
        "MS.",
        "Ms.",
        "ms.",
        "Mz.",
        "mz.",
        "MZ.",
        "St.",
        "st.",
        "Dr.",
        "dr.",

    ]

    # Look for each of the replacements
    for replacement in context_sensitive_replacements:

        start_index = working_string.find(replacement)

        # Did not find this replacement
        if start_index == -1:
            continue

        # False positive checks for #1 since #1234 and the like would trigger
        # this. Doing a simple bailout that will miss #1234pass#1 since the
        # frequencys that a false negative are expected to occur should not
        # noticably impact the effectiveness of the grammar
        if replacement == '#1':
            if start_index < len(working_string) - 3:
                if working_string[start_index + 3].isdigit():
                    # False positive
                    continue

        ## Found a context sensitive string

        # Update the parsing
        #
        # If the CS string did not start the password. aka 'pass#1'
        if start_index != 0:
            parsing.append((working_string[0:start_index], None))

        # Mark the context sensitive string as parsed
        parsing.append((working_string[start_index:start_index + len(replacement)], 'X1'))

        # If there is non-CS data at the end. aka '#1pass'
        if start_index + len(replacement) < len(working_string):
            parsing.append((working_string[start_index + len(replacement):], None))

        return parsing, replacement

    # No context sensitive string found
    return section, None


def context_sensitive_detection(section_list):
    """
    Finds context sensitive strings in the password

    Returns:
        Returns one list, conext_sensitive_list

        context_sensitive_list: A list of the CS strings that were detected

    """

    context_sensitive_list = []
    ## Do a pass through and detect context sensitive strings
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

            parsing, cs_string = detect_context_sensitive(section_list[index])

            # If a context sensitive string was detected
            if cs_string:
                context_sensitive_list.append(cs_string)

                # This is a trick to use the list extend but at an index
                del section_list[index]
                section_list[index:index] = parsing

                # We still need to check the first section again in case
                # it was classified as unparsed
                continue

        index += 1
    return context_sensitive_list
