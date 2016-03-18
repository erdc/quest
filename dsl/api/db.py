import json
import pandas as pd
from playhouse.dataset import DataSet

from .. import util


def upsert(dbpath, table, name, dsl_metadata=None, metadata=None):
    """
    """
    # name = _sanitize(name)
    dsl_metadata['name'] = name

    if dsl_metadata is None:
        dsl_metadata = {}

    data = {'_{}'.format(k): v for k, v in dsl_metadata.items()}

    if metadata is not None:
        data.update(metadata)

    # cannot have id field in data when inserting into dataset
    if 'id' in data.keys():
        data['uid'] = data.pop('id')


    db = DataSet(_dburl(dbpath))
    t = db[table]

    if '_name' not in t.columns:
        t.insert(**data)
        t.create_index(['_name'], unique=True)
        return db

    if t.find_one(_name=name) is not None:
        t.update(columns=['_name'], **data)
    else:
        t.insert(**data)

    return db


def upsert_features(dbpath, features):
    """
    upsert pandas dataframe
    """
    db = DataSet(_dburl(dbpath))
    t = db['features']

    # peewee datasets cannot store field names with _id in them so rename
    # fields to _uid
    r = {field: field.replace('_id', '_uid') for field in features.columns}
    if 'id' in r.keys():
        r['id'] = 'uid'
    features.rename(columns=r, inplace=True)

    uris = []  # feature uris inside collection
    for uri, data in features.iterrows():
        if '_service' in data.index and '_service' in t.columns:
            row = t.find_one(
                    _service=data['_service'],
                    _service_uid=data['_service_uid'],
                    _collection=data['_collection'],
                    )
            if row is not None:
                uris.append(row['_name'])
                continue

        # make roundtrip through json to make sure all fields
        # are database friendly
        data_dict = json.loads(data.to_json(date_format='iso'))
        uri = util.uuid('feature')
        data_dict.update({'_name': uri})
        t.insert(**data_dict)
        uris.append(uri)

    try:
        t.create_index(['_name'], unique=True)
    except:
        pass  # index already present

    return uris


def read_all(dbpath, table, as_dataframe=None):
    db = DataSet(_dburl(dbpath))
    t = db[table]
    data = {row['_name']: row for row in t.all()}
    data = pd.DataFrame(data).T
    if not data.empty:
        data.index = data['_name']
        del data['id']
        r = {field: field.replace('_uid', '_id') for field in data.columns}
        if 'uid' in r.keys():
            r['uid'] = 'id'
        data.rename(columns=r, inplace=True)

    if not as_dataframe:
        data = data.to_dict(orient='index')

    return data


def read_data(dbpath, table, name):
    db = DataSet(_dburl(dbpath))
    t = db[table]
    return t.find_one(_name=name)


def _dburl(dbpath):
    if dbpath == 'memory':
        return 'sqlite:///:memory:'
    else:
        return 'sqlite:///' + dbpath


def _sanitize(name):
    pass
