#!/usr/bin/env python3


"""
Used to create and increment guesses for a particular length + IP + target level with OMEN
"""


class GuessStructure:
    """
    Will attempt to create a guess for a particular length + IP + target level
    Based on OMEN

    Seperating this out to clean up the markov_cracker code
    """

    def __init__(self, cp, max_level, ip, cp_length, target_level, optimizer):
        """
        Initializes the guess structure

        Inputs:
            cp: The conditional probability structure

            max_level: The maximum OMEN level a CP can be to be added. This
            is used as a quick bail out. Initially this will be equal to
            target_level, but it is a variable to make saving/loading
            a guess structure from file easier.

            ip: The Initial probability: (Starting NGRAM)

            cp_length: The number of conditional probability ngrams to
            add after the IP.

            target_level: The OMEN level to generate a gues for

            optimizer: A TMTO optimizer to cache OMEN generated results
            to make future guesses faster.

        Returns:
            GuessStructure
        """

        # If this is the first guess
        self.first_guess = True

        # The CP structures
        self.cp = cp

        # The maximum level an item can be
        self.max_level = max_level

        # The IP string to use
        self.ip = ip

        # The length of the IP to use
        self.ip_length = len(self.ip)

        # The number of cps to add after the IP
        self.cp_length = cp_length

        # The target level for this item
        self.target_level = target_level

        # Initialize the parse_tree
        self.parse_tree = []

        # The optimizer
        self.optimizer = optimizer

    def next_guess(self):
        """
        Get the next guess for this guess structure (aka level + IP)
        Returns None if no valid guess is left

        Inputs:
            None:

        Returns:
            guess: The next guess that can be generated for this Markov structure.
            Aka the OMEN target level and initial IP.

            None: If no more guesses can be generated
        """
        # First Guess
        if not self.parse_tree:
            self.parse_tree = self._fill_out_parse_tree(self.ip,self.cp_length, self.target_level)
            if not self.parse_tree:
                return None

            return self._format_guess()

        # Every guess after the first guess

        # Shortcut deal with the last item
        last_item = self.parse_tree[-1]
        if last_item[2] + 1 < len(self.cp[last_item[0]][last_item[1]]):
            self.parse_tree[-1][2] += 1
            return self._format_guess()

        # Pop the last element off
        element = self.parse_tree.pop()

        # Quick bail out since there is nothing else to increment,
        # (the parse tree was only one cp long)
        if not self.parse_tree:
            return None

        # The number of CP we need to fill in after this depth
        req_length = 1

        # The number of levels we have to fill for the final password from this depth
        req_level = element[1] + self.parse_tree[-1][1]

        # Now loop through all the possible items at this depth
        while self.parse_tree:

            # Simplifying some of the code by assigning this pointer
            last_item = self.parse_tree[-1]

            # Start it out by incrementing the index of the last item
            last_item[2] += 1

            # The level we are workng from for this current depth
            depth_level = last_item[1]

            # Levels for depth start off at the max and go down to 0
            while True:

                while last_item[2] < len(self.cp[last_item[0]][depth_level]):
                    new_ip = element[0][0:-1] + self.cp[last_item[0]][depth_level][last_item[2]]
                    new_elements = self._fill_out_parse_tree(new_ip, req_length, req_level-depth_level)

                    # Found a match!!
                    if new_elements is not None:
                        self.parse_tree += new_elements
                        return self._format_guess()

                    # Otherwise, increase the index and try again at this depth level
                    last_item[2] += 1

                # No lower level, exit out of this
                if depth_level == 0:
                    break

                # Try a lower level
                cp_index, depth_level = self._find_cp(last_item[0], depth_level-1, 0)

                # No lower level, exit
                if cp_index is None:
                    break

                last_item[1] = depth_level

                # Reset the index to the start
                last_item[2] = 0

            # No match, go deeper
            element = self.parse_tree.pop()
            req_length += 1

            if self.parse_tree:
                req_level += self.parse_tree[-1][1]

        return None

    def _format_guess(self):
        """
        Takes the parse tree and the IP and generates an actual guess to return

        Inputs:
            None

        Returns:
            guess: The string guess to print out
        """

        guess = self.ip
        for item in self.parse_tree:
            guess += self.cp[item[0]][item[1]][item[2]]

        return guess

    def _fill_out_parse_tree(self, ip, length, target_level):
        """
        Fills out a parse tree for OME given an IP, length and
        target level.

        Inputs:
            ip: The initial probability Ngram to start with

            length: The length of the guess to generate

            target_level: The target level to generate OMEN strings for

        Returns:
            result: the parse tree for this OMEN generation

            None: If no valid parse tree exists for the IP/length/target level
        """
        if length == 1:
            cp_index, cp_level = self._find_cp(ip, target_level, target_level)
            if cp_index is None:
                return None
            return [[ip, cp_level, 0]]

        ###--Check to see if the optimizer has an answer
        if length <= self.optimizer.max_length:
            found, result = self.optimizer.lookup(ip, length, target_level)

            # If a previous result was stored in the optimizer, return it
            if found:
                return result

        cur_level = target_level

        # Need to save these off for updating the optimizer
        optimize_level_target = target_level

        while cur_level >= 0:
            # Find the top level CP for the current level
            cp_index, cp_level = self._find_cp(ip, cur_level, 0)
            if cp_index is None:
                if length <= self.optimizer.max_length:
                    self.optimizer.update(ip, length, optimize_level_target, None)
                return None

            next_length = length - 1
            top_index = len(cp_index)
            cur_index = 0
            while cur_index < top_index:
                next_ip = ip[1:]+cp_index[cur_index]
                working_parse_tree = self._fill_out_parse_tree(
                    ip = next_ip,
                    length = next_length,
                    target_level = target_level - cp_level
                    )

                if working_parse_tree is not None:
                    result = [[ip, cp_level, cur_index]] + working_parse_tree
                    if length <= self.optimizer.max_length:
                        self.optimizer.update(ip, length, optimize_level_target, result)
                    return result

                cur_index += 1

            # Need to go one less than the returned cp level so we don't loop forever
            cur_level = cp_level - 1

        if length <= self.optimizer.max_length:
            self.optimizer.update(ip, length, optimize_level_target, None)
        return None

    def _find_cp(self, ip, top_level, bottom_level):
        """
        Returns a pointer to the highest possible transition in the format of
        [ip, level, index], for the next conditional probability ngram

        Inputs:
            IP: The initial probability ngram to work from

            top_level: The highest OMEN level the CP can be

            bottom_level: The lowest OMEN level the CP can be. Useful
            for identifying the last CP in a string.

        Returns:
            (CP_Pointer, top_level)

            CP_Pointer: A pointer to the hightest level CP possible

            top_level: The remainder OMEN level for future CP ngrams to use
        """

        # Quick bail out if the ip is not present
        if ip not in self.cp:
            return None, None

        # Set the maximum level we're going to check
        if self.max_level < top_level:
            top_level = self.max_level

        # Attempt to find the highest transition possible
        while top_level >= bottom_level:
            if top_level in self.cp[ip]:
                return self.cp[ip][top_level], top_level

            top_level -= 1

        return None, None
