#!/usr/bin/env python3


"""
Name: Status Report
Description: Responsible for tracking statistcs and printing status reports
"""


import sys
import datetime
import time


class StatusReport:
    """
    Used to keep track of a gussing session's status
    """

    def __init__(self):
        """
        Basic initialization function

        Inputs:
            None

        Returns:
            StatusReport
        """

        # Total number of parse_trees processed so far
        self.num_parse_trees = 0

        # Total number of guesses made so far
        self.num_guesses = 0

        # Current pt_item that is being processed
        self.pt_item = {}

        # Probability Coverage
        # See https://github.com/lakiw/pcfg_cracker/issues/9
        self.probability_coverage = 0

        # The total time generating guesses in previoius sessions (seconds)
        self.past_guessing_time = 0

        # The start time of the current run
        self.start_time = time.perf_counter()

    def print_status(self, pcfg):
        """
        Prints a status report to stderr

        Inputs:
            pcfg: The PCFG grammar Object

        Returns:
            None
        """

        # Banner
        print("Status Report:",file=sys.stderr)

        # Need to copy pt_item so it doesn't get modified while being printed
        static_pt_item = self.pt_item

        # Quick bail out if the PCFG is still initalizing and hasn't started
        # cracking yet
        if not static_pt_item:
            print("Haven't started generating guesses yet",file=sys.stderr)
            return

        status_item = pcfg.get_status(static_pt_item['pt'])

        # Check if it is an OMEN based guessing session or not
        is_omen = False
        if status_item['pt'][0][0] == 'M':
            is_omen = True

        # Past Guessing Status
        if is_omen:
            print("Total Guesses (Approximate): " + "{:,}".format(self.num_guesses + status_item['guess_num']),file=sys.stderr)
        else:
            print("Total Guesses (Approximate): " + "{:,}".format(self.num_guesses),file=sys.stderr)

        # Time spent generating guesses
        total_time, current_session_time = self._calc_running_time()

        print("Total Guessing Time: ", end='', file=sys.stderr)
        self._print_time(total_time)
        print("Session Guessing Time: ", end='', file=sys.stderr)
        self._print_time(current_session_time)

        print("Number of Pre-Terminals (Rules) Processed: " + "{:,}".format(self.num_parse_trees),file=sys.stderr)
        print("Probability Coverage: " + str(self.probability_coverage),file=sys.stderr)

        # Current Guessing Status
        print("Current Probability of Guesses: " + str(static_pt_item['prob']),file=sys.stderr)
        print("Current Pre-Terminal (Rule): " + str(static_pt_item['pt']),file=sys.stderr)

        # Prints out OMEN Info:
        if is_omen:
            print("Using OMEN to Generate Guesses",file=sys.stderr)
            print("OMEN Level: " + str(status_item['level']),file=sys.stderr)
            print("Keyspace for Level:           " + "{:,}".format(status_item['keyspace']),file=sys.stderr)
            print("Current Position in Keyspace: " + "{:,}".format(status_item['guess_num']),file=sys.stderr)

        # Print out info for non-OMEN guess generation
        else:
            self._print_guess(status_item['first_guess'])

    def _print_guess(self, guess):
        """
        Prints out an example guess from the current pre-terminal to stderr for status report

        Need to have error handling which is why it was split into its own
        function

        Inputs:
            guess: The guess to print out

        Returns:
            None

        """
        try:
            print("Example Guess: " + guess, file=sys.stderr)

        # While I could silently replace/ignore the Unicode character for now
        # I want to know if this is happening
        except UnicodeEncodeError as msg:
            print("Unable to print example guess due to Unprintable Character(s)",file=sys.stderr)
        except Exception as msg:
            print('',file=sys.stderr)
            print("Weird error trying to print status.",file=sys.stderr)
            print(f"{msg}",file=sys.stderr)

    def _print_time(self, session_time):
        """
        Prints the Days, Hours, Minutes and Seconds from a total number of seconds to stderr

        Used for formating the status output

        Inputs:
            session_time: Number of seconds this has been running

        Returns:
            None
        """

        days = session_time // (24 * 3600)
        remainder = session_time % (24 * 3600)
        hours = remainder // 3600
        remainder %= 3600
        minutes = remainder // 60
        remainder %= 60
        seconds = remainder

        # Tell it to print out Hours, Minutes if there was a field printed
        # before this
        print_rest = False

        if days != 0:
            print_rest = True
            if days == 1:
                print(str(days) +" Day, ", end='', file=sys.stderr)
            else:
                print(str(days) +" Day, ", end='', file=sys.stderr)

        if print_rest or hours != 0:
            print_rest = True
            if hours == 1:
                print(str(hours) +" Hour, ", end='', file=sys.stderr)
            else:
                print(str(hours) +" Hours, ", end='', file=sys.stderr)

        if print_rest or minutes != 0:
            print_rest = True
            if minutes == 1:
                print(str(minutes) +" Minute, ", end='', file=sys.stderr)
            else:
                print(str(minutes) +" Minutes, ", end='', file=sys.stderr)

        if seconds == 1:
            print(str(seconds) +" Second", file=sys.stderr)
        else:
            print(str(seconds) +" Seconds", file=sys.stderr)

    def _calc_running_time(self):
        """
        Returns the total time (in seconds) a cracking session has been actively running

        Putting this in a function to make it easier to poll
        Note, this will round down to the nearest second

        Inptus:
            None

        Returns:
            (total_time, current_session)

            total_time : The total time cracking sessions have been run (seconds)

            current_session : The time in the current session (since load) (seconds)
        """

        current_session = time.perf_counter() - self.start_time
        total_time = self.past_guessing_time + current_session

        return int(total_time), int(current_session)

    def print_help(self):
        """
        Prints out help info for the status report to stderr

        Inputs:
            None

        Returns:
            None
        """

        print("Status Report Help", file=sys.stderr)
        print("----------------------", file=sys.stderr)
        print("Fields:", file=sys.stderr)
        print("    Total Guesses:", file=sys.stderr)
        print("        Overview: Approximate number of guesses generated so far", file=sys.stderr)
        print("        Misc: Not 100% accurate as this is updated periodically", file=sys.stderr)
        print("", file=sys.stderr)
        print("    Total Guessing Time:", file=sys.stderr)
        print("        Overview: Total time spent generating guesses", file=sys.stderr)
        print("        Misc: This includes time from previous run if you have", file=sys.stderr)
        print("              restored/loaded this guessing session", file=sys.stderr)
        print("", file=sys.stderr)
        print("    Session Guessing Time:", file=sys.stderr)
        print("        Overview: Time spent this session generating guesses", file=sys.stderr)
        print("        Misc: This does not include previous time if you loaded", file=sys.stderr)
        print("              this guessing session. If this is your first run,", file=sys.stderr)
        print("              then this should match total guessing time.", file=sys.stderr)
        print("", file=sys.stderr)
        print("    Number of Pre-Terminals:", file=sys.stderr)
        print("        Overview: Can be viewed as the number of rules that have", file=sys.stderr)
        print("                  have been processed so far", file=sys.stderr)
        print("        Misc: Mostly for debugging. Do not expect to exhaust", file=sys.stderr)
        print("              all the rules as there are likely billions+", file=sys.stderr)
        print("", file=sys.stderr)
        print("    Probability Coverage:", file=sys.stderr)
        print("        Overview: Expected chance that a password would be", file=sys.stderr)
        print("                  guessed at this point", file=sys.stderr)
        print("        Misc: This is a fuzzy metric since it assumes that the", file=sys.stderr)
        print("              target password follows the same probability", file=sys.stderr)
        print("              distribution as the training set and that the grammar", file=sys.stderr)
        print("              is perfect.", file=sys.stderr)
        print('              Narrator: "The grammar was not perfect"', file=sys.stderr)
        print("", file=sys.stderr)
        print("              Can be useful to determine if this PCFG run is", file=sys.stderr)
        print("              worth continuing or not.", file=sys.stderr)
        print("", file=sys.stderr)
        print("              Much like Zeno's paradox, this percentage will increase", file=sys.stderr)
        print("              slower and slower as a guessing session continues as", file=sys.stderr)
        print("              each guess has a lower probability than the previous.", file=sys.stderr)
        print("", file=sys.stderr)
        print("    Current Probability of Guesses:", file=sys.stderr)
        print("        Overview: According to the PCFG, the probability of the", file=sys.stderr)
        print("                  current guess being a password", file=sys.stderr)
        print("", file=sys.stderr)
        print("    Current Pre-Terminal:", file=sys.stderr)
        print("        Overview: The current rule being processed", file=sys.stderr)
        print("                  -Rules are processed left to right", file=sys.stderr)
        print("                  -Pairs of rule type and index into the rule", file=sys.stderr)
        print("                  -Index starts at 0 with lower being more probable", file=sys.stderr)
        print("", file=sys.stderr)
        print("        Rule Type Key:", file=sys.stderr)
        print('              "M": OMEN (Ordered Markov ENumerator). Basically smart bruteforce', file=sys.stderr)
        print('              "An": (A)lpha string (Letter) of length "n"', file=sys.stderr)
        print('              "Cn": (C)apitalization mangling for length "n"', file=sys.stderr)
        print('              "Dn": (D)igit string (number) of length "n"', file=sys.stderr)
        print('              "Y1": (Y)ear, four digits, (e.g. 2019)', file=sys.stderr)
        print('              "Kn": (K)eyboard walk of length "n"', file=sys.stderr)
        print('              "X1": Conte(x)t sensitive replacement, (e.g. "<3")', file=sys.stderr)
        print('              "On": (O)ther replacement. Special characters, (e.g. !@#$)', file=sys.stderr)
        print("", file=sys.stderr)
        print("    Example Guess:", file=sys.stderr)
        print("        Overview: This is the first guess that will be generated for", file=sys.stderr)
        print("                  the current rule.", file=sys.stderr)
        print("        Misc: Will not display for OMEN guess generation", file=sys.stderr)
        print("", file=sys.stderr)
        print("              An error message may display instead if the guess can", file=sys.stderr)
        print("              not be printed to terminal due to character encoding issues.", file=sys.stderr)
        print("", file=sys.stderr)
        print("    Various OMEN Status Outputs:", file=sys.stderr)
        print("        Overview: As a guessing session goes on, the keyspace for", file=sys.stderr)
        print("                  each Omen guess generation grows, so it is helpful", file=sys.stderr)
        print("                  to know how long it will be until other rule based", file=sys.stderr)
        print("                  guessing will resume.", file=sys.stderr)
        print("", file=sys.stderr)
        print("                  Other OMEN status outputs can be useful for debugging", file=sys.stderr)
        print("                  and research purposes.", file=sys.stderr)

    def update_save_config(self, save_config):
        """
        Updates the config file for saving/loading sessions for the status
        output, with current status

        Inputs:
            save_config: A configparser object to save the current state

        Returns:
            None
        """

        save_config.set('session_info', 'num_guesses', str(self.num_guesses))
        save_config.set('session_info', 'num_parse_trees', str(self.num_parse_trees))
        save_config.set('session_info', 'probability_coverage', str(self.probability_coverage))
        save_config.set('session_info', 'last_updated', datetime.datetime.now().isoformat())
        total_time, current_session_time = self._calc_running_time()
        save_config.set('session_info', 'running_time', str(total_time))

    def load(self, save_config):
        """
        Loads data for the status output from a previously saved session

        Inputs:
            save_config: A configparser object to load the current state

        Returns:
            None
        """
        self.num_guesses = save_config.getint('session_info', 'num_guesses')
        self.num_parse_trees = save_config.getint('session_info', 'num_parse_trees')
        self.probability_coverage = save_config.getfloat('session_info', 'probability_coverage')
        self.past_guessing_time = save_config.getint('session_info','running_time')
