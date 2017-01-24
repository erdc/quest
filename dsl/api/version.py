"""API functions related to versions."""
import dsl
from jsonrpc import dispatcher


@dispatcher.add_method
def get_dsl_version():
    """Get DSL version.

   Returns:
        DSL version (string):
            version of DSL being used
    """
    return dsl.__version__


@dispatcher.add_method
def get_api_version():
    """Get DSL API version.

    Returns:
        DSL version (string):
            version of DSL API being used
    """
    return dsl.api.__version__
