from sqlalchemy import *
from migrate import *

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    table = Table('teams', meta, autoload=True)
    cons = UniqueConstraint('name', table=table)
    cons.create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    table = Table('teams', meta, autoload=True)
    cons = UniqueConstraint('name', table=table)
    cons.drop()
