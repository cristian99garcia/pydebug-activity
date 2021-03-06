"""Decorators for labeling test objects.

Decorators that merely return a modified version of the original function
object are straightforward.  Decorators that return a new function object need
to use nose.tools.make_decorator(original_function)(decorator) in returning the
decorator, in order to preserve metadata such as function name, setup and
teardown functions and so on - see nose.tools for more information.

This module provides a set of useful decorators meant to be ready to use in
your own tests.  See the bottom of the file for the ready-made ones, and if you
find yourself writing a new one that may be of generic use, add it here.

NOTE: This file contains IPython-specific decorators and imports the
numpy.testing.decorators file, which we've copied verbatim.  Any of our own
code will be added at the bottom if we end up extending this.
"""

# Stdlib imports
import inspect
import sys

# Third-party imports

# This is Michele Simionato's decorator module, also kept verbatim.
from decorator_msim import decorator, update_wrapper

# Grab the numpy-specific decorators which we keep in a file that we
# occasionally update from upstream: decorators_numpy.py is an IDENTICAL copy
# of numpy.testing.decorators.
from decorators_numpy import *

##############################################################################
# Local code begins

# Utility functions

def apply_wrapper(wrapper,func):
    """Apply a wrapper to a function for decoration.

    This mixes Michele Simionato's decorator tool with nose's make_decorator,
    to apply a wrapper in a decorator so that all nose attributes, as well as
    function signature and other properties, survive the decoration cleanly.
    This will ensure that wrapped functions can still be well introspected via
    IPython, for example.
    """
    import nose.tools

    return decorator(wrapper,nose.tools.make_decorator(func)(wrapper))


def make_label_dec(label,ds=None):
    """Factory function to create a decorator that applies one or more labels.

    :Parameters:
      label : string or sequence
      One or more labels that will be applied by the decorator to the functions
    it decorates.  Labels are attributes of the decorated function with their
    value set to True.

    :Keywords:
      ds : string
      An optional docstring for the resulting decorator.  If not given, a
      default docstring is auto-generated.

    :Returns:
      A decorator.

    :Examples:

    A simple labeling decorator:
    >>> slow = make_label_dec('slow')
    >>> print slow.__doc__
    Labels a test as 'slow'.

    And one that uses multiple labels and a custom docstring:
    >>> rare = make_label_dec(['slow','hard'],
    ... "Mix labels 'slow' and 'hard' for rare tests.")
    >>> print rare.__doc__
    Mix labels 'slow' and 'hard' for rare tests.

    Now, let's test using this one:
    >>> @rare
    ... def f(): pass
    ...
    >>>
    >>> f.slow
    True
    >>> f.hard
    True
    """

    if isinstance(label,basestring):
        labels = [label]
    else:
        labels = label
        
    # Validate that the given label(s) are OK for use in setattr() by doing a
    # dry run on a dummy function.
    tmp = lambda : None
    for label in labels:
        setattr(tmp,label,True)

    # This is the actual decorator we'll return
    def decor(f):
        for label in labels:
            setattr(f,label,True)
        return f
    
    # Apply the user's docstring, or autogenerate a basic one
    if ds is None:
        ds = "Labels a test as %r." % label
    decor.__doc__ = ds
    
    return decor


# Inspired by numpy's skipif, but uses the full apply_wrapper utility to
# preserve function metadata better and allows the skip condition to be a
# callable.
def skipif(skip_condition, msg=None):
    ''' Make function raise SkipTest exception if skip_condition is true

    Parameters
    ----------
    skip_condition : bool or callable. 
    Flag to determine whether to skip test.  If the condition is a 
    callable, it is used at runtime to dynamically make the decision.  This 
    is useful for tests that may require costly imports, to delay the cost 
    until the test suite is actually executed.        
    msg : string
        Message to give on raising a SkipTest exception

   Returns
   -------
   decorator : function
       Decorator, which, when applied to a function, causes SkipTest
       to be raised when the skip_condition was True, and the function
       to be called normally otherwise.

    Notes
    -----
    You will see from the code that we had to further decorate the
    decorator with the nose.tools.make_decorator function in order to
    transmit function name, and various other metadata.
    '''

    def skip_decorator(f):
        # Local import to avoid a hard nose dependency and only incur the 
        # import time overhead at actual test-time. 
        import nose

        # Allow for both boolean or callable skip conditions.
        if callable(skip_condition):
            skip_val = lambda : skip_condition()
        else:
            skip_val = lambda : skip_condition

        def get_msg(func,msg=None):
            """Skip message with information about function being skipped."""
            if msg is None: out = 'Test skipped due to test condition.'
            else: out = msg
            return "Skipping test: %s. %s" % (func.__name__,out)

        # We need to define *two* skippers because Python doesn't allow both
        # return with value and yield inside the same function.
        def skipper_func(*args, **kwargs):
            """Skipper for normal test functions."""
            if skip_val():
                raise nose.SkipTest(get_msg(f,msg))
            else:
                return f(*args, **kwargs) 

        def skipper_gen(*args, **kwargs):
            """Skipper for test generators."""
            if skip_val():
                raise nose.SkipTest(get_msg(f,msg))
            else:
                for x in f(*args, **kwargs):
                    yield x

        # Choose the right skipper to use when building the actual generator.
        if nose.util.isgenerator(f):
            skipper = skipper_gen
        else:
            skipper = skipper_func
            
        return nose.tools.make_decorator(f)(skipper)

    return skip_decorator

# A version with the condition set to true, common case just to attacha message
# to a skip decorator
def skip(msg=None):
    """Decorator factory - mark a test function for skipping from test suite.

    :Parameters:
      msg : string
        Optional message to be added.

    :Returns:
       decorator : function
         Decorator, which, when applied to a function, causes SkipTest
         to be raised, with the optional message added.
      """

    return skipif(True,msg)


#-----------------------------------------------------------------------------
# Utility functions for decorators
def numpy_not_available():
    """Can numpy be imported?  Returns true if numpy does NOT import.

    This is used to make a decorator to skip tests that require numpy to be
    available, but delay the 'import numpy' to test execution time.
    """
    try:
        import numpy
        np_not_avail = False
    except ImportError:
        np_not_avail = True

    return np_not_avail

#-----------------------------------------------------------------------------
# Decorators for public use

skip_doctest = make_label_dec('skip_doctest',
    """Decorator - mark a function or method for skipping its doctest.

    This decorator allows you to mark a function whose docstring you wish to
    omit from testing, while preserving the docstring for introspection, help,
    etc.""")                              

# Decorators to skip certain tests on specific platforms.
skip_win32 = skipif(sys.platform == 'win32',
                    "This test does not run under Windows")
skip_linux = skipif(sys.platform == 'linux2',
                    "This test does not run under Linux")
skip_osx = skipif(sys.platform == 'darwin',"This test does not run under OS X")


# Decorators to skip tests if not on specific platforms.
skip_if_not_win32 = skipif(sys.platform != 'win32',
                           "This test only runs under Windows")
skip_if_not_linux = skipif(sys.platform != 'linux2',
                           "This test only runs under Linux")
skip_if_not_osx = skipif(sys.platform != 'darwin',
                         "This test only runs under OSX")

# Other skip decorators
skipif_not_numpy = skipif(numpy_not_available,"This test requires numpy")

skipknownfailure = skip('This test is known to fail')
