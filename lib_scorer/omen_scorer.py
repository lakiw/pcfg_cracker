#!/usr/bin/env python3


"""

Responsible for scoring input values according to the OMEN level they would
be generated at.

"""


import os
import sys
import codecs


class OmenScorer:
    """
    Responsible for all OMEN options in the scorer
    Making this a class to bundle all of the OMEN functionality
    """

    def __init__(self, base_directory, encoding, max_omen_level):
        """
        Initalizes OmenScorer and calls to load the OMEN ruleset from disk

        Passes file exceptions back up if they occur
        Eg: if the OMEN ruleset does not exist

        Inputs:
            base_directory: The rule directory to load the OMEN info from

            encoding: The file encoding the OMEN ngrams are saved as

            max_omen_level: The maximum OMEN level to use to attempt to
            parse passwords as.

        Returns:
            OmenScorer
        """

        self.encoding = encoding
        self.max_omen_level = max_omen_level

        self.ip = {}
        self.cp = {}

        # Length is currently hardcoded to 10 to match other aspects of the OMEN
        # generation.
        self.ln = ['10']

        # The size of the ngrams used. Initalize it to -1, will be learned once
        # CPs are loaded in
        self.ngram = -1

        # Load the OMEN stats from disk
        self._load_omen(base_directory)

        # Set the max length an OMEN parsing can be
        self.max_len = len(self.ln) - 1

    def parse(self, password):
        """
        Pases the password and assigns an OMEN score to it

        Inputs:
            password: A string to parse using OMEN

        Returns:
            (int): The OMEN level required to generate the parsed string
            If the string can not be parsed, returns -1
        """

        # Reject if too short or too long
        pass_len = len(password)
        if pass_len < self.ngram or pass_len > self.max_len:
            return -1

        # Using KeyError exception to catch if a length or ngram is not
        # present in the training data. Also helps to avoid having to check if
        # a letter is present in the alphabet.
        try:
            # Find the length cost
            ln_level = self.ln[pass_len]

            # Find the IP (initial point) level to start the chain
            # Note: the IP is len ngram - 1
            chunk = password[0:self.ngram-1]
            chain_level = self.ip[chunk]

            # Add the levels of all the ngram chain transisions
            end_pos = self.ngram

            while end_pos <= pass_len:
                chunk = password[end_pos - self.ngram:end_pos]
                chain_level += self.cp[chunk]
                end_pos += 1

            # Return final level of length level + all the transition levels
            return ln_level + chain_level

        # A value wasn't found in the trained OMEN grammar
        except KeyError:
            return -1

    def _load_omen(self, base_directory):
        """
        Loads the OMEN ruleset from disk

        Note: If an error occurs, it will forward/raise an Exception

        Inputs:
            base_directory: The rule directory the OMEN training will be found

        Returns:
            None
        """

        # Note, realized we don't need to parse the config file since
        # the encoding will be the same as the rest of the PCFG grammar
        # and we can figure out the NGRAM length based on the IP/CPs

        # Load the IP costs
        full_file_path = os.path.join(base_directory, "Omen", "IP.level")

        # Open the file for reading
        try:
            with open(full_file_path, 'r') as file:
                for line in file:
                    line = line.rstrip('\n\r').split('\t')

                    # If there wasn't a line to read. This indicates an error
                    # in the trianing file somewhere
                    if len(line) != 2:
                        print(f"Error parsing {full_file_path}", file=sys.stderr)
                        print("This indicates there was a problem with the training program or the file was corrupted somehow", file=sys.stderr)
                        raise Exception

                    # Will throw a ValueError if not an int
                    level = int(line[0])
                    # Sanity check on the range the level falls in
                    if level < 0 :
                        print(f"Invalid level found parsing {full_file_path}", file=sys.stderr)
                        print(f"Level = {level}", file=sys.stderr)
                        print("This indicates there was a problem with the training program or the file was corrupted somehow", file=sys.stderr)
                        raise Exception

                    # Save the level
                    self.ip[line[1]] = level

        except IOError as msg:
            print("Could not open the config file for the ruleset specified. The rule directory may not exist", file=sys.stderr)
            print(f"Filename: {full_file_path}", file=sys.stderr)
            raise
        except ValueError as msg:
            print(f"Error reading an item from the file: " + full_file_path)
            print("This indicates there was a problem with the training program or the file was corrupted somehow", file=sys.stderr)
            raise
        except Exception as msg:
            print(f"Exception: {msg}", file=sys.stderr)
            raise

        # Load the CP costs
        full_file_path = os.path.join(base_directory, "Omen", "CP.level")

        # Open the file for reading
        try:
            with open(full_file_path, 'r') as file:
                for line in file:
                    line = line.rstrip('\n\r').split('\t')

                    # If there wasn't a line to read. This indicates an
                    # error in the trianing file somewhere
                    if len(line) != 2:
                        print(f"Error parsing {full_file_path}", file=sys.stderr)
                        print("This indicates there was a problem with the training program or the file was corrupted somehow", file=sys.stderr)
                        raise Exception

                    # Will throw a ValueError if not an int
                    level = int(line[0])
                    # Sanity check on the range the level falls in
                    if level < 0 :
                        print(f"Invalid level found parsing {full_file_path}", file=sys.stderr)
                        print(f"Level = {level}", file=sys.stderr)
                        print("This indicates there was a problem with the training program or the file was corrupted somehow", file=sys.stderr)
                        raise Exception

                    # Save the level
                    self.cp[line[1]] = level
                    if self.ngram == -1:
                        self.ngram = len(line[1])

        except IOError as msg:
            print("Could not open the config file for the ruleset specified. The rule directory may not exist", file=sys.stderr)
            print("Filename: " + full_file_path, file=sys.stderr)
            raise
        except ValueError as msg:
            print(f"Error reading an item from the file: {full_file_path}", file=sys.stderr)
            print("This indicates there was a problem with the training program or the file was corrupted somehow", file=sys.stderr)
            raise
        except Exception as msg:
            print(f"Exception: {msg}", file=sys.stderr)
            raise

        # Load the Length costs
        full_file_path = os.path.join(base_directory, "Omen", "LN.level")

        # Open the file for reading
        try:
            with open(full_file_path, 'r') as file:
                for line in file:
                    line = line.rstrip('\n\r')

                    # Will throw a ValueError if not an int
                    level = int(line)
                    # Sanity check on the range the level falls in
                    if level < 0 :
                        print(f"Invalid level found parsing {full_file_path}", file=sys.stderr)
                        print(f"Level = {level}", file=sys.stderr)
                        print("This indicates there was a problem with the training program or the file was corrupted somehow", file=sys.stderr)
                        raise Exception

                    # Save the level
                    self.ln.append(level)

        except IOError as msg:
            print("Could not open the config file for the ruleset specified. The rule directory may not exist", file=sys.stderr)
            print(f"Filename: {full_file_path}", file=sys.stderr)
            raise
        except ValueError as msg:
            print(f"Error reading an item from the file: {full_file_path}", file=sys.stderr)
            print("This indicates there was a problem with the training program or the file was corrupted somehow", file=sys.stderr)
            raise
        except Exception as msg:
            print(f"Exception: {msg}", file=sys.stderr)
            raise
