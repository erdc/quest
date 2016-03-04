import os
from playhouse.dataset import DataSet

# project
# db.new_entry('name')


def upsert(dbpath, table, name, dsl_metadata=None, metadata=None):
    """
    """
    # name = _sanitize(name)
    dsl_metadata['name'] = name

    if dsl_metadata is None:
        dsl_metadata = {}

    if 'display_name' not in dsl_metadata:
        dsl_metadata['display_name'] = name

    if 'description' not in dsl_metadata:
        dsl_metadata['description'] = ''

    if table in ['projects'] and dsl_metadata.get('folder') is None:
        dsl_metadata['folder'] = name

    data = {'_{}_'.format(k): v for k, v in dsl_metadata.items()}

    if metadata is not None:
        data.update(metadata)

    # cannot have id field in data when inserting into dataset
    if 'id' in data.keys():
        data['id0'] = data.pop('id')

    db = DataSet(_dburl(dbpath))
    create_index = False
    if table not in db.tables:
        create_index = True

    t = db[table]
    if t.find_one(_name_=name) is not None:
        t.update(columns='_name_', **data)
    else:
        t.insert(**data)

    if create_index:
        t.create_index(['name'], unique=True)

    return db


def read_data(dbpath, table, name):
    db = DataSet(_dburl(dbpath))
    t = db[table]
    return t.find_one(name=name)


def _dburl(dbpath):
    if dbpath == 'memory':
        return 'sqlite:///:memory:'
    else:
        return 'sqlite:///' + os.path.join(dbpath, 'dsl.db')


def _sanitize(name):
    pass
