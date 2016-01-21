"Tests for functions in settings.py using rpc server"
import os
from jsonrpc_requests import Server
import json
import tempfile
import requests
import subprocess
import time

rpc = Server('http://localhost:4000')

test_settings = {
    u'BASE_DIR': u'dsl',
    u'CACHE_DIR': u'cache',
    u'PROJECTS_DIR': u'projects',
    u'USER_SERVICES': [],
}

def setup_module(function):
    os.environ['ENVSIM_DSL_DIR'] = 'dslenv'
    subprocess.Popen(['dsl-rpc-server', 'start'], env=os.environ.copy())
    time.sleep(1) # wait a second to make sure server has started


def teardown_module(function):
    subprocess.Popen(['dsl-rpc-server', 'stop'])


# this test needs to run first because dsl is set from environment only
# when BASE_DIR is unset
def test_set_base_path_with_env_var():
    os.environ['ENVSIM_DSL_DIR'] = 'dslenv'
    rpc.update_settings()

    assert rpc.get_settings() == {
                u'BASE_DIR': u'dslenv',
                u'CACHE_DIR': u'cache',
                u'PROJECTS_DIR': u'projects',
                u'USER_SERVICES': [],
                }


def test_update_settings():
    """Basic test that paths are set correctly and defaults are used

    """
    rpc.update_settings(config={'BASE_DIR': 'dsl'})

    assert rpc.get_settings() == test_settings


def test_update_settings_from_file():
    rpc.update_settings_from_file('files/dsl_config.yml')
    test = test_settings.copy()
    test.update({'USER_SERVICES': ['iraq-vitd', 'usgs-ned1']})
    assert rpc.get_settings() == test


def test_save_settings():
    rpc.update_settings(config={'BASE_DIR': 'dsl'})
    filename = os.path.join(tempfile.gettempdir(), 'dsl_config.yml')
    rpc.save_settings(filename)
    rpc.update_settings_from_file(filename)

    assert rpc.get_settings() == test_settings
