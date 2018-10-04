import os
import yaml


def read_yaml(path):
    if not os.path.exists(path):
        return {}

    with open(path) as f:
        return yaml.safe_load(f)


def write_yaml(path, payload):
    folder, _ = os.path.split(path)
    os.makedirs(folder, exist_ok=True)

    with open(path, 'w') as f:
        yaml.safe_dump(payload, f, default_flow_style=False)
