#!/usr/bin/env python3


"""
Collections of functions to evalute a password against a previously
trained OMEN model
"""


from collections import Counter


def find_omen_level(omen_trainer, password):
    """
    Finds the OMEN level for an input password

    Input Variables:
        omen_trainer: A previously trained OMEN dataset
        password: The password to evaluate

    Return Values:

        level: An INT representing the OMEN level of the trained password
        Returns -1 if the password can't be parsed

    """

    # Reject if too short or too long
    pw_len = len(password)
    if pw_len < omen_trainer.min_length or pw_len > omen_trainer.max_length:
        return -1

    # Length of ngram
    ngram = omen_trainer.ngram

    # Using KeyError exception to catch if a length or ngram is not
    # present in the training data. Also helps to avoid having to check if
    # a letter is present in the alphabet.
    #
    try:
        ## Find the length
        # the OMEN length value is 0 indexed so need to subtract 1 from len
        ln_level = omen_trainer.ln_lookup[pw_len - 1][0]

        ## Find the IP (initial point) level to start the chain
        #
        # Note: the IP is len ngram - 1
        #
        chunk = password[0:ngram-1]
        chain_level = omen_trainer.grammar[chunk]['ip_level']

        ## Add the levels of all the ngram chain transisions
        #
        end_pos = ngram

        while end_pos <= pw_len:
            chunk = password[end_pos - ngram:end_pos]
            chain_level += omen_trainer.grammar[chunk[:-1]]['next_letter'][chunk[-1]][0]
            end_pos += 1

        ## Return final level of length level + all the transition levels
        return ln_level + chain_level

    # A value wasn't found in the trained OMEN grammar
    except KeyError:
        return -1


def _rec_calc_keyspace(omen_trainer, level, length, ip):
    """
    Used to recusivly calculate the keyspace for an OMEN level

    Input Variables:
        omen_trainer: A previously trained OMEN dataset
        Note: This function will modify the OMEN dataset to cache
        some of the keyspace calculations for the grammar

        level: The remaining level that needs to be exhausted for this parse

        length: The length of the remaining "password" to generate

        ip: The starting ip that this password chunk will have

    Return Values:

        current_keyspace: (INT) A count of the keyspace for this level, length, ip

    """

    # Initialize the keyspacecache if not created already for this ip
    if 'keyspace_cache' not in omen_trainer.grammar[ip]:
        omen_trainer.grammar[ip]['keyspace_cache'] = {}

    # Initiliaze the length cache if not created
    if length not in omen_trainer.grammar[ip]['keyspace_cache']:
        omen_trainer.grammar[ip]['keyspace_cache'][length] = {}

    # Look for a cached ip + length + level count
    if level in omen_trainer.grammar[ip]['keyspace_cache'][length]:
        # Return the cached value
        return omen_trainer.grammar[ip]['keyspace_cache'][length][level]

    # Value was not cached so calculate it
    omen_trainer.grammar[ip]['keyspace_cache'][length][level] = 0

    # Calculate if the last letter
    if length == 1:
        for last_letter, letter_level in omen_trainer.grammar[ip]['next_letter'].items():
            if letter_level[0] == level:
                omen_trainer.grammar[ip]['keyspace_cache'][length][level] += 1

    # Not last letter so need to do it recursivly
    else:
        for last_letter, letter_level in omen_trainer.grammar[ip]['next_letter'].items():
            if letter_level[0] <= level:
                omen_trainer.grammar[ip]['keyspace_cache'][length][level] += _rec_calc_keyspace(omen_trainer, level - letter_level[0], length - 1, ip[1:] + last_letter)

    return omen_trainer.grammar[ip]['keyspace_cache'][length][level]


def calc_omen_keyspace(omen_trainer, max_level = 18, max_keyspace = 10000000000):
    """
    Finds the keyspace for OMEN levels

     Variables:
        omen_trainer: A previously trained OMEN dataset
        Note: This function will modify the OMEN dataset to cache
        some of the keyspace calculations for the grammar

        max_level: (INT) The maximum OMEN level to calculate keyspace
        Note: Default of 18 was figured off the RockYou dataset
        as less than 5% of passwords were of a higher calculated
        level. Note this is biased on training and evaluating off
        of same dataset so in real life my gut feeling would be
        something like 10% would be higher than 18. Still the
        keyspace grows so large that calculating it isn't worth it
        
        max_keyspace: (INT) The maximum keyspace to search. This also is
        a cut-off for when to stop calculating the keyspace. The
        reasoning for this was that too large of a keyspace there
        was memory issues when running the training in a Windows
        cmd prompt. Also, it's unlikely that a super large keyspace
        OMEN level would actually be employed in a PCFG style cracking
        session.

    Return Values:
        keyspace: An Python Counter object with the levels and associate keyspace

    """

    keyspace = Counter()

    # Calculate keyspace for all levels up to max_level
    for level in range(1,max_level+1):

        # Check each IP to find the starting ngrams that can fit the level
        for ip, ip_info in omen_trainer.grammar.items():
            level_minus_ip = level - ip_info['ip_level']

            # Note, length will always have a level cost of at least one
            if level_minus_ip > 0:

                # Check each length to see if it might be valid for the max_level
                # Note: length_info is actually a (level, count) set
                for length, length_info in enumerate(omen_trainer.ln_lookup):

                    # Since ln_lookup is 0 indexed
                    length += 1

                    # Skip lengths that will not have valid ngram transitions
                    if length <= omen_trainer.ngram:
                        continue

                    if length_info[0] <= level_minus_ip:

                        keyspace[level] += _rec_calc_keyspace(
                                                omen_trainer,
                                                level_minus_ip - length_info[0],
                                                length - omen_trainer.ngram + 1,
                                                ip)
                        
                        # Break if the keyspace is growing too much
                        if keyspace[level] > max_keyspace:
                            return keyspace

        print("OMEN Keyspace for Level : " + str(level) + " : " + str(keyspace[level]))

    return keyspace
