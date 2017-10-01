"""A simple Google-style logging wrapper.

This library attempts to greatly simplify logging in Python applications.
Nobody wants to spend hours pouring over the PEP 282 logger documentation, and
almost nobody actually needs things like loggers that can be reconfigured over
the network.  We just want to get on with writing our apps.

## Core benefits

* You and your code don't need to care about how logging works. Unless you want
  to, of course.

* No more complicated setup boilerplate!

* Your apps and scripts will all have a consistent log format, and the same
  predictable behaviours.

This library configures the root logger, so nearly everything you import
that uses the standard Python logging module will play along nicely.

## Behaviours

* By default, all messages are recorded to a local log file and only messages of
  level ERROR and higher are sent to stderr (configurable).  

* Lines are prefixed with a google-style log prefix, of the form

      E0924 22:19:15.123456 19552 filename.py:87] Log message blah blah

  Splitting on spaces, the fields are:

    1. The first character is the log level, followed by MMDD (month, day)
    2. HH:MM:SS.microseconds
    3. Process ID
    4. basename_of_sourcefile.py:linenumber]
    5. The body of the log message.

* Use gflags to change the default behavior (details below)

* Log files are stored in --log_dir with name: 
  <program_name>.<hostname>.<user name>.log.<severity level>.<date>.<time>.<pid>
  example: hello_world.example.com.hamaji.log.INFO.20080709.222411.10474


## Example logging usage

    import glog as log

    log.info("It works.")
    log.warn("Something not ideal")
    log.error("Something went wrong")
    log.fatal("AAAAAAAAAAAAAAA!")

If your app uses gflags, it will automatically gain these flags: 

--logtostderr  Send all logs to stderr (set minloglevel to reduce verbosity)    
--minloglevel  Controls verbosity when logtostderr enabled
--stderrthreshold  Controls verbosity when logtostderr is not set 
    (default setting supresses all but ERROR and FATAL messages) 

In order for that flag to take effect, you must call log.init() after parsing
flags, like so:

    import sys
    import gflags
    import glog as log

    FLAGS = gflags.FLAGS

    def main():
      log.debug('warble garble %s', FLAGS.verbosity)

    if __name__ == '__main__':
        posargs = FLAGS(sys.argv)
        log.init()
        main(posargs[1:])


## Example flag usage

Default behavior is suitable for typical interactive cli utility.  It logs only
ERROR and higher to stderr to avoid cluttering the cli interface with chatty log
messages.  When running a headless server with no user interaction, use the 
--logtostderr flag.  This ensures all messages are sent to stderr and can be
redirected to a logging service.

Example using syslog logger command: 

logger | ./my_app --logtostderr


## Example check usage

The C++ glog library provides a set of macros that help document and enforce
invariants.  These are superior to standard python asserts because they provide
a message indicating the values that caused the check to fail.  This helps in
reproducing failure cases and provides values for test cases.  Another important
difference is that assert statements can be disabled by optimization, but check
statements are always executed regardless of optimization level.

https://google-glog.googlecode.com/svn/trunk/doc/glog.html#check


    import glog as log
    import math
    
    def compute_something(a):
        log.check_eq(type(a), float) # require floating point types
        log.check_ge(a, 0) # require non-negative values
        value = math.sqrt(a)
        return value
   
    if __name__ == '__main__':
        compute_something(10)


Happy logging!

"""
from __future__ import absolute_import
import logging
import logging.handlers
import time
import traceback
import os
import sys
import gflags
import platform
import getpass
import datetime

FLAGS = gflags.FLAGS
try:
    gflags.DEFINE_bool('logtostderr', False, 'Send log messsage to STDERR instead of the log file.')
    gflags.DEFINE_integer('stderrthreshold', 2, 'Copy log messages at or above this level to STDERR in addition to the '
                          'log files. The numbers of severity levels DEBUG, INFO, WARNING, ERROR, and FATAL are '
                          '-1, 0, 1, 2, and 3, respectively.')
    gflags.DEFINE_integer('minloglevel', -1, 'Log messages at or above this level. Again, the numbers of severity '
                          'levels DEBUG, INFO, WARNING, ERROR, and FATAL are -1, 0, 1, 2, and 3, respectively.')
    gflags.DEFINE_string('log_dir', '/tmp', 'If specified, log files are written into this directory instead of the '
                         'default directory.')
except:
    pass

# This used to call getLogger('common.log') but the problem with this is that it effectively
# creates to root loggers. In the case that Django is getting used,the root logged is
# called 'root' so we want to bind to that existing logger here too so we don't get duplicate
# records on every log call. Based on experiments (without much understanding) by ZBS 16 Aug 2016.
# I'm leaving this commented out here and with this note because I'm not 100% sure this is the right solution.
# logger = logging.getLogger('common.log')
logger = logging.getLogger('root')

global orig_except_hook_handler

def init(log_dir=None):
    """ Called to configure logger from gflags.  
    
    If you'd like your program to respond to logging flags, call log.init() at
    some point after you have parsed gflags.
    
    Example: 
    
    >>> gflags.FLAGS(sys.argv)  # parse flags
    >>> log.init() # GFLAGS just parsed, so ask logging to init using updated flags     
    """
    global logger
    global file_handler
    global stderr_handler
    global orig_except_hook_handler
    logger.removeHandler(stderr_handler)
    logger.removeHandler(file_handler)        

    # Here we get the flags using the FLAGS.FlagDict(), because the FLAGS [] op 
    # imposes a requirement that flags have been parsed.  We need to support
    # users who won't parse any command line args and need the default values.
    d = FLAGS.FlagDict()
    
    
    logtostderr = d['logtostderr'].value
    stderrthreshold = d['stderrthreshold'].value
    minloglevel = d['minloglevel'].value
    if log_dir is None:
        log_dir = d['log_dir'].value

    # If we redirect all logging to stderr, the --minloglevel flags controls 
    # how much is output just like it did for the file output mode
    if logtostderr:
        stderr_handler = logging.StreamHandler(stream=sys.stderr)
        level = _glog_to_python_level(minloglevel)
        init_handler(stderr_handler, level)        
    # In interactive mode, file logging and stderr logging levels can be set 
    # independently by --minloglevel and --stderrthreshold, respectively  
    else:
        filename = logfile_name(log_dir)
        file_handler = logging.handlers.RotatingFileHandler(filename, maxBytes=1e6, backupCount=4, delay=True)
        level = _glog_to_python_level(minloglevel)
        init_handler(file_handler, level)    
        stderr_handler = logging.StreamHandler(stream=sys.stderr)
        level = _glog_to_python_level(stderrthreshold)
        init_handler(stderr_handler, level)
    
    logger.setLevel(logging.DEBUG)  # delegate filtering to each output handler
    orig_except_hook_handler = sys.excepthook
    sys.excepthook = log_uncaught_exceptions
    return


class GlogFormatter(logging.Formatter):
    LEVEL_MAP = {
        logging.FATAL: 'F',  # FATAL is alias of CRITICAL
        logging.ERROR: 'E',
        logging.WARN: 'W',
        logging.INFO: 'I',
        logging.DEBUG: 'D'
    }

    def __init__(self):
        logging.Formatter.__init__(self)

    @staticmethod
    def format_message(record):
        try:
            record_message = '%s' % (record.msg % record.args)
        except TypeError:
            record_message = record.msg
        except ValueError:
            # This was previously an except only for TypeError
            # but a Value error can happen when the record.msg
            # has a % in it that isn't part of a variable expansion
            record_message = record.msg
        return record_message

    def format(self, record):
        try:
            level = GlogFormatter.LEVEL_MAP[record.levelno]
        except:
            level = '?'
        date = time.localtime(record.created)
        date_usec = (record.created - int(record.created)) * 1e6
        record_message = '%c%02d%02d %02d:%02d:%02d.%06d %s %s:%d] %s' % (
            level, date.tm_mon, date.tm_mday, date.tm_hour, date.tm_min,
            date.tm_sec, date_usec,
            record.process if record.process is not None else '?????',
            record.filename,
            record.lineno,
            self.format_message(record))
        record.getMessage = lambda: record_message
        return logging.Formatter.format(self, record)

exception_count = 0

def handle_exception(*args):
    global exception_count
    exception_count += 1
    sys.stderr.write('*** EXCEPTION START {} ************************************************************************\n'.format(exception_count))
    logger.exception(*args)
    sys.stderr.write('*** EXCEPTION STOP  {} ************************************************************************\n'.format(exception_count))


file_handler = None
stderr_handler = None
debug = logger.debug
info = logger.info
warning = logger.warning
warn = logger.warning
error = logger.error
exception = handle_exception
fatal = logger.fatal
log = logger.log

_glog_to_py_levels = {-1: logging.DEBUG,
                       0: logging.INFO,
                       1: logging.WARN,
                       2: logging.ERROR,
                       3: logging.FATAL}

def _glog_to_python_level(glog_level):
    if glog_level not in _glog_to_py_levels:
        raise RuntimeError('Invalid glog level: %s' % glog_level)
    return _glog_to_py_levels[glog_level]


def init_handler(handler, level):
    handler.setFormatter(GlogFormatter())
    handler.setLevel(level)
    logger.addHandler(handler)
    return


def logfile_name(log_dir):
    # glog default is <program_name>.<hostname>.<user name>.log.<severity level>.<date>.<time>.<pid>
    # example hello_world.example.com.hamaji.log.INFO.20080709.222411.10474
    # NOTE: time used in other glog implementations seems to be local time.  That is used here for consistency.
    program_name = sys.argv[0]
    program_name = os.path.basename(program_name).strip('.py')
    host_name = platform.node()
    user_name = getpass.getuser()
    pid = os.getpid()
    now = datetime.datetime.now()
    date = now.strftime('%Y%m%d')  # YYYYMMDD
    time = now.strftime('%H%M%S')  # HHMMSS
    filename = '%s/%s.%s.%s.log.DEBUG.%s.%s.%d' % (log_dir, program_name, host_name, user_name, date, time, pid)
    # filename = '%s/log.%d' % (FLAGS.log_dir, pid)
    return filename


# Define functions emulating C++ glog check-macros 
# https://google-glog.googlecode.com/svn/trunk/doc/glog.html#check

def format_stacktrace(stack):
    """ Print a stack trace that is easier to read. 
    * Reduce paths to basename component
    * Truncates the part of the stack after the check failure
    """
    lines = []
    for i, f in enumerate(stack):
        name = os.path.basename(f[0])
        line = "@\t%s:%d\t%s" % (name + "::" + f[2], f[1], f[3])
        lines.append(line)    
    return lines


class FailedCheckException(Exception):

    """ Exception with message indicating check-failure location and values. """

    def __init__(self, message):
        self.message = message
        return

    def __str__(self):
        return self.message



def check_failed(message):
    """ Log informative message and a stack trace to failed check, level FATAL.
    
    Because logging fatal doesn't force termination, this raises an exception 
    to ensure process dies if not explicitly handled.
    
    Raises: FailedCheckException
    """
    raise FailedCheckException(message)
    
    
def check(condition, message=None):
    """ Raise exception with message if condition is False """
    if not condition:
        if message is None:
            message = "Check failed."
        check_failed(message)


def check_eq(obj1, obj2, message=None):
    """ Raise exception with message if obj1 != obj2. """
    if obj1 != obj2:
        if message is None:
            message = "Check failed: %s != %s" % (str(obj1), str(obj2))
        check_failed(message)


def check_ne(obj1, obj2, message=None):
    """ Raise exception with message if obj1 == obj2. """
    if obj1 == obj2:
        if message is None:
            message = "Check failed: %s == %s" % (str(obj1), str(obj2))
        check_failed(message)


def check_le(obj1, obj2, message=None):
    """ Raise exception with message if not (obj1 <= obj2). """
    if obj1 > obj2:
        if message is None:
            message = "Check failed: %s > %s" % (str(obj1), str(obj2))
        check_failed(message)


def check_ge(obj1, obj2, message=None):
    """ Raise exception with message if not (obj1 >= obj2)
    """
    if obj1 < obj2:
        if message is None:
            message = "Check failed: %s < %s" % (str(obj1), str(obj2))
        check_failed(message)


def check_lt(obj1, obj2, message=None):
    """ Raise exception with message if not (obj1 < obj2). """
    if obj1 >= obj2:
        if message is None:
            message = "Check failed: %s >= %s" % (str(obj1), str(obj2))
        check_failed(message)


def check_gt(obj1, obj2, message=None):
    """ Raise exception with message if not (obj1 > obj2). """
    if obj1 <= obj2:
        if message is None:
            message = "Check failed: %s <= %s" % (str(obj1), str(obj2))
        check_failed(message)


def check_notnone(obj, message=None):
    """ Raise exception with message if obj is None """
    if obj is None:
        if message is None:
            message = "Check failed. Object is None."
        check_failed(message)


def check_numeric(obj, message=None):
    """ Raise exception if not a form of numeric representation
    
    NOTE(Pablo):
    We've tried several implementations of this code, current one is the fastest
    we tried:
    1. isinstance(obj, numbers.Number)
        takes about 700 ns to run
    2. if type(obj) in [int, float, np.float32, ...]:
        takes about 300 ns to run
    3. current implementation takes about 100 ns to run
    """
    try:
        # multipyling by 1 would not work since for example "a" * 1 = "a"
        obj * 1.1
    except:
        if message is None:
            message = "Check failed. Object %s is not numeric." % (obj)
        check_failed(message)


def check_type(obj, obj_type, message=None):
    """ Raise exception if obj is not an instance of type """
    if not isinstance(obj, obj_type):
        if message is None:
            message = "Check failed. Object is of type %s, expected %s." % (str(type(obj)), str(obj_type))
        check_failed(message)


def log_uncaught_exceptions(ex_cls, ex, tb):
    """ Extends standard uncaught exception handling.
    
    Prints the exception to stdout (default behavior) and also sends to the 
    logger so it appears in log streams.
    
    If the exception is a CheckFailed exception then the stack trace is 
    re-formatted to stop at the location of the check failure.  This helps
    the developer quickly find the site where action needs to be taken. 
    """
    # standard exception formatting to stdout
    traceback.print_tb(tb)
     
    # also send to logging framework
    stack = traceback.extract_tb(tb)
    filename, line_num = 'unknown', 0
    lines = []
    # If the exception is a CheckFailed exception, remove two layers of stack 
    # so trace starts at the call site of the failed check.
    if isinstance(ex, FailedCheckException):
        stack = stack[0:-2]
        lines.insert(0, 'Stacktrace of failed check:')
        lines.insert(0, '%s' % (ex))
    else:
        lines.insert(0, 'Uncaught exception: %s' % (ex))
    if stack:
        filename, line_num, _, _ = stack[0]
    lines.extend(format_stacktrace(stack))
    for line in lines:
        if line.strip() != '':
            log_record = logger.makeRecord('FATAL', 50, filename, line_num, line, None, None)
            logger.handle(log_record)    


def stacktrace_exception(e=None):
    # TODO(heathkh): this should NOT take an argument... fix all call sites accordingly
    tb_string = traceback.format_exc()
    stack = traceback.extract_stack()
    filename, line_num, _, _ = stack[0]
    for line in tb_string.split('\n'):
        if line.strip() != '':
            log_record = logger.makeRecord('FATAL', 50, filename, line_num, line, None, None)
            logger.handle(log_record)

# Defines a constant useful by modules that might want to parse a 
# glog formatted log message

GLOG_PREFIX_REGEX = (
    r"""
    (?x) ^
    (?P<severity>[%s])
    (?P<month>\d\d)(?P<day>\d\d)\s
    (?P<hour>\d\d):(?P<minute>\d\d):(?P<second>\d\d)
    \.(?P<microsecond>\d{6})\s+
    (?P<process_id>-?\d+)\s
    (?P<filename>[a-zA-Z<_][\w._<>-]+):(?P<line>\d+)
    \]\s
    """) % ''.join(['D', 'I', 'W', 'E', 'F'])
"""Regex you can use to parse glog line prefixes."""


# Ensure log module initialized at least once.  Should be called again
# after parsing gflags to allow log related flags to be used.  
init()

