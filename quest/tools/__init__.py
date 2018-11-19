import sys

from ..static import PluginType
from ..plugins import load_plugins


tools = load_plugins(PluginType.TOOL)


def codify(name):
    return name.lower().replace('-', '_').replace(' ', '_')


for tool_name, tool in tools.items():
    this_module = sys.modules[__name__]
    tool_code_name = codify(tool_name)
    setattr(this_module, tool_code_name, tool)
