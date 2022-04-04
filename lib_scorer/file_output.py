#!/usr/bin/env python3


"""

Contains file operations for saving output of a PCFG Scoring Run

"""


import sys
import codecs


class FileOutput:
    """
    Saves output to a file or to stdout.

    Making this a class so I can open the file once, (if needed), for writing
    and then can call the write function repeatedly each time
    there is new data to output.

    The data this saves is a Python tuple but it should work for a Python
    dictionary as well.
    """

    def __init__(self, filename = None, encoding = 'utf-8'):
        """
        Open the file for writing if necissary. If filename is
        None, will instead set it up to write to stdout instead

        Will pass Exceptions back up if they occur. For example
        if the program does not have permission to create the file

        Inputs:
            filename: The full name + path of the file to save
            results to. If it is set to None, will output resutls to stdout

            encoding: The character encoding to use when saving results.
            This is important since it will save the original password
            as well as its associated score.

        Returns:
            FileOutput
        """

        self.encoding = encoding
        self.filename = filename

        # If a file was specified to write the data to, open it for writing
        if self.filename is not None:
            self.file = codecs.open(
                self.filename,
                'w',
                encoding= self.encoding,
            )

    def write(self, data):
        """
        Takes a Python tuple and writes it as tab seperated to output
        followed by a newline. Will save to a file or print to
        stdout as defined by when this FileOutput class was initialized

        Note: This only catches exceptions for some stdout issues, so
        if for example, the file becomes full that exception will
        be passed back up to the calling function.

        Inptus:
            data: The Python tuple or dictionary to output

        Returns:
            None
        """

        last_index = len(data) -1

        # If the writer was initalized to output to a file, write the data
        # to the file
        if self.filename is not None:
            for index, item in enumerate(data):
                self.file.write(str(item))
                if index < last_index:
                    self.file.write('\t')

            self.file.write('\n')

        # If the writer was not set up to write to a file, write the data
        # instead to stdout, followed by a newline
        else:
            for index, item in enumerate(data):

                # Adding exception handling here to deal with trying
                # to print out an unprintable chacacter it can print the
                # hex instead
                try:
                    sys.stdout.write(str(item))
                except UnicodeEncodeError:
                    print("[UNPRINTABLE_HEX]")

                if index < last_index:
                    sys.stdout.write('\t')

            sys.stdout.write('\n')
