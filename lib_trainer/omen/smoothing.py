#!/usr/bin/env python3


"""

Handles probability smoothing for a given grammar

Breaking this out into its own section to make changing this at
a later point easier

"""


import math


def smooth_grammar(grammar, ip_total, ep_total):
    """
    Responsible for applying probability smoothing to the grammar

    Will update the grammar and return it with the levels assicated with each transition

    --The input grammar has the format (example for ngram=4)
    
    .. code-block:: python
        
        {
            'aaa': {       //the starting charaters
                ip_count: 5,    //the number of times they have shown up in the ip (begining)
                ep_count: 3,    //the number of times they have shown up in the ep (end)
                cp_count: 100,  //the number of times they have shown up total in passwords (for cp)
                next_letter:{   //the next letter for cp
                    a:5         //represents the cp 'aaaa' with the count of the times that cp has been seen
                    b:12,       //represents the cp 'aaab'
                    ...,
                },
            },
            ...,
        }

    --The output grammar will have the following format (example for ngram=4)
    
    .. code-block:: python
    
        {
            'aaa': {       //the starting charaters
                ip_count: 5,    //the number of times they have shown up in the ip (begining)
                ip_level: 2,    //the smoothed level for the ip
                ep_count: 3,    //the number of times they have shown up in the ep (end)
                ep_level: 5,    //The smoothed level for the ep
                cp_count: 100,  //the number of times they have shown up total in passwords (for cp)
                next_letter:{   //the next letter for cp
                    a:(1,5)       //represents the cp 'aaaa' with smoothed level 1, seen 5 times
                    b:(0,12),     //represents the cp 'aaab' with smoothed level 0, seen 12 times
                    ...,
                },
            },
            ...,
        }

    """

    # Set the level adjust factor for smoothing
    #
    # May eventually move this to a configurable options
    #
    level_adjust_factor = {
        'ip':250,
        'cp':2,
        'ep':250,
        }

    # Loop through the top (ngram-1) list that has IP, EP and the next letter transition
    for starting_letters in grammar.keys():

        # Saving a pointer to the dic to clean up code
        index = grammar[starting_letters]

        # Save the IP info
        index['ip_level'] = _calc_level(index['ip_count'], ip_total, level_adjust_factor['ip'])

        # Save the EP info
        index['ep_level'] = _calc_level(index['ep_count'], ep_total, level_adjust_factor['ep'])

        # Now loop through all the conditional probabilities
        for cond_prob in index['next_letter']:
            # Saving a pointer to the dic to clean up code
            cp_index = index['next_letter'][cond_prob]

            saved_level = _calc_level(cp_index, index['cp_count'], level_adjust_factor['cp'])

            index['next_letter'][cond_prob] = (saved_level, cp_index)


def smooth_length(ln_lookup, ln_counter, max_level = 10):
    """
    Responsible for smoothing the length info

    Given a list of the lengths with their associated counts, return a list
    of the lengths with the (level, count)

    """

    # Used to normalize the length level costs so at least one lenght
    # has a level cost of 0.
    min_level = max_level

    # Smooth the level lengths
    for length, count in enumerate(ln_lookup):

        # Calculate the level
        try:
            level = _calc_level(count, ln_counter, 1)

            # Update level cost based on length
            # Using a length cost factor of 1 so that for every
            # character, the level goes up by one. Leaving in
            # the part to modify the level_cost here to make
            # updating it on the fly easier.
            level_cost = 1
            level += length * level_cost

            # Take the floor of the level to avoid levels such as 3.5
            # Not necessary for a cost of 1, but leaving this in here
            # in case I make the level cost have a fraction in it.
            level = int(level)

            if level < min_level:
                min_level = level

            ln_lookup[length] = (level, count)

        # Will throw a divide by 0 exception if there is length items
        except ZeroDivisionError:
            # Set the length to be the max_level
            # DevNote: Creating length based exclusion rules should be the
            #          responsibility of the guess generator. The trainer
            #          should just say that this length is really unlikely
            ln_lookup[length] = (max_level,0)

    # Normalize length to have at least one be at 0 level
    for length, count in enumerate(ln_lookup):
        new_level = ln_lookup[length][0] - min_level

        # With the length cost added on, some of the levels might
        # be above max_level, so reduce them to be max_level
        new_level = min(new_level, max_level)

        ln_lookup[length] = (new_level, count)


def _calc_level(base_count, total_count, level_adjust_factor, max_level = 10):
    """
    Applies the probability smoothing levels

    Note, if total count is 0 will intentionally raise a divide by 0 error

    Returns the calculated level

    """

    # Calculate the probi values
    probi = base_count / total_count
    probi *= level_adjust_factor
    probi += 0.00000000001

    # Now calculate the level
    level = math.floor(-1 * math.log(probi))

    # Perform sanity checking of the level to get it to fall
    # within the appropriate bounds
    if level > max_level:
        level = max_level
    # Sometimes this can give an item -1 or -2 vs the base 0 so correct that
    elif level < 0:
        level = 0

    return level
