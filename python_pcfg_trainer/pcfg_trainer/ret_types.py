#!/usr/bin/env python3

## \package pcfg_trainer.ret_values
# Global return values for functions
#

import enum

__all__ = [
    'RetValues'
    ]
    
#########################################################################
## Alert type code enumeration.
## Mostly just satisfies an OCD aspect of my personality to know what
## went wrong and pass it back up the stack
##########################################################################
@enum.unique
class RetType(enum.IntEnum):
    
    ## Everything worked as expected
    STATUS_OK                           = 0   
    
    ## Error parsing the command line
    COMMAND_LINE_ERROR                  = 1   
    
    ## Error reading or writeing a file
    FILE_IO_ERROR                       = 2
    
    ## IS_TRUE, Used to return TRUE when I want to allow other possible error codes to be returned
    IS_TRUE                             = 3
    
    ## IS_FALSE, Used to return FALSE when I want to allow other possible error codes to be returned
    IS_FALSE                            = 4
    
    ## Not enough passwords in the training file
    NOT_ENOUGH_TRAINING_PASSWORDS       = 5
    
    ## Bad input to the program
    BAD_INPUT                           = 6
    
    ## File encoding error
    ENCODING_ERROR                      = 7
    
    ## Debug results
    DEBUG                               = 8
    
    ## Generic error
    GENERIC_ERROR                       = 98
    
    ## Program should shut down
    QUIT                                = 99
    
    ## Program should shut down due to error
    ERROR_QUIT                          = 100
    
    
    

if __name__ == '__main__':
    # Self-test; print out all the return values.
    # Mostly just ensures the syntax of the module is correct and that the
    # unique constraint is not violated. No real test since it's just an enum.
    for c in RetType:
        print('{:20}: {}'.format(c.name, c.value))