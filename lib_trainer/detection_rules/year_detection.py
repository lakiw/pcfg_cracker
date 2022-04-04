#!/usr/bin/env python3


"""

This file contains the functionality to detect years, such as '2021'

"""


def detect_year(section):
    """
    Looks for years in a section

    For example password2019 would extract '2019'

    Variables:

        section: The current section of the password to process

    Returns:
        There are two return values:
        parsing, found

        parsing: A list of the sections to return
        E.g. input password is 'password2019'
        parsing should return:
        [('password',None),('2019',Y)]

        found: The year found parsing this section, or None

    """

    working_string = section[0]
    parsing = []

    ## Note, currently only idendifying four digit years, aka '2019'.
    #
    # May try to extract two digit years later, aka '19', but not sure
    # how effective that will be since most two digits look like years.
    #
    # As a further filter, only looking at years that start with '19' or '20'

    year_prefix = ['19','20']

    for prefix in year_prefix:
        # Running this in a loop to deal with false positives such as '20pass2019'
        start = 0
        while True:
            start_index = working_string[start:].find(prefix)

            # No year prefix found
            if start_index == -1:
                break

            # Normalize start_index to be the real index into the string
            start_index += start

            ## Potential year found
            #
            # Check length first
            if len(working_string) < start_index + 4:
                # String is too short so break out of the loop
                break

            # Update start so if we have to loop again make sure we don't search
            # the same string again
            start = start_index + 2

            ## Verify that the year is not part of a bigger number, aka '020190'
            #

            # Skip if the previous char was a digit
            if start_index != 0:
                if working_string[start_index -1].isdigit():
                    continue

            # Skip if the following character of the year is a digit
            if start_index + 4 < len(working_string):
                if working_string[start_index + 4].isdigit():
                    continue

            # Check to make sure the next two characters are digits
            if working_string[start_index + 2].isdigit():
                if working_string[start_index + 3].isdigit():
                    # It is a year
                    year = working_string[start_index:start_index + 4]

                    ## Update the parsing
                    #
                    # If there is a non-year at the begining. aka 'pass2019'
                    if start_index != 0:
                        parsing.append((working_string[0:start_index], None))

                    # Mark the year as parsed
                    parsing.append((working_string[start_index:start_index+4],'Y1'))

                    # If there is non-year data at the end. aka '2019pass'
                    if start_index +4 < len(working_string):
                        parsing.append((working_string[start_index+4:], None))

                    return parsing, year

    # No year found
    return section, None


def year_detection(section_list):
    """
    Finds likely years in the password

    Returns:

    year_list: (List) A list of years that were detected

    """

    year_list = []

    ## Do a pass through and detect years
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

            parsing, year = detect_year(section_list[index])

            # If a year was detected
            if year:
                year_list.append(year)

                # This is a trick to use the list extend but at an index
                del section_list[index]
                section_list[index:index] = parsing

                # We still need to check the first section again in case
                # it was classified as unparsed
                continue

        index += 1

    return year_list
