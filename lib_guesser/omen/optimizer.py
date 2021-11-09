#!/usr/bin/env python3


"""

Uses time memory trade off to speed up guess generation by caching previous results for
filling out guesses for level + length + starting string combinations

"""


class Optimizer:
    """
    Contains all the logic to speed up guess generation by using tmto tricks

    Creating this as a class so I can easily pass it around
    """

    def __init__(self, max_length):
        """
        Initializes the optimizer

        Inputs:
            max_length: The maximum length of strings to optimize. Increasing this
            increases memory requirements
        """

        self.max_length = max_length

        # The grammar lookup
        #
        # Will be a list indexed on the length
        # so length 1 will be at position 1
        # dictionary lookups will be of the format
        # {
        #    'ip_ngram':{
        #         'level': 'first result',
        #         'level2': 'first result',
        #         ...
        #    },
        #   'ip_ngram2':{
        #         'level':'first result',
        #    }
        #    ...,
        # }
        #
        # Example (assuming length = 4):
        # {
        #   'abc':{
        #       '0':[[abc, 0],[bcd,0], [cde, 0], [def, 0]],
        #       '5[[abc, 1],[bc1,1], [c12, 2], [123, 1]],
        #   },
        # }
        self.tmto_lookup = []
        for i in range(self.max_length + 1):
            self.tmto_lookup.append({})

    def lookup(self, ip_ngram, length, target_level):
        """
        Look up a previous result

        Inputs:
            ip_ngram: The initial starting point for the word

            length: The length of the word

            target_level: The target OMEN level of the word to generate

        Returns:
            (if_found, parse_tree)

            if_found: True if a result was cahced, False if it was not

            parse_tree: The first parse tree to match the lookup criteria.
            Returns None if no parse tree matches it
        """
        try:
            return True, self.custom_copy( self.tmto_lookup[length][ip_ngram][target_level] )
        except KeyError:
            return False, None

    def update(self, ip_ngram, length, target_level, parse_tree):
        """
        Updates the optimizer with a found result

        Inputs:
            ip_ngram: The inital pointer (ngram) to start the word

            length: The length of the word to generate

            target_level: The target OMEN level the word needs to be

            parse_tree: The parse tree of the found result
        """

        ##--If we haven't seen this ip_ngram for this length before
        if ip_ngram not in self.tmto_lookup[length]:
            self.tmto_lookup[length][ip_ngram] = {}

        self.tmto_lookup[length][ip_ngram][target_level] = self.custom_copy(parse_tree)

    def custom_copy(self, input_list):
        """
        Copies the first order values of the list to a new list

        Using this because copy.deepcopy is overkill, (and slow) for what we want

        Inputs:
            input_list: The list to copy

        Returns:
            copied_list: A copy of the list
        """

        if input_list:
            return [x[:] for x in input_list]
        return None
