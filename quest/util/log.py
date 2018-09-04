import logging
import appdirs
import os


logger = logging.getLogger('quest')
null_handler = logging.NullHandler()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s : %(message)s')
null_handler.setFormatter(formatter)
logger.addHandler(null_handler)
logger.propagate = False

default_log_dir = appdirs.user_log_dir('quest', 'erdc')
default_log_file = os.path.join(default_log_dir, 'quest.log')


def log_to_file(status=True, filename=default_log_file, log_level=None):
    """Log events to a file.

    Args:
        status (bool, Optional, Default=True)
            whether logging to file should be turned on(True) or off(False)
        filename (string, Optional, Default=None) :
            path of file to log to
        log_level (string, Optional, Default=None) :
            level of logging; whichever level is chosen all higher levels will be logged. For example,
            selecting DEBUG will log all DEBUG,INFO,WARNING,ERROR, and CRITICAL events

            If not reset to "DEBUG" after changing level, changed level will remain in effect for that current session

            Available log levels:
                DEBUG	Detailed information, typically of interest only when diagnosing problems.
                INFO	Confirmation that things are working as expected.
                WARNING	An indication that something unexpected happened, or indicative of some problem in the near
                    future(e.g. 'disk space low'). The software is still working as expected.
                ERROR	Due to a more serious problem, the software has not been able to perform some function.
                CRITICAL	A serious error, indicating that the program itself may be unable to continue running.


     Returns:
          status (bool):
            if True, logging to file was successful
      """

    if status:

            os.makedirs(os.path.dirname(filename), exist_ok=True)

            file_handler = logging.FileHandler(filename)

            logger.addHandler(file_handler)

            if log_level is not None:
                logger.setLevel(log_level)

    else:
        for i, j in enumerate(logger.handlers):
            if type(j).__name__ == 'FileHandler':
                logger.removeHandler(logger.handlers[i])

    return True


def log_to_console(status=True, log_level=None):
    """Log events to  the console.

    Args:
        status (bool, Optional, Default=True)
            whether logging to console should be turned on(True) or off(False)
        log_level (string, Optional, Default=None) :
            level of logging; whichever level is chosen all higher levels will be logged. For example,
            selecting DEBUG will log all DEBUG,INFO,WARNING,ERROR, and CRITICAL events

            If not reset to "DEBUG" after changing level, changed level will remain in effect for that current session

            Available log levels:
                DEBUG	Detailed information, typically of interest only when diagnosing problems.
                INFO	Confirmation that things are working as expected.
                WARNING	An indication that something unexpected happened, or indicative of some problem in the near
                    future(e.g. 'disk space low'). The software is still working as expected.
                ERROR	Due to a more serious problem, the software has not been able to perform some function.
                CRITICAL	A serious error, indicating that the program itself may be unable to continue running.


     Returns:
          status (bool):
            if True, logging to console was successful
      """

    if status:

        console_handler = logging.StreamHandler()

        logger.addHandler(console_handler)

        if log_level is not None:
            logger.setLevel(log_level)

    else:
        for i, j in enumerate(logger.handlers):
            if type(j).__name__ == 'StreamHandler':
                logger.removeHandler(logger.handlers[i])

    return True
