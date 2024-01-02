#!/usr/bin/env python3


"""
Name: PCFG_Cracker Cracking Management Code

Description: Manages a cracking session

Making this a class to help support different guess generation
modes in the future

"""


import sys
import time
import threading # Used only for the "check for user input" threads

# Local imports
from .priority_queue import PcfgQueue
from .status_report import StatusReport


class CrackingSession:
    """
    Used to manage a password cracking session
    """

    def __init__(self, pcfg, save_config, save_filename):
        """
        Basic initialization function
        """

        # Used to save a session's status to disk
        self.save_config = save_config
        self.save_filename = save_filename

        # Initalize the status report class for providing debugging and
        # status information
        self.report = StatusReport()

        # Save the grammar for easy reference
        self.pcfg = pcfg

        # The guessing session modes
        self.mode = "priority_queue"

        # The actual Priority queue. Will be defined when run() is called
        self.pqueue = None

    def run(self, load_session = False, limit = None):
        """
        Starts the cracking session and starts generating guesses
        """

        ## New session
        #
        if not load_session:

            # Initalize the priority queue
            self.pqueue = PcfgQueue(self.pcfg)

            # Save the inital restore file
            self._save_session()

        ## Load session described in previously saved configfile
        #
        else:
            print ("Restoring saved progress...",file=sys.stderr)
            # Update the status report so things like probability coverage
            # reflect what was done before
            self.report.load(self.save_config)

            # Update the priority queue to skip over pre-terminals that have
            # been guessed previously
            self.pqueue = PcfgQueue(self.pcfg, self.save_config)

        print ("Starting to generate password guesses",file=sys.stderr)
        print ("Press [ENTER] to display a status output",file=sys.stderr)
        print ("Press 'q' [ENTER] to exit",file=sys.stderr)

        ## Set up the check to see if a user is pressing a button
        #
        user_thread = threading.Thread(target=keypress, args=(self.report, self.pcfg))
        user_thread.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
        user_thread.start()

        ## Check to see if we are restoring an OMEN session
        #
        if load_session:
            # If true, we need to restart an OMEN guessing session
            if self.save_config.has_option('guessing_info','omen_guess_number'):

                # Create a fake pt_item for the status reports while generating
                # OMEN guesses. Will fill it in when we restore OMEN session
                self.report.pt_item = {
                    'prob': self.save_config.getfloat('guessing_info','max_probability'),
                    'pt':[['M',1,1]],
                    'level':1,
                }

                omen_guess_num = self.save_config.getint('guessing_info','omen_guess_number')
                num_generated_guesses = self.pcfg.restore_omen(omen_guess_num, self.report.pt_item)
                self.report.num_guesses += num_generated_guesses

        # Keep running while the p_queue.next_function still has items in it
        while True:

            # Get the next item from the pqueue
            pt_item = self.pqueue.next()

            # If the pqueue is empty, there are no more guesses to make
            if pt_item is None:
                print ("Done processing the PCFG. No more guesses to generate",file=sys.stderr)
                print ("Shutting down guessing session",file=sys.stderr)
                return

            # Check to see if the program should exit based on user input
            #
            # DevNote: Doing this after we get an item from the pqueue so if
            #          the session shuts down we save the probability of
            #          this item and don't repeat the previous pt that was
            #          popped off and already guessed.
            #
            #          Note: In some rare cases the probability of this pt and
            #          the prev one might be the same in which case both will
            #          be repeated if this session restarts. That's not ideal
            #          but shouldn't have a noticable impact when people restarts
            #          sessions.
            #
            if not user_thread.is_alive():
                print("Saving Session Info",file=sys.stderr)
                self._save_session()
                print("Exiting...",file=sys.stderr)
                break

            # Update stats after the save might occur so we don't double count
            # them when restoring a session
            self.report.num_parse_trees += 1
            self.report.pt_item = pt_item

            try:
                num_generated_guesses = self.pcfg.create_guesses(pt_item['pt'], limit = limit)
                self.report.num_guesses += num_generated_guesses

                # Check if a limit was defined
                if limit:
                    limit = limit - num_generated_guesses
                    if limit <= 0:
                        print("Limit reached. Exiting...",file=sys.stderr)
                        break

                self.report.probability_coverage += pt_item['prob'] * num_generated_guesses

            # The receiving program is no longer accepting guesses
            # Usually occurs after all passwords have been cracked
            except OSError:
                break

        return

    def _save_session(self):
        """
        Saves a gussing session's status to disk
        """

        # Update the status report information
        self.report.update_save_config(self.save_config)

        # Update the guessing session information
        self.save_config.set('guessing_info', 'mode', self.mode)

        # Priority Queue Mode
        if self.mode == "priority_queue":
            self.pqueue.update_save_config(self.save_config)

        #OMEN Guessing is going on so save the current state
        if self.pcfg.omen_exit:
            self.save_config.set(
                'guessing_info',
                'omen_guess_number',
                str(self.pcfg.omen_guess_num)
                )

        # Save the configuration file
        try:
            with open(self.save_filename, 'w') as configfile:
                self.save_config.write(configfile)

        except IOError as error:
            print (error)
            print ("Error writing sessiong restore file: " + self.save_filename)
            return False

        return True


def keypress(report, pcfg):
    """
    Used to check to see if a key was pressed to output program status
    *Hopefully* should work on multiple OSs

    --Simply check user_input_char to see if it is not none
    """
    while True:
        user_input = input()

        # If the main thread died before this is killed off it will throw
        # an error, so check to make sure it is alive before printing items
        # to stderr. Otherwise exit.
        #
        # Adding the time.sleep option because otherwise it'll start trying
        # to print and then error out after the below call. It's a hack, I'll
        # admit it. Probably shouldn't use daemon threads, but Python makes
        # checking for interuptable input a pain from stdin.
        #
        time.sleep(0.1)
        if not threading.main_thread().is_alive():
            return

        try:
            # Display the status report
            report.print_status(pcfg)

            # If the program should exit
            if user_input == 'q':
                print( "",file=sys.stderr)
                print ("Exit command received",file=sys.stderr)
                print ("Will exit after finishing processing current pre-terminal",file=sys.stderr)
                print ("Note: If this takes too long, you can also use CTRL-C",file=sys.stderr)
                print ("      but if you exit early and later restart the session ",file=sys.stderr)
                print ("      it will begin with the previous pre-terminal",file=sys.stderr)
                print ("",file=sys.stderr)
                pcfg.should_exit = True
                return

            # Print the help screen
            elif user_input == 'h':
                print( "",file=sys.stderr)
                report.print_help()

            print( "",file=sys.stderr)
            print("Press [ENTER] to display an updated status output",file=sys.stderr)
            print("Press 'h' [ENTER] for help on what the status reports mean",file=sys.stderr)
            print("Press 'q' [ENTER] to exit",file=sys.stderr)
            print( "",file=sys.stderr)

        # If we can't print to stderr, that implies something weird is happening
        # so exit the user input thread.
        except:
            return
