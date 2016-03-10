import os
from playhouse.dataset import DataSet
from .. import util


def upsert(dbpath, table, name, dsl_metadata=None, metadata=None):
    """
    """
    # name = _sanitize(name)
    dsl_metadata['name'] = name

    if dsl_metadata is None:
        dsl_metadata = {}

    data = {'_{}_'.format(k): v for k, v in dsl_metadata.items()}

    if metadata is not None:
        data.update(metadata)

    # cannot have id field in data when inserting into dataset
    if 'id' in data.keys():
        data['id0'] = data.pop('id')

    db = DataSet(_dburl(dbpath))
    t = db[table]

    if '_name_' not in t.columns:
        t.insert(**data)
        t.create_index(['_name_'], unique=True)
        return db

    if t.find_one(_name_=name) is not None:
        t.update(columns='_name_', **data)
    else:
        t.insert(**data)

    return db


def upsert_features(dbpath, features):
    """
    upsert pandas dataframe
    """
    db = DataSet(_dburl(dbpath))
    t = db['features']

    for uri, data in features.iterrows():
        if '_service_uri_' in data.index and '_service_uri_' in t.columns:
            if t.find_one(_service_uri_=data['_service_uri_']) is not None:
                continue

        data_dict = data.to_dict()
        data_dict.update({'_name_': util.uuid()})
        t.insert(**data_dict)

    try:
        t.create_index(['_name_'], unique=True)
        t.create_index(['_service_uri_'], unique=True)
    except:
        pass # index already present

    return db


def read_all(dbpath, table):
    db = DataSet(_dburl(dbpath))
    t = db[table]
    return {row['_name_']: row for row in t.all()}


def read_data(dbpath, table, name):
    db = DataSet(_dburl(dbpath))
    t = db[table]
    return t.find_one(_name_=name)


def _dburl(dbpath):
    if dbpath == 'memory':
        return 'sqlite:///:memory:'
    else:
        return 'sqlite:///' + dbpath


def _sanitize(name):
    pass
