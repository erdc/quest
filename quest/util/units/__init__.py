import os

from pint import UnitRegistry


def unit_registry():
    file_path = os.path.join(os.path.dirname(__file__), 'default_units.txt')
    return UnitRegistry(file_path)


def unit_list():
    reg = unit_registry()
    return [u for u in dir(reg) if isinstance(getattr(reg, u), type(reg.A))]