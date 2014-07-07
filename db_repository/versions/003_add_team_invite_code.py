from sqlalchemy import *
from migrate import *

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    table = Table('teams', meta, autoload=True)
    col = Column('invite_code', String(length=32), nullable=False)
    col.create(table, populate_default=False, unique_name='invite_code')


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    table = Table('teams', meta, autoload=True)
    col = Column('invite_code', String(length=32), nullable=False)
    col.drop(table)
