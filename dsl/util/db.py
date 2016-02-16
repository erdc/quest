from playhouse import dataset

# project
# db.new_entry('name')


def create_metadata(dbpath, table, name, dsl_metadata=None, metadata=None):
    #name = _sanitize(name)
    if dsl_metadata is None:
        dsl_metadata = {
            'display_name': name,
            'description': ''
            }

    if table in ['projects', 'collections']:
        dsl_metadata.get('folder') is None
            dsl_metadata['folder'] = name

    data = {'_{}_'.format(k): v for k, v in dsl_metadata.items()}
    data.update(metadata)

    # cannot have id field in data when inserting into dataset
    if 'id' in data.keys():
        data['id0'] = data.pop('id')

    db = DataSet(_dburl(dbpath))
    if table not in db.tables:
        t = db[table]
        t.create_index(['_name_'], unique=True)

    t = db['table']
    t.insert(**data)


def read_metadata(dbpath, table, name):
    pass


def upsert(dbpath, table, data):
    pass


def _dburl(dbpath):
    return 'sqlite:///' + dbpath


def _sanitize(name):
    pass
