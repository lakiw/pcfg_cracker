########################################################################
# Used for code profiling
########################################################################

import cProfile


#####################################################################
# I've struggled getting other python profiling tools to work but this
# hack I found on stack exchange seems to do a decent job
# To use it, put 
# @do_cprofile
# before the function you want to profile.
# Do not leave this enable on deployed code since it will generate *junk* guesses
# since it prints to stdout
######################################################################
def do_cprofile(func):
    def profiled_func(*args, **kwargs):
        profile = cProfile.Profile()
        try:
            profile.enable()
            result = func(*args, **kwargs)
            profile.disable()
            return result
        finally:
            profile.print_stats()
    return profiled_func