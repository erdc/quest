import appdirs
import os
from stevedore import extension, driver
try:
    import simplejson as json
except ImportError:
    import json


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


def load_drivers(namespace, names=None):
    namespace = 'data_services_library.' + namespace 
    if not names:
        mgr = extension.ExtensionManager(
            namespace=namespace,
            invoke_on_load=True,
        )
        return dict((x.name, x.obj) for x in mgr)

    if not isinstance(ids, list):
        names = [names]

    return {name: driver.DriverManager(namespace, name, invoke_on_load='True') for name in names} 
    

def get_driver_method(ext, method):
    return ext.obj.get(method).copy()
    

def jsonify(f):
    def wrapped_f(*args, **kw):
        if 'json' in kw.keys():
            kw = json.loads(kw)

        if 'as_json' in kw.keys():
            return json.dumps(f(*args, **kw), sort_keys=True, indent=4, separators=(',', ': '))
        else:
            return f(*args, **kw)
    return wrapped_f  # the wrapped function gets returned.
