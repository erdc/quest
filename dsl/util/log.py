import logging
import os
import inspect
import sys

logger = logging.getLogger('dsl')
nullHdlr = logging.NullHandler()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s : %(message)s')
nullHdlr.setFormatter(formatter)
logger.addHandler(nullHdlr)
logger.propagate = False
defaultLog = os.getenv('DSL_DIR') + '/Log.log'



def log_to_file(status=True, filename=defaultLog, loglevel=None):
    """Log events to a file.

    Args:
        status (boolean) whether logging to file should be turned on(True) or off(False); default is True
        filename (string) : path of file to log to; Default path is DSL directory
        loglevel (string) : level of logging; whichever level is chosen all higher levels will be logged. For example, selecting DEBUG will log all DEBUG,INFO,WARNING,ERROR, and CRITICAL events; Default is DEBUG
            DEBUG	Detailed information, typically of interest only when diagnosing problems.
            INFO	Confirmation that things are working as expected.
            WARNING	An indication that something unexpected happened, or indicative of some problem in the near future (e.g. ‘disk space low’). The software is still working as expected.
            ERROR	Due to a more serious problem, the software has not been able to perform some function.
            CRITICAL	A serious error, indicating that the program itself may be unable to continue running.


    Returns:
        True: file exists
      """

    filehdlr = logging.FileHandler(filename)

    if loglevel is not None:
            logger.setLevel(logging.loglevel)

    if status is True:

        logger.addHandler(filehdlr)

    else:
        for i, j in enumerate(logger.handlers):
            if type(j).__name__ == 'FileHandler':
                logger.removeHandler(logger.handlers[i])


def log_to_console(status=True, loglevel=None):
    """Log events to console.

    Args:
        status (boolean) whether logging to console should be turned on(True) or off(False); default is True
        loglevel (string) : level of logging; whichever level is chosen all higher levels will be logged. For example, selecting DEBUG will log all DEBUG,INFO,WARNING,ERROR, and CRITICAL events; Default is DEBUG
            DEBUG	Detailed information, typically of interest only when diagnosing problems.
            INFO	Confirmation that things are working as expected.
            WARNING	An indication that something unexpected happened, or indicative of some problem in the near future (e.g. ‘disk space low’). The software is still working as expected.
            ERROR	Due to a more serious problem, the software has not been able to perform some function.
            CRITICAL	A serious error, indicating that the program itself may be unable to continue running.


    Returns:
        True: file exists
      """

    consolehdlr = logging.StreamHandler()

    if loglevel is not None:
            logger.setLevel(logging.loglevel)

    if status is True:

        logger.addHandler(consolehdlr)

    else:
        for i, j in enumerate(logger.handlers):
            if type(j).__name__ == 'StreamHandler':
                logger.removeHandler(logger.handlers[i])

