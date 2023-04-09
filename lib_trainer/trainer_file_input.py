#!/usr/bin/env python3


"""

Contains all the file reading logic for the python pcfg trainer

"""


import codecs


def get_confirmation(warningtext):
    """
    Prints a warning message and asks for user confirmation

    Inputs:
        warningtext: (String) The warning to display to the user

    Returns:
        True: User selected Yes
        
        False: User selected No

    """
    print()
    print(warningtext)
    while True:
        try:
            user_input = input("Please confirm (Y/N): ")
        except:
            user_input = ''
        if user_input.lower() == 'y' or user_input.lower() == 'yes':
            return True
        elif user_input.lower() == 'n' or user_input.lower() == 'no':
            return False

        print("The option: " + str(user_input) + " : is not a valid input")
        print("Valid options: [Y]es or [N]o")


def detect_file_encoding(training_file, file_encoding, max_passwords = 500000):
    """
    Used for autodetecting file encoding of the training password set

    Autodectection requires the python package chardet to be installed

    pip install chardet

    You can also get it from https://github.com/chardet/chardet

    I'm keeping the declarations for the chardet package local to this file
    so people can run this tool without installing it if they don't want to
    use this feature

    Inputs:
        training_file: (String) The path+name of the file to open

        file_encoding: (List) A list to return the possible/recommended file
        encodings of the training file

        max_passwords: (Int) The maximum number of passwords to parse to
        identify the encoding of the file. This is an optimization so this
        function doesn't have to parse the whole file.
        
    Returns:
        True: The function executed sucesfully
        
        False: An error occured, or the user did not have the chardet library
        and decided to not accept the default 'ascii' setting

    """

    # Try to import chardet
    #
    # If that package is not installed print out a warning and use is ok,
    # then use ascii as the default values
    #
    try:
        from chardet.universaldetector import UniversalDetector
        detector = UniversalDetector()
    except ImportError as error:
        print("FAILED: chardet not insalled")
        print("It is highly recommended that you install the 'chardet' Python package")
        print("or manually specify the file encoding of the training set via the command line")
        print("You can download chardet from https://pypi.python.org/pypi/chardet")
        if get_confirmation("Do you want to continue using the default encoding 'ascii'?"):
            file_encoding.append('ascii')
            return True

        # User wanted to exit instead
        print("Understood. Please install chardet or specify an encoding " +
            "format on the command line"
            )
        return False

    try:
        cur_count = 0
        with open(training_file, 'rb') as file:
            for line in file.readlines():
            
                # Check for a $HEX[] encoded password 
                end_bracket_pos = line.find(bytes("]", "ascii"))
                if line.startswith(bytes("$HEX[","ascii")) and end_bracket_pos:
                    try:
                        line = bytes.fromhex(line[5:end_bracket_pos].decode("ascii"))
                    except:
                        continue

                # Now try to detect encoding of line
                detector.feed(line)
                if detector.done:
                    break
                cur_count = cur_count + 1
                if cur_count >= max_passwords:
                    break
            detector.close()

    except IOError as error:
        print ("Error opening file " + training_file)
        print ("Error is " + str(error))
        return False

    try:
        file_encoding.append(detector.result['encoding'])
        print("File Encoding Detected: " + str(detector.result['encoding']))
        print("Confidence for file encoding: " + str(detector.result['confidence']))
        print("If you think another file encoding might have been used please ")
        print("manually specify the file encoding and run the training program again")
        print()

        # Manually overriding ASCII to UTF-8 to deal with $HEX[] encoded files
        if file_encoding[0] is "ascii":
            print("Overriding ASCII and converting it to UTF-8 to deal with $HEX[] encoded training files")
            print("If you really want to have an ASCII encoded file you can specify it on the command line")
            print("But there shouldn't be any downside with using UTF-8")
            file_encoding[0] = "utf-8"

    except KeyError as error:
        print("Error encountered with file encoding autodetection")
        print("Error : " + str(error))
        return False

    return True


def check_valid(input_password):
    """
    Checks to see if the input password is valid for this training program

    Invalid in this case means you don't want to train on them

    Additionaly grammar checks may be run later to futher exclude passwords#
    This just features that will likely be universal rejections

    Inputs:
        input_password: (String) The input password to parse

    Returns:
        TRUE: If the password is valid
        
        FALSE: If the password is invalid

    """

    # Don't accept blank passwords for training.
    if len(input_password) == 0:
        return False

    # Remove tabs from the training data
    # This is important since when the grammar is saved to disk tabs are used
    # as seperators. There certainly are other approaches but putting this
    # placeholder here for now since tabs are unlikely to be used in passwords
    if "\t" in input_password:
        return False

    # Below are other values that cause problems that we are going to remove.
    # These values include things like LineFeed LF

    #Invalid characters at the begining of the ASCII table
    for invalid_hex in range (0x0,0x20):
        if chr(invalid_hex) in input_password:
            return False

    # UTF-8 Line Seperator
    if u"\u2028" in input_password:
        return False

    # UTF-8 NEL Line seperator 'C285' eg unicode character '0085'
    # I coupld probably replace with a newline, but given how this tends to
    # show up in XML data it can highlight a weirder issue going on with inputs.
    # So dropping it vs. trying to fix it up for now.
    if u"\u0085" in input_password:
        return False

    return True


class TrainerFileInput:
    """
    Reads input passwords from file, one by one

    Making this a class so it can return one password at a time from the
    training file

    """

    def __init__(self, filename, encoding = 'utf-8'):
        """
        Open the file for reading

        Passes file exceptions back up if they occur
        Eg: if the file doesn't exist
        
        Inputs:
            filename: (String) The filename of the training file to open
            
            encoding: (String) The file encoding to use when parsing the file
            
        Returns:
            TrainingFileInput: (Object)

        """

        # Using surrogateescape to handle errors so we can detect encoding
        # issues without raising an exception during the reading
        # of the original password
        #
        self.encoding = encoding
        self.filename = filename
        self.file = codecs.open(
            self.filename,
            'r',
            encoding= self.encoding,
            errors= 'surrogateescape'
        )

        # Keep track of the number of encoding errors
        self.num_encoding_errors = 0

        # Keep track of the number of valid passwords that have been parsed
        self.num_passwords = 0

        # Duplicate password detection
        #
        # Duplicates are good. If this doesn't see duplicate passwords warn the
        # user.
        self.duplicates_found = False

        # Mini dictionary of the first X passwords to look for duplicates
        self.duplicate_detection = {}

        # Number of passwords to read in to check for duplicates
        self.num_to_look_for_duplicates = 100000

    def read_password(self):
        """
        Returns one password from the training set. If there are no more passwords returns None
        
        Inputs:
            None
            
        Returns:
            clean_password: (String) The next password
            
            None: IF there are no more passwords to parse

        """

        # Read an input password from the training set
        try:
            # Loop until we find a valid password
            while True:
                try:
                    password = self.file.readline()

                # Unicode errors will throw an exception here, so catch it
                # and skip the password
                except UnicodeError:
                    self.num_encoding_errors += 1
                    continue

                # Check to see if the file is done
                if password == "":
                    # Close file and return None
                    self.file.close()
                    return None

                # Remove newlines but leave whitespace
                clean_password = password.rstrip('\r\n')                

                # Check for a $HEX[] encoded password    
                if clean_password.startswith("$HEX[") and clean_password.endswith("]"):
                    try:
                        clean_password = bytes.fromhex(clean_password[5:-1]).decode(self.encoding)
                    except:
                        self.num_encoding_errors += 1
                        continue
                    
                ## Check the encoding of the file
                #
                # Re-encode it and detect surrogates, this way we can
                # identify encoding errors.
                #
                # I know, could simplify by throwing an exception during
                # the original parsing and not use surrogate escapes, but this
                # has helped with troubleshooting in the past
                #
                try:
                    clean_password.encode(self.encoding)
                except UnicodeEncodeError as msg:
                    if msg.reason == 'surrogates not allowed':
                        self.num_encoding_errors += 1
                    else:
                        #print("Hmm, there was a weird problem reading in a line")
                        #print("")
                        self.num_encoding_errors += 1
                    continue

                # Checks to see if the password is valid
                if not check_valid(clean_password):
                    continue

                ## This is a valid password
                self.num_passwords += 1

                # Perform duplicate check if needed
                if not self.duplicates_found:
                    if self.num_passwords < self.num_to_look_for_duplicates:
                        # It is a duplicate!!
                        if clean_password in self.duplicate_detection:
                            self.duplicates_found = True
                            # clean up duplicate_detection dic since we do
                            # not need it anymore
                            self.duplicate_detection.clear()

                        # Not a duplicate
                        self.duplicate_detection[clean_password] = 1

                # Return the password
                return clean_password

        # File errors *shouldn't* happen but if they do raise them to make
        # sure they don't silently halt the training
        #
        # Aka we want the training to stop and the user to know something
        # went wrong
        #
        except IOError as error:
            print (error)
            print ("Error reading file " + self.filename)
            raise
