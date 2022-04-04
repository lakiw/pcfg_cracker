#!/usr/bin/env python3


"""
Tries to detect L33t mangling in the training dataset

Aka P@ssw0rd = password

This relies on the multi-word detector to identify base/multi words

General Approach:
1)  If the alpha string is a base or multi word, exit
2)  If alpha string is not a base word (too short, or not in dictionary)
    convert one common replacement if it exists. Start with replacements
    between two alpha strings first. Aka p@ss1 -> "pass"1. If no replacement
    can be found, exit
3)  Attempt to parse the expanded alpha string and see if it is a base word
    or multiword. If it is, then return it as a l33t replacement
4)  If not, go back to step 2 and coninue. For example now try
    pass1 -> passl

The above will likely get a bit more complicated if/when I add support for
multiple leet conversions. Aka "a" can be transformed as "4" or "@"

This first PoC will just look at the most common replacement

The reason to slowly try to unmangle l33t word and start in the middle is
to deal with people adding digits/special to the end of their password.
For example: 1passw0rd or passw0rd1

In that case, we want to "unmangle" the 0 but leave the "1" alone

Note, this is very much mapped to ASCII/UTF-8 l33t mapping. Will likely
have problems with other encoding schemes.

"""


class LeetDetector:
    """
    Attempts to identify l33t mangling

    Creating this as a class in case I want to add more advanced features later
    """

    def __init__(self, multi_word_detector):
        """
        Initialize the Leet detector

        Variables:
            multi_word_detector: A previously trained multi word detector

        """

        self.multi_word_detector = multi_word_detector

        ## A mapping of possible l33t replacements to check
        #
        # Note: Currently there is no support for multi letter l33t replacements
        # For example '|-|' = "h".
        # I don't think this happens too often so that is a future improvement
        # to look into.
        #
        # Also note, while eventually I'd like to check all possible
        # leet replacements, and I included multiple leet replacements below,
        # the current PoC only checks the first item.
        #
        # Checking multiple replacements is a higher priority target simply
        # because '1' can map to both 'L', and 'i', fairly frequently.
        #
        self.replacements = {
            '4':['a','h'],
            '@':['a'],
            '8':['b'],
            '3':['e'],
            '6':['g','b'],
            '1':['l','i'],
            '0':['o'],
            '9':['g','q'],
            '5':['s'],
            '7':['t'],
            'x':['%'],
            '2':['z','e'],
            '$':['s']
        }

    def _unleet(self,password):
        """
        Attempt to return the base word with l33t modifications replaced with
        the underlying characters
        """

        run = False
        start = -1
        for i, x in enumerate(password):
            if x.isalpha():
                if not run:
                    start = i
                run = True

            else:
                if run:
                    if x in self.replacements:
                        return password[:i] + self.replacements[x][0] + password[i+1:]

                    elif start != -1:
                        start_char = password[start-1]
                        if start_char in self.replacements:
                            return password[:start-1] + self.replacements[start_char][0] + password[start:]
                    else:
                        return None
        return None

    def _find_leet(self, password):
        """
        Find if leet replacements were made

        TOD: Not implimented/tested. This is temporary code.

        """
        working_pw = self._unleet(password.lower())
        if not working_pw:
            return None
        else:

            cur_run = []
            for x in password:
                if x.isalpha():
                    cur_run.append(x)
                else:
                    if cur_run:
                        found, base_word = self.multi_word_detector.detect_multiword("".join(cur_run))
                        if found:
                            print (password)
                            print (working_pw)
                            print()

                        return None

        return None

    def parse(self, password):
        """
        Detects if the input has l33t replacement

        Variables:
            password: Password to parse

        Returns:
            None: If no l33t replacements were found

            {
                '1npu7':{
                    "word":'input',
                    "replacements":{
                        "1":'i',
                        "7":'t'
                    },
                    "strategy": "unknown"
                }
            }
        """
        leet = self._find_leet(password)

        if leet:
            return True, leet

        return False, None
