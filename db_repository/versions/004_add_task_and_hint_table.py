from sqlalchemy import *
from migrate import *

meta = MetaData()
task = Table(
    'tasks', meta,
    Column('id', Integer, primary_key = True),
    Column('name', String(255)),
    Column('description', Text),
    Column('point', Integer, default = 0),
    Column('flag', String(255)),
    Column('is_open', Boolean)
)

hint = Table(
    'hints', meta,
    Column('id', Integer, primary_key = True),
    Column('description', Text),
    Column('is_open', Boolean),
    Column('task_id', Integer, ForeignKey('tasks.id'))
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    task.create()
    hint.create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    hint.drop()
    task.drop()

