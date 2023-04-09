#!/usr/bin/env python3


"""

Name: PCFG_Guesser Priority Queue Handling Function

Description: Section of the code that is responsible of outputting all of the
pre-terminal values of a PCFG in probability order. Because of that, this
section also handles all of the memory management of a running password
generation session

"""


import heapq


class QueueItem:
    """
    Wrapper for a parse tree item

    This is so the Priority Queue can determine where to place a parse tree item
    Aka it holds all the "less than", "greater than", "equal to", logic for abs
    parse tree

    Need to have a custom compare functions for use in the priority queue

    I have to do this the reverse of what I'd normally expect
    since the priority queue will output stuff of lower values first.
    Aka if there are two items with probabilities of 0.7 and 0.4, the PQueue
    will by default output 0.4
    """

    def __init__(self, pt_item):
        """
        Initialization function

        Inputs:
            pt_item: A parse tree item, (List)

        Returns:
            QueueItem
        """

        self.pt_item = pt_item

    def __lt__(self, other):
        """
        Reverse of what you'd expect since the priority queue needs to output
        the highest probability guess first. Therefore while this checkes the
        "less then" for this item, it really checks if the item is higher probability
        than what it is being compared against

        Inputs:
            other: Item to compare against

        Outputs:
            True: If the item is higher probability than the other

            False: If the item is lower probability than the other
        """
        return self.pt_item['prob'] > other.pt_item['prob']

    def __le__(self, other):
        """
        Reverse of what you'd expect since the priority queue needs to output
        the highest probability guess first. Therefore while this checkes the
        "less then or equal" for this item, it really checks if the item is higher probability
        or equal than what it is being compared against

        Inputs:
            other: Item to compare against

        Outputs:
            True: If the item is higher probability than the other or equal

            False: If the item is lower probability than the other
        """
        return self.pt_item['prob'] >= other.pt_item['prob']

    def __eq__(self, other):
        """
        Checks if this item is equal to the other item.

        Inputs:
            other: Item to compare against

        Outputs:
            True: If the item and the other are equal probability

            False: If this item and the other item have different probabilities
        """
        return self.pt_item['prob'] == other.pt_item['prob']

    def __ne__(self, other):
        """
        Checks if this item is not equal to the other item.

        Inputs:
            other: Item to compare against

        Outputs:
            True: If this item and the other item have different probabilities

            False: If the item and the other are equal probability
        """
        return self.pt_item['prob'] != other.pt_item['prob']

    def __gt__(self, other):
        """
        Reverse of what you'd expect since the priority queue needs to output
        the highest probability guess first. Therefore while this checkes the
        "greater then" for this item, it really checks if the item is lower probability
        than what it is being compared against

        Inputs:
            other: Item to compare against

        Outputs:
            True: If the item is lower probability than the other

            False: If the item is higher probability than the other
        """
        return self.pt_item['prob'] < other.pt_item['prob']

    def __ge__(self, other):
        """
        Reverse of what you'd expect since the priority queue needs to output
        the highest probability guess first. Therefore while this checkes the
        "greater then or equal" for this item, it really checks if the item is lower probability
        or equal to what it is being compared against

        Inputs:
            other: Item to compare against

        Outputs:
            True: If the item is lower probability or equal to the other

            False: If the item is higher probability than the other
        """
        return self.pt_item['prob'] <= other.pt_item['prob']


class PcfgQueue:
    """
    Main class for handling the classic PCFG next function using a PQueue

    This is the "next" function to use if you want to generate guesses in true
    probability order

    I may make changes to the underlying priority queue code in the future to
    better support removing low probability items from it when it grows too
    large. Therefore I felt it would be best to treat it as a class. Right now
    though it uses the standared python queue HeapQ as its backend
    """

    def __init__(self, pcfg, save_config = None):
        """
        Basic initialization function

        Inputs:
            pcfg: The pcfg grammar object

            save_config: A configparser config, with the following fields
                ["guessing_info"]
                min_probability: float
                max_probability: float

        Returns:
            PcfgQueue
        """

        # Holds the grammar
        self.pcfg = pcfg

        # The actual priority queue
        self.p_queue = []

        # The current highest priority item in the queue. Used for memory
        # management and restoring sessions
        self.max_probability = 1.0

        # The lowest prioirty item is allowed to be in order to be pushed in
        # the queue. Used for memory management
        self.min_probability = 0.0

        # Used for memory management. The maximum number of items before
        # triming the queue.
        # Note: the queue can temporarially be larger than this
        self.max_queue_size = 50000

        # New Guessing Session
        if save_config is None:
            # Initalize the priority queue with all of the initial base
            # structures from the pcfg
            for base_item in self.pcfg.initalize_base_structures():
                heapq.heappush(self.p_queue, QueueItem(base_item))

            return

        # Restore Guessing Session
        self.min_probability = save_config.getfloat('guessing_info', 'min_probability')
        self.max_probability = save_config.getfloat('guessing_info', 'max_probability')

        for base_item in self.pcfg.initalize_base_structures():
            self.restore_base_item(base_item)

    def next(self):
        """
        Pops the top value off the queue and inserts children back

        Inputs:
            None

        Returns:
            pt_item: A parse tree item that was popped off the queue

            None: If no items are left to be popped from the queue
        """

        # Check if the queue is empty
        if len(self.p_queue) == 0:
            return None

        # Pop the top value off the queue
        queue_item = heapq.heappop(self.p_queue)
        self.max_probability = queue_item.pt_item['prob']

        # Push the children back on the stack
        #
        # Currently using the deadbeat dad algorithm as described
        # in my dissertation:
        # http://diginole.lib.fsu.edu/cgi/viewcontent.cgi?article=5135
        #
        for child in self.pcfg.find_children(queue_item.pt_item):
            self.insert_queue(child)

        return queue_item.pt_item

    def insert_queue(self, queue_item):
        """
        Inserts an item into the pqueue

        Making this its own function in case I decide to change how the pqueue
        operates in the future

        Inputs:
            queue_item: The value to save in the pqueue

        Returns:
            None
        """
        heapq.heappush(self.p_queue, QueueItem(queue_item))

    def restore_base_item(self, base_item):
        """
        Restores all the items from the base_item to the pqueue

        This is used to restore a previous guessing session

        Inputs:
            base_item: A pt of the most probable pre-terminal for a base_item

        Returns:
            None
        """
        load_success = self.pcfg.restore_prob_order(
            base_item,
            self.max_probability,
            self.min_probability,
            self.insert_queue
            )

    def update_save_config(self, save_config):
        """
        Updates the config file for saving/loading sessions, with current status

        Inputs:
            save_config: A configparser object to save the current state

        Returns:
            None
        """
        save_config.set('guessing_info', 'min_probability', str(self.min_probability))
        save_config.set('guessing_info', 'max_probability', str(self.max_probability))
