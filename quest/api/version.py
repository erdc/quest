import quest


def get_quest_version():
    """Get QUEST version.

   Returns:
        QUEST version (string):
            version of QUEST being used
    """
    return quest.__version__


def get_api_version():
    """Get QUEST API version.

    Returns:
        QUEST version (string):
            version of QUEST API being used
    """
    return quest.api.__version__
