#!/usr/bin/env python3


"""

This file contains the functionality to create base structures

These are the first transistions in the PCFG. For example A5D2

"""


def base_structure_creation(section_list):
    """
    Parse out the base structure in a password

    Returns:
        Returns two values, is_valid, base_structure

        is_supported: If the base structure is currently supported by the default
        PCFG cracker. This is useful since things like e-mail addresses
        and websites will likely not have support until targeted
        cracking sessions support is added

        base_structure: A string representing a base structures
    """

    # Saving this as a list and will join it at the end
    base_structure = []

    # If the base structure is currently supported by the standard PCFG cracker
    is_supported = True

    ## Do a pass through the parsing and create a base structure
    #
    # Walk through each section and parse it individually
    #
    for section in section_list:

        # Sanity check, this should never happen
        if section[1] is None:
            print("Error with parsing this password")
            print(str(section_list))
            raise ValueError

        # Check for unsupported transistions
        if section[1][0] in ['W','E']:
            is_supported = False

        base_structure.append(section[1])

    return is_supported, ''.join(base_structure)
