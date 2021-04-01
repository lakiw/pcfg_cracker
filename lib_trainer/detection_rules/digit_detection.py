#!/usr/bin/env python3


"""
This file contains the functionality to identify digit strings

Note, some digit strings may be classified before this is called, for example
the year detection code will classify some four digit numbers as years

"""


def detect_digits(section):
    """
    Looks for digit strings in a section

    For example 123password@#$ will extract '123'

    Variables:

        section: The current section of the password to process

    Returns:
        There are two return values:
        parsing, found_strings

        parsing: A list of the sections to return
        E.g. input password is '123password'
        parsing should return:
        [('123','D'),('password', None)]

        found_digit: The digit that was found

    """
    working_string = section[0]
    parsing = []

    # Tells if a run is currently happening of alpha values
    is_run = False

    # The start location of a run
    start_pos = -1

    for pos, value in enumerate(working_string):

        # Continue or start a run
        if value.isdigit():
            # Start a run
            if not is_run:
                is_run = True
                start_pos = pos

        # Possible end of a run, either this is the last character or not an
        # digit string
        #
        # Not doing this as an "else" statement so I don't have to repeat
        # the code to deal with runs ending if the letter isn't a digit or we
        # hit the end of the pw
        if not value.isdigit() or pos == len(working_string) - 1:
            # Need to stop a run and process it
            if is_run:
                # Update the parsing info if data occurs before the alpha run
                if start_pos !=0:
                    parsing.append((section[0][0:start_pos],None))

                # Need to set end_pos since pos can be the end of the string or
                # after the end depending on how we got here
                if value.isdigit():
                    end_pos = pos
                else:
                    # Don't have to check for bounds since is_run would not
                    # be set if the pw was only one char long
                    end_pos = pos - 1

                ## Parse the section where digits were found
                found_digit = ''.join(section[0][start_pos:end_pos + 1])

                parsing.append((found_digit,'D' + str(len(found_digit)) ))

                # Update the parsing info if data occurs after the alpha run
                if end_pos != len(section[0]) -1:
                    parsing.append((section[0][end_pos+1:],None))

                return parsing, found_digit


    return section, None


def digit_detection(section_list):
    """
    Finds digit strings in the password

    Returns:
        Returns one list, digit_list

        digit_list: A list of digit strings that were detected

    """

    digit_list = []

    ## Do a pass through and detect digit strings
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

            parsing, digit_string = detect_digits(section_list[index])

            # If a digit string was detected
            if digit_string is not None:
                digit_list.append(digit_string)

                # This is a trick to use the list extend but at an index
                del section_list[index]
                section_list[index:index] = parsing

        index += 1

    return digit_list
