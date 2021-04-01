#!/usr/bin/env python3


"""

This file contains the functionality to identify alpha strings, (letters)

This will call multiword detection, though multiword detection code is
not included in this file, and is handled by multiword_detector.py using the
MultiWordDetector class

"""


def detect_alpha(section, multiword_detector):
    """
    Looks for alpha strings in a section

    For example 123password@#$ will extract 'password'

    Variables:

        section: The current section of the password to process

        multiword_detector: The multiword detector to identify multiwords

    Returns:
        There are three return values:

        parsing, found_strings, masks

        parsing: A list of the sections to return
        E.g. input password is '123password'
        parsing should return:
        [('123',None),('password','A')]

        found_strings: A list containing all the alpha strings found for a section

        masks: A list containing all of the capitalization masks. For example, the
        alpha string 'PaSSword' would have a mask of 'ULUULLLL'

    """

    # The alpha strings themselves will be saved as all lowercase, but
    # we'll need to go back to the original version to grab the capitalization
    # masks
    #
    working_string = section[0].lower()
    parsing = []

    # Tells if a run is currently happening of alpha values
    is_run = False

    # The start location of a run
    start_pos = -1

    for pos, value in enumerate(working_string):

        # Continue or start a run
        if value.isalpha():
            # Start a run
            if not is_run:
                is_run = True
                start_pos = pos

        # Possible end of a run, either this is the last character or not an
        # alpha string
        #
        # Not doing this as an "else" statement so I don't have to repeat
        # the code to deal with runs ending if the letter isn't alpha or we
        # hit the end of the pw
        if not value.isalpha() or pos == len(working_string) - 1:
            # Need to stop a run and process it
            if is_run:
                # Update the parsing info if data occurs before the alpha run
                if start_pos !=0:
                    parsing.append((section[0][0:start_pos],None))

                # Need to set end_pos since pos can be the end of the string or
                # after the end depending on how we got here
                if value.isalpha():
                    end_pos = pos
                else:
                    # Don't have to check for bounds since is_run would not
                    # be set if the pw was only one char long
                    end_pos = pos - 1

                # Need to check for multiwords
                is_multi, word_list = multiword_detector.parse(
                    working_string[start_pos:end_pos + 1]
                    )

                # Initialize the mask list to return the case mangling masks
                mask_list = []

                ## loop through all the words returned by multiword_detector
                #
                # Need to keep track of where each word starts in the working_string
                current_start = start_pos
                for word in word_list:
                    # Update the parsing
                    parsing.append(
                        (section[0][current_start:current_start+len(word)],'A' + str(len(word)))
                        )

                    # Add in the mask
                    mask = ''
                    for letter in section[0][current_start:current_start+len(word)]:
                        if letter.isupper():
                            mask +='U'
                        else:
                            mask +='L'
                    mask_list.append(mask)

                    # Update the pointer to the start of the word
                    current_start +=len(word)

                # Update the parsing info if data occurs after the alpha run
                if end_pos != len(section[0]) -1:
                    parsing.append((section[0][end_pos+1:],None))

                return parsing, word_list, mask_list


    return section, None, None


def alpha_detection(section_list, multiword_detector):
    """
    Finds alpha strings in the password

    Returns:
        Returns two lists, alpha_list and mask_list

        alpha_list: A list of alpha strings that were detected

        mask_list: A list containing all of the capitalization masks that were
        detected

    """


    alpha_list = []
    mask_list = []

    ## Do a pass through and detect alpha strings
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

            parsing, alphas, masks = detect_alpha(section_list[index], multiword_detector)

            # If an alpha string was detected
            if alphas:
                alpha_list.extend(alphas)
                mask_list.extend(masks)

                # This is a trick to use the list extend but at an index
                del section_list[index]
                section_list[index:index] = parsing

        index += 1

    return alpha_list, mask_list
