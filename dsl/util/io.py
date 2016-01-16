"""io utilities"""
import os
import yaml
from .misc import mkdir_if_doesnt_exist


def read_yaml(path):
    if not os.path.exists(path):
        return {}

    with open(path) as f:
        return yaml.safe_load(f)


def write_yaml(path, payload):
    folder, _ = os.path.split(path)
    mkdir_if_doesnt_exist(folder)
    with open(path, 'w') as f:
        yaml.safe_dump(payload, f, default_flow_style=False)
