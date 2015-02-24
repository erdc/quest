import appdirs
import os
from stevedore import extension, driver
try:
    import simplejson as json
except ImportError:
    import json


def append_features(old, new):
    if not old:
        return new

    existing_features = [feature['id'] for feature in old['features']]
    for feature in new['features']:
        if feature['id'] not in existing_features:
            old['features'].append(feature)

    return old


def bbox2poly(x1, y1, x2, y2):
    xmin, xmax = sorted([float(x1), float(x2)])
    ymin, ymax = sorted([float(y1), float(y2)])
    poly = [(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)]
    poly.append(poly[0])

    return poly


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


def listify(liststr, delimiter=','):
    """If input is a string, split on comma and convert to python list
    """
    if liststr is None:
        return None

    return isinstance(liststr, list) and liststr or [s.strip() for s in liststr.split(delimiter)] 


def load_drivers(namespace, names=None):
    namespace = 'dsl.' + namespace 
    if not names:
        mgr = extension.ExtensionManager(
            namespace=namespace,
            invoke_on_load=True,
        )
        return dict((x.name, x.obj) for x in mgr)

    if not isinstance(names, list):
        names = [names]

    return {name: driver.DriverManager(namespace, name, invoke_on_load='True') for name in names} 
    

def remove_key(d, key):
    r = dict(d)
    del r[key]
    return r


def jsonify(f):
    def wrapped_f(*args, **kw):
        if 'json' in kw.keys():
            kw = json.loads(kw)

        if 'as_json' in kw.keys():
            return json.dumps(f(*args, **kw), sort_keys=True, indent=4, separators=(',', ': '))
        else:
            return f(*args, **kw)
    return wrapped_f  # the wrapped function gets returned.


def stringify(args):
    return isinstance(args, list) and ','.join(args) or None
