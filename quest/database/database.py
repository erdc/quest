from datetime import datetime

from pony import orm
from pony.orm import db_session
import shapely.wkt

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
        datasets = orm.Set('Dataset')

    class Dataset(db.Entity):
        name = orm.PrimaryKey(str)
        display_name = orm.Optional(str)
        description = orm.Optional(str, nullable=True)
        created_at = orm.Required(datetime, default=datetime.now())
        metadata = orm.Optional(orm.Json)
        updated_at = orm.Optional(datetime)

        # dataset - metadata
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
        collection = orm.Required(Collection)
        catalog_entry = orm.Required(str)

    class Providers(db.Entity):
        provider = orm.PrimaryKey(str)
        username = orm.Required(str)
        password = orm.Required(str)

    class QuestCatalog(db.Entity):
        service_id = orm.PrimaryKey(str)
        created_at = orm.Required(datetime, default=datetime.now())
        updated_at = orm.Optional(datetime)
        metadata = orm.Optional(orm.Json)
        geometry = orm.Optional(orm.Json)


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
    """
    Args:
    Returns:
    """
    db = orm.Database()  # create new database object
    define_models(db)  # define entities for this database
    db.bind('sqlite', dbpath, create_db=True)  # bind this database
    db.generate_mapping(create_tables=True)

    return db


def select_collections(select_func=None):
    """
    Args:
    Returns:
    """
    db = get_db()
    with db_session:
        if select_func is None:
            collections = db.Collection.select()
        else:
            collections = db.Collection.select(select_func)

        return [dict(c.to_dict(), **{'metadata': _convert_to_dict(c.metadata)
                                     }
                     ) for c in collections]


def select_datasets(select_func=None):
    """
    Args:
    Returns:
    """
    db = get_db()
    with db_session:
        if select_func is None:
            datasets = db.Dataset.select()
        else:
            datasets = db.Dataset.select(select_func)

        return [dict(d.to_dict(), **{'collection': d.collection.name,
                                     'options': _convert_to_dict(d.options),
                                     'metadata': _convert_to_dict(d.metadata),
                                     }
                     ) for d in datasets]


def select_catalog_entries(select_func=None):
    """
    Args:
    Returns:
    """
    db = get_db()
    with db_session:
        if select_func is None:
            catalog_entries = db.QuestCatalog.select()
        else:
            catalog_entries = db.QuestCatalog.select(select_func)

        return [dict(e.to_dict(), **{'geometry': None if e.geometry is None else shapely.wkt.loads(e.geometry),
                                     'metadata': _convert_to_dict(e.metadata),
                                     }
                     ) for e in catalog_entries]


def _convert_to_dict(tracked_dict):
    """
    Recursively convert a Pony ORM TrackedDict to a normal Python dict
    """
    if not isinstance(tracked_dict, orm.ormtypes.TrackedDict):
        return tracked_dict

    return {k: _convert_to_dict(v) for k, v in tracked_dict.items()}
