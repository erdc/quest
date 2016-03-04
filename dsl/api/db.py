import os
from playhouse.dataset import DataSet




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
    if table not in db.tables:
        t = db[table]
        t.insert(**data)
        t.create_index(['_name_'], unique=True)
        return db

    t = db[table]
    if t.find_one(_name_=name) is not None:
        t.update(columns='_name_', **data)

    return db


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
