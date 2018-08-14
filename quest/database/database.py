from datetime import datetime
from pony import orm
from pony.orm import db_session

_connection = None  # global var to hold persistant db connection

def define_models(db):

    class Project(db.Entity):
        display_name = orm.Optional(str)
        description = orm.Optional(str)
        created_at = orm.Required(datetime, default=datetime.now())
        updated_at = orm.Optional(datetime)
        metadata = orm.Optional(orm.Json)

    class Collection(db.Entity):
        name = orm.PrimaryKey(str)
        display_name = orm.Optional(str)
        description = orm.Optional(str)
        created_at = orm.Required(datetime, default=datetime.now())
        updated_at = orm.Optional(datetime)
        metadata = orm.Optional(orm.Json)

        # setup relationships
        features = orm.Set('Feature')

    class Feature(db.Entity):
        name = orm.PrimaryKey(str)
        display_name = orm.Optional(str)
        description = orm.Optional(str)
        created_at = orm.Required(datetime, default=datetime.now())
        updated_at = orm.Optional(datetime)
        geometry = orm.Optional(orm.Json)

        metadata = orm.Optional(orm.Json)
        service = orm.Optional(str)
        service_id = orm.Optional(str)
        reserved = orm.Optional(orm.Json)
        parameters = orm.Optional(orm.Json)

        # setup relationships
        collection = orm.Required(Collection)
        datasets = orm.Set('Dataset')

    class Dataset(db.Entity):
        name = orm.PrimaryKey(str)
        display_name = orm.Optional(str)
        description = orm.Optional(str, nullable=True)
        created_at = orm.Required(datetime, default=datetime.now())
        updated_at = orm.Optional(datetime)
        metadata = orm.Optional(orm.Json)

        # dataset require metadata
        parameter = orm.Optional(orm.Json)
        unit = orm.Optional(str)
        datatype = orm.Optional(str)
        file_format = orm.Optional(str)
        source = orm.Optional(str)
        options = orm.Optional(orm.Json)
        status = orm.Optional(str)
        message = orm.Optional(str)
        file_path = orm.Optional(str, nullable=True)
        visualization_path = orm.Optional(str)

        # setup relationships
        feature = orm.Required(Feature)

    class Providers(db.Entity):
        provider = orm.PrimaryKey(str)
        username = orm.Required(str)
        password = orm.Required(str)


def get_db(dbpath=None, reconnect=False):
    """Get database object.

       Args:
          dbpath (string, Optional, Default=None):
            path to the database

            dbpath must be set at least once in a session before being called without arguments

          reconnect (bool, Optional, Default=None):
            if True, reconnect to the database

       Returns:
           database (object):
               database object
       """
    global _connection
    if _connection:
        if reconnect is False:
            return _connection
        else:
            _connection.disconnect()

    if dbpath is None:
        from ..api.projects import active_db
        dbpath = active_db()

    _connection = init_db(dbpath)

    return _connection


def init_db(dbpath):
    db = orm.Database()  # create new database object
    define_models(db)  # define entities for this database
    db.bind('sqlite', dbpath, create_db=True)  # bind this database
    db.generate_mapping(create_tables=True)

    return db


def select_collections(select_func=None):
    db = get_db()
    with db_session:
        if select_func is None:
            collections = db.Collection.select()
        else:
            collections = db.Collection.select(select_func)

        return [dict(c.to_dict(), **{'metadata': _convert_to_dict(c.metadata)
                                     }
                     ) for c in collections]


def select_features(select_func=None):
    db = get_db()
    with db_session:
        if select_func is None:
            features = db.Feature.select()
        else:
            features = db.Feature.select(select_func)

        return [dict(f.to_dict(), **{'metadata': _convert_to_dict(f.metadata),
                                     'reserved': _convert_to_dict(f.reserved),
                                     }
                     ) for f in features]


def select_datasets(select_func=None):
    db = get_db()
    with db_session:
        if select_func is None:
            datasets = db.Dataset.select()
        else:
            datasets = db.Dataset.select(select_func)

        return [dict(d.to_dict(), **{'collection': d.feature.collection.name,
                                     'options': _convert_to_dict(d.options),
                                     'metadata': _convert_to_dict(d.metadata),
                                     }
                     ) for d in datasets]


def _convert_to_dict(tracked_dict):
    """
    Recursively convert a Pony ORM TrackedDict to a normal Python dict
    """
    if not isinstance(tracked_dict, orm.ormtypes.TrackedDict):
        return tracked_dict

    return {k: _convert_to_dict(v) for k, v in tracked_dict.items()}
