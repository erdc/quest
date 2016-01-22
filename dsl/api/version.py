"""API functions related to versions."""
import dsl
from jsonrpc import dispatcher


@dispatcher.add_method
def get_dsl_version():
    """Return DSL version.

    Returns
    -------
        str
            DSL version
    """
    return dsl.__version__


@dispatcher.add_method
def get_api_version():
    """Return DSL API version.

    Returns
    -------
        str
            DSL version
    """
    return dsl.api.__version__
