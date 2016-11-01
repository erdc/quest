from datetime import datetime
from pony import orm
from pony.orm import db_session

db = None

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
        parameters = orm.Optional(orm.Json)

        # setup relationships
        collection = orm.Required(Collection)
        datasets = orm.Set('Dataset')

    class Dataset(db.Entity):
        name = orm.PrimaryKey(str)
        display_name = orm.Optional(str)
        description = orm.Optional(str)
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
        file_path = orm.Optional(str)
        visualization_path = orm.Optional(str)
        parent_datasets = orm.Optional(orm.Json)

        # setup relationships
        feature = orm.Required(Feature)


def connect(dbpath, reconnect=False):
    global db
    if db:
        if reconnect is False:
            return db
        else:
            db.disconnect()

    db = orm.Database()  # create new database object
    define_models(db)  # define entities for this database
    db.bind('sqlite', dbpath, create_db=True)  # bind this database
    db.generate_mapping(create_tables=True)

    return db
