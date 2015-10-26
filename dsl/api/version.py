import dsl
from jsonrpc import dispatcher

@dispatcher.add_method
def get_dsl_version():
    return dsl.__version__


@dispatcher.add_method
def get_api_version():
    return dsl.api.__version__
