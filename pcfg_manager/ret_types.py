#!/usr/bin/env python3

## \package pcfg_manager.ret_values
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
    
    ## Error with File IO
    FILE_IO_ERROR                       = 1
    
    ## The priority queue is empty
    QUEUE_EMPTY                         = 2
    
    ## The priority queue is full, no more values can be added to it at this time
    QUEUE_FULL_ERROR                    = 4
    
    ## Error parsing the command line. Can be caused by invalid inputs or lack of required inputs
    COMMAND_LINE_ERROR                  = 5
    
    ## Error parsing the config file
    CONFIG_ERROR                        = 6
    
    ## Error with the PCFG Grammar
    GRAMMAR_ERROR                       = 7
    
    ## No more children for this particula node
    NO_MORE_CHILDREN                    = 8
    
    ## Broken output pipe, (the password cracker probably stopped)
    BROKEN_PIPE                         = 9
    
    ## Debug results
    DEBUG                               = 97
    
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