"""API functions related to versions."""
import quest
from jsonrpc import dispatcher


@dispatcher.add_method
def get_quest_version():
    """Get QUEST version.

   Returns:
        QUEST version (string):
            version of QUEST being used
    """
    return quest.__version__


@dispatcher.add_method
def get_api_version():
    """Get QUEST API version.

    Returns:
        QUEST version (string):
            version of QUEST API being used
    """
    return quest.api.__version__
