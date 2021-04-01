#!/usr/bin/env python3


"""

This file contains the functionality to detect keyboard walks

The keyboard walk blacklist will also be contained here, as there are
a lot of dicitonary words that look like keyboard walks

"""


def find_keyboard_row_column(char):
    """
    Finds the keyboard row and column of a character

    This is currently configured for a standard US QWERTY KeyboardInterrupt
    If other keyboard layouts are desired they could be added later

    """

    # I'm leaving off '`' but it is rarely used in keyboard combos and
    # it makes the code cleaner
    row1=['1','2','3','4','5','6','7','8','9','0','-','=']
    s_row1=['!','@','#','$','%','^','&','*','(',')','_','+']

    row2=['q','w','e','r','t','y','u','i','o','p','[',']','\\']
    s_row2=['Q','W','E','R','T','Y','U','I','O','P','{','}','|']

    row3=['a','s','d','f','g','h','j','k','l',';','\'']
    s_row3=['A','S','D','F','G','H','J','K','L',':','"']

    row4=['z','x','c','v','b','n','m',',','.','/']
    s_row4=['Z','X','C','V','B','N','M','<','>','?']

    if char in row1:
        return (0,row1.index(char))

    if char in s_row1:
        return (0,s_row1.index(char))

    if char in row2:
        return (1,row2.index(char))

    if char in s_row2:
        return (1,s_row2.index(char))

    if char in row3:
        return (2,row3.index(char))

    if char in s_row3:
        return (2,s_row3.index(char))

    if char in row4:
        return (3,row4.index(char))

    if char in s_row4:
        return (3,s_row4.index(char))

    # Default value for keys that are not checked + non-ASCII chars
    return None


def is_next_on_keyboard(past, current):
    """

    Finds if a new key is next to the previous key

    """
    # Check to see if either past or current keys are not valid
    if (past is None) or (current is None):
        return False

    # Adding exclusion for repeated characters, aka '112233'
    if (current[0] == past[0]) and (current[1] == past[1]):
        return False

    # If they both occur on the same row (easy)
    if current[0] == past[0]:
        if (current[1] == past[1]) or (current[1] == past[1]-1) or (current[1] == past[1]+1):
            return True

    ## If it occurs one row down from the past combo
    #
    # Gets a bit weird since they "rows" don't exactly line up
    # aka 'w' (pos 1) is next to 'a' (pos 0) and 's' (pos 1)
    #
    elif current[0] == past[0]+1:
        if (current[1] == past[1]) or (current[1] == past[1]-1):
            return True

    # If it occurs one row up from the past combo
    elif current[0] == past[0]-1:
        if (current[1] == past[1]) or (current[1] == past[1]+1):
            return True

    ##-- The two keys are not adjacent according to the checked keyboard
    return False


def interesting_keyboard(combo):
    """
    Filters keyboard walks to try and limit false positives

    Currently only defining "interesting" keyboard combos as a combo that has
    multiple types of characters, aka alpha + digit

    Also added some filters for common words that tend to look like
    keyboard combos

    Note, this can cause some false negatives in certain cases where a true
    keyboard combo will happen after a false positive check but still be
    part of the original como. For example 'er5tgb'

    Haven't seen this much in user behavior so it shouldn't have much impact
    but want to disclose that for future coders. May eventually want to add
    checks for that.

    """


    # Length check
    if len(combo) < 3:
        return False

    ## Filter combos that start with "likely" partial words
    #
    # These occur from common english words that look like keyboard combos
    # E.g. 'deer43'
    #
    if (combo[0] == 'e'):
        return False

    if (combo[1] == 'e') and (combo[2] == 'r'):
        return False

    if (combo[0] == 't') and (combo[1] == 'y'):
        return False

    if (combo[0] == 't') and (combo[1] == 't') and (combo[2] == 'y'):
        return False

    if (combo[0] == 'y'):
        return False

    ## Reject words that look like keyboard combos
    #
    # Eventually might want to read in a blacklist from a file vs
    # hardcoding it here
    #
    # TODO: Some of the shorter strings will also cover the longer strings
    #       That is a function of how I'm currently adding into the blacklist
    #       May want to clean this up a bit, though it is useful to record
    #       for future research.
    #
    false_positive_words = [
        "drew",
        "kiki",
        "fred",
        "were",
        "pop",
    ]
    full_lower_word = ''.join(combo).lower()

    for item in false_positive_words:
        if item in full_lower_word:
            return False

    # Check for complexity requirements
    alpha = 0
    special = 0
    digit = 0
    for value in combo:
        if value.isalpha():
            alpha=1
        elif value.isdigit():
            digit=1
        else:
            special=1

    # If it meets all the complexity requirements
    if (alpha + special + digit) >=2:
        return True

    return False


def detect_keyboard_walk(password, min_keyboard_run = 4):
    """
    Looks for keyboard combinations in the training data for a section

    For example 1qaz or xsw2

    Variables:

        password: The current section of the password to process
        When first called this will be the whole process.
        This function calls itself recursively so will then parse
        smaller chunks of this password as it goes along

        min_keyboard_run: The minimum size of a keyboard run

    Returns:
        There are two return values:
        section_list, found_list

        section_list: A list of the sections to return
        E.g. input password is 'test1qaztest'
        section_list should return:
        [('test',None),('1qaz','K4'),('test',None)]

        found_list: A list of every keyboard combo found when parsing password

    """

    # The keyboard position of the last key processed
    past_pos = None

    # The current keyboard combo
    cur_combo = []

    # The current found list
    found_list = []

    # The current section list of parsing
    section_list = []

    # Loop through each character to find the combos
    for index, value in enumerate(password):

        # Find the current location of the key on the keyboard
        pos = find_keyboard_row_column(value)

        # Check to see if a run is occuring, (two keys next to each other)
        is_run = is_next_on_keyboard(past_pos, pos)

        # If it is a run, keep it going!
        if is_run is True:
            cur_combo.append(value)

        # The keyboard run has stopped
        else:
            if len(cur_combo) >= min_keyboard_run:

                ## Look at saving this keyboard combo
                #
                # See if the keyboard combo is interesting enough to save
                if interesting_keyboard(cur_combo):

                    # Save the results
                    found_list.append(''.join(cur_combo))

                    ## Update base structure mask
                    #
                    # Update any unprocessed sections before the current run
                    if len(cur_combo) != index:
                        section_list.append((password[0:index-len(cur_combo)],None))

                    # Update the mask for the current run
                    section_list.append((''.join(cur_combo),"K"+str(len(cur_combo)) ))

                    # If not the last section, go recursive and call it with
                    # what's remaining
                    if index != (len(password)):
                        temp_section, temp_found = detect_keyboard_walk(password[index:])

                        # update info if needed
                        section_list.extend(temp_section)
                        if temp_found:
                            found_list.extend(temp_found)

                        # Now return since we don't want to parse the same data twice
                        return section_list, found_list

            # Start a new run
            cur_combo = [value]

        # What was new is now old. Update the previous position
        past_pos = pos

    # Update the last run if needed
    if len(cur_combo) >= min_keyboard_run:

        ## Look at saving this keyboard combo
        #
        # See if the keyboard combo is interesting enough to save
        if interesting_keyboard(cur_combo):

            # Save the results
            found_list.append(''.join(cur_combo))

            ## Update base structure mask
            #
            # Update any unprocessed sections before the current run
            if len(cur_combo) != len(password):
                section_list.append((password[0:len(password)-len(cur_combo)],None))

            # Update the mask for the current run
            section_list.append((''.join(cur_combo),"K"+str(len(cur_combo))))

        # Not treating it as a keyboard combo since it is not intersting
        else:
            section_list.append((password,None))

    # No keyboard run found
    else:
        section_list.append((password,None))

    return section_list, found_list
