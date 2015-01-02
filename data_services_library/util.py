import appdirs
import os


def get_dsl_dir(sub_dir=None):
    return_dir = os.environ.get('ENVSIM_DSL_DIR')
    if not return_dir:
        return_dir = appdirs.user_data_dir('data-services-library', 'envsim')
    if sub_dir:
        return_dir = os.path.join(return_dir, sub_dir)
    mkdir_if_doesnt_exist(return_dir)
    return return_dir


def get_dsl_demo_dir():
    return_dir = os.environ.get('ENVSIM_DSL_DEMO_DIR')
    if not return_dir:
        raise 'Please Set environment variable ENVSIM_DSL_DEMO_DIR'
    mkdir_if_doesnt_exist(return_dir)
    return return_dir


def mkdir_if_doesnt_exist(dir_path):
    """makes a directory if it doesn't exist"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
