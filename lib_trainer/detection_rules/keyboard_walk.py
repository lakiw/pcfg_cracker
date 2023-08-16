#!/usr/bin/env python3


"""

This file contains the functionality to detect keyboard walks

The keyboard walk blacklist will also be contained here, as there are
a lot of dicitonary words that look like keyboard walks

"""


def _get_us_keyboard():
    """
    Returns a dictionary of key mappings for a US keyboard. 
    Abstracting this out to make adding non-US QWERTY keyboard easier to add.

    Inputs:
        None

    Returns:
        key_mapping: (dictionary) A dictionary containing the key mappings

        .. code-block:: python
            {
                'name':"The name of the keyboard used",
                'row1':[values from top row of keyboard],
                's_row1':[values from top row of keyboard + shift],
                'row2':[values from second row of keyboard],
                's_row2':[values from second row of keyboard + shift],
                'row3':[values from third row of keyboard],
                's_row3':[values from third row of keyboard + shift],
                'row4':[values from bottom row of keyboard],
                's_row4':[values from bottom row of keyboard + shift],
            }
    """

    keyboard_mapping = {

        'name': "qwerty",

        'row1': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
        's_row1': ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+'],

        'row2': ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\\'],
        's_row2': ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '{', '}', '|'],

        'row3': ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\''],
        's_row3': ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ':', '"'],

        'row4': ['z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/'],
        's_row4': ['Z', 'X', 'C', 'V', 'B', 'N', 'M', '<', '>', '?'],
    }

    return keyboard_mapping


def _get_jcuken_keyboard():
    """
    Returns a dictionary of key mappings for a Russian JCUKEN keyboard. 
    Abstracting this out to make adding non-US QWERTY keyboard easier to add.

    Note: I found a lot of variation of many of the punctuation characters
    across different keyboard variations. I'm going with the layout described
    in kwprocessor: https://github.com/hashcat/kwprocessor/blob/master/keymaps/ru.keymap
    My reasoning is that's been vetted the most and has the most buy-in from the
    password cracking community.    

    Inputs:
        None

    Returns:
        key_mapping: (dictionary) A dictionary containing the key mappings

        .. code-block:: python
            {
                'name':'The name of the keyboard mapping',
                'row1':[values from top row of keyboard],
                's_row1':[values from top row of keyboard + shift],
                'row2':[values from second row of keyboard],
                's_row2':[values from second row of keyboard + shift],
                'row3':[values from third row of keyboard],
                's_row3':[values from third row of keyboard + shift],
                'row4':[values from bottom row of keyboard],
                's_row4':[values from bottom row of keyboard + shift],
            }
    """

    # Leaving off the leading 'ё' for the first row
    keyboard_mapping = {

        'name': 'jcuken',

        'row1': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
        's_row1': ['!', '"', '№', ';', '%', ':', '?', '*', '(', ')', '_', '+'],

        'row2': ['й', 'ц', 'у', 'к', 'е', 'н', 'г', 'ш', 'щ', 'з', 'х', 'ъ', '\\'],
        's_row2': ['Й', 'Ц', 'У', 'К', 'Е', 'Н', 'Г', 'Ш', 'Щ', 'З', 'Х', 'Ъ', '/'],

        'row3': ['ф', 'ы', 'в', 'а', 'п', 'р', 'о', 'л', 'д', 'ж', 'э'],
        's_row3': ['Ф', 'Ы', 'В', 'А', 'П', 'Р', 'О', 'Л', 'Д', 'Ж', 'Э'],

        'row4': ['я', 'ч', 'с', 'м', 'и', 'т', 'ь', 'б', 'ю'],
        's_row4': ['Я', 'Ч', 'С', 'М', 'И', 'Т', 'Ь', 'Б', 'Ю', ','],
    }

    return keyboard_mapping


def find_keyboard_row_column(char, keyboards):
    """
    Finds the keyboard row and column of a character

    Inputs:
        char: (char) The character to find

        keyboards: (list) The list of keyboards to search

    Returns:
        pos_list: (dictionary) A dictionary of all possible positions it could be 
        for different keyboard types. Each keyboard finding is saved as the following dictionary:

        .. code-block:: python
            "The name of the keyboard used":{
                'row':"(int) The row of the key",
                'pos':"(int) The position of key in the row"
            }

    """

    pos_list = {}

    for board in keyboards:
        if char in board['row1']:
            pos_list[board['name']] = {
                'row': 1,
                'pos': board['row1'].index(char)
            }
            continue

        if char in board['s_row1']:
            pos_list[board['name']] = {
                'row': 1,
                'pos': board['s_row1'].index(char)
            }
            continue

        if char in board['row2']:
            pos_list[board['name']] = {
                'row': 2,
                'pos': board['row2'].index(char)
            }
            continue

        if char in board['s_row2']:
            pos_list[board['name']] = {
                'row': 2,
                'pos': board['s_row2'].index(char)
            }
            continue

        if char in board['row3']:
            pos_list[board['name']] = {
                'row': 3,
                'pos': board['row3'].index(char)
            }
            continue

        if char in board['s_row3']:
            pos_list[board['name']] = {
                'row': 3,
                'pos': board['s_row3'].index(char)
            }
            continue

        if char in board['row4']:
            pos_list[board['name']] = {
                'row': 4,
                'pos': board['row4'].index(char)
            }
            continue

        if char in board['s_row4']:
            pos_list[board['name']] = {
                'row': 4,
                'pos': board['s_row4'].index(char)
            }
            continue

    # Note: pos_list may be empty for characters that don't have any directy
    # keyboard mappings
    return pos_list


def is_next_on_keyboard(past, current):
    """

    Finds if a new key is next to the previous key

    Inputs:
        past: (dictionary) A dict of all the keyboard locations for the previous character

        current: (dictionary) A dict of all the keyboard locations on the current keyboard

    Returns:
        current_runs: (dictionary) A list of all the keyboards this run is happening on


    """

    current_runs = {}

    # Check to see if either past or current keys are not valid
    if (past is None) or (current is None):
        return []

    # Loop through the past keyboards that were detected
    for past_name, past_data in past.items():

        # Quick fail if both characters were not found in the same dictionary
        if past_name not in current:
            continue

        cur_data = current[past_name]

        # Adding exclusion for repeated characters, aka '112233'
        if (cur_data['row'] == past_data['row']) and (cur_data['pos'] == past_data['pos']):
            continue

        # If they both occur on the same row (easy)
        if cur_data['row'] == past_data['row']:
            if (cur_data['pos'] == past_data['pos'] - 1) or (cur_data['pos'] == past_data['pos'] + 1):
                current_runs[past_name] = {
                    'past_row': past_data['row'],
                    'past_pos': past_data['pos'],
                    'cur_row': cur_data['row'],
                    'cur_pos': cur_data['pos']
                }
                continue

        # If it occurs one row down from the past combo
        #
        # Gets a bit weird since they "rows" don't exactly line up
        # aka 'w' (pos 1) is next to 'a' (pos 0) and 's' (pos 1)
        #
        elif cur_data['row'] == past_data['row'] + 1:
            if (cur_data['pos'] == past_data['pos']) or (cur_data['pos'] == past_data['pos'] - 1):
                current_runs[past_name] = {
                    'past_row': past_data['row'],
                    'past_pos': past_data['pos'],
                    'cur_row': cur_data['row'],
                    'cur_pos': cur_data['pos']
                }
                continue

        # If it occurs one row up from the past combo
        elif cur_data['row'] == past_data['row'] - 1:
            if (cur_data['pos'] == past_data['pos']) or (cur_data['pos'] == past_data['pos'] + 1):
                current_runs[past_name] = {
                    'past_row': past_data['row'],
                    'past_pos': past_data['pos'],
                    'cur_row': cur_data['row'],
                    'cur_pos': cur_data['pos']
                }
                continue

    return current_runs


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

    # Filter combos that start with "likely" partial words
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

    if (combo[0] == '1') and (combo[1] == '2') and (combo[2] == '3'):
        return False

    # Filter combos that end with "likely partial words"
    #
    if (combo[-1] == '3') and (combo[-2] == '2') and (combo[-3] == '1') and (combo[-4] not in ['q', 'Q']):
        return False

    # Reject words that look like keyboard combos
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

        # jcuken false positives
        "123;",
        "234;",
        "й123"
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
            alpha = 1
        elif value.isdigit():
            digit = 1
        else:
            special = 1

    # If it meets all the complexity requirements
    if (alpha + special + digit) >= 2:
        return True

    return False


def detect_keyboard_walk(password, min_keyboard_run=4):
    """
    Looks for keyboard combinations in the training data for a section

    For example 1qaz or xsw2

    Variables:

        password: The current section of the password to process
        When first called this will be the whole password.
        This function calls itself recursively so will then parse
        smaller chunks of this password as it goes along

        min_keyboard_run: The minimum size of a keyboard run

    Returns:
        There are three return values:
        section_list, found_list, detected_keyboards

        section_list: A list of the sections to return
        E.g. input password is 'test1qaztest'
        section_list should return:
        [('test',None),('1qaz','K4'),('test',None)]

        found_list: A list of every keyboard combo found when parsing password

        detected_keyboards: (List) All keyboards that have been involved in a keyboard walk

    """

    # The keyboard position of the last key processed
    past_pos_list = {}

    # The current keyboard combo
    cur_combo = []

    # List of all the keyboards involved in this run
    keyboard_run_list = []

    # The current found list
    found_list = []

    # The current section list of parsing
    section_list = []

    # List of all keyboards that have been involved in a keyboard walk
    detected_keyboards = []

    # A list of all the keyboard layouts. The ordering matters for what order they are checked
    # aka if a key appears in multiple keyboard layouts, it will start a mapping with the first
    # layout the key is found in. Yes this can lead to false positives, but when training on
    # large datasets, it's hard to standardize on one keyboard layout...
    #
    # Note, this ordering can be changed as the password is processed if a key on a later keyboard
    # is found as part of the password analysis
    keyboards = []

    keyboards.append(_get_us_keyboard())
    keyboards.append(_get_jcuken_keyboard())

    # Loop through each character to find the combos
    for index, value in enumerate(password):

        # Find the current location of the key on the keyboard
        pos_list = find_keyboard_row_column(value, keyboards)

        # Save statistics about keyboards detected
        # Initialize based on the first character found
        if index == 0:
            for board in pos_list:
                if board not in detected_keyboards:
                    detected_keyboards.append(board)
        # Now remove any keyboards that don't match as the parsing continues
        # This means the list of potential keyboards only shrinks after the first
        # character, never grows. This is more restrictive than the current keyboard
        # walk detection, so may want to revisit this if problems occur.
        else:
            detected_keyboards = [
                key for key in detected_keyboards if key in pos_list]

        # Check to see if a run is occuring, (two keys next to each other)
        current_runs = is_next_on_keyboard(past_pos_list, pos_list)

        past_pos_list = pos_list.copy()

        # Set up the keyboard_run_list to ensure that the runs only apply to the current keyboard detected at the start
        if not keyboard_run_list:
            # Note, if current_runs is empty this will be a slightly costly noopt. I could make another if
            # statement here, but I figured it was worth the cost to keep the code cleaner
            keyboard_run_list = current_runs.copy()

        # Remove runs that are not part of the current run
        else:
            for key in list(keyboard_run_list):
                if key not in current_runs:
                    keyboard_run_list.pop(key, None)

        # If it is a run, keep it going!
        if keyboard_run_list:
            cur_combo.append(value)

        # The keyboard run has stopped
        else:
            if len(cur_combo) >= min_keyboard_run:

                # Look at saving this keyboard combo
                #
                # See if the keyboard combo is interesting enough to save
                if interesting_keyboard(cur_combo):

                    # Save the results
                    found_list.append(''.join(cur_combo))

                    # Update base structure mask
                    #
                    # Update any unprocessed sections before the current run
                    if len(cur_combo) != index:
                        section_list.append(
                            (password[0:index-len(cur_combo)], None))

                    # Update the mask for the current run
                    section_list.append(
                        (''.join(cur_combo), "K"+str(len(cur_combo))))

                    # If not the last section, go recursive and call it with
                    # what's remaining
                    if index != (len(password)):
                        temp_section, temp_found, temp_detected_keyboards = detect_keyboard_walk(
                            password[index:])

                        # update info if needed
                        section_list.extend(temp_section)
                        if temp_found:
                            found_list.extend(temp_found)

                        detected_keyboards = [
                            key for key in temp_detected_keyboards if key in detected_keyboards]

                        # Now return since we don't want to parse the same data twice
                        return section_list, found_list, detected_keyboards

            # Start a new run
            cur_combo = [value]

    # Update the last run if needed
    if len(cur_combo) >= min_keyboard_run:

        # Look at saving this keyboard combo
        #
        # See if the keyboard combo is interesting enough to save
        if interesting_keyboard(cur_combo):

            # Save the results
            found_list.append(''.join(cur_combo))

            # Update base structure mask
            #
            # Update any unprocessed sections before the current run
            if len(cur_combo) != len(password):
                section_list.append(
                    (password[0:len(password)-len(cur_combo)], None))

            # Update the mask for the current run
            section_list.append((''.join(cur_combo), "K"+str(len(cur_combo))))

        # Not treating it as a keyboard combo since it is not intersting
        else:
            section_list.append((password, None))

    # No keyboard run found
    else:
        section_list.append((password, None))

    return section_list, found_list, detected_keyboards


if __name__ == "__main__":
    section_list, found_list, detected_keyboards = detect_keyboard_walk("123;")
    print(section_list)
    print(found_list)
    print(detected_keyboards)
