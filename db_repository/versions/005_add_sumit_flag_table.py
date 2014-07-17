from sqlalchemy import *
from migrate import *

meta = MetaData()

user_solved = Table(
    'user_solved', meta,
    Column('id', Integer, primary_key = True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('task_id', Integer, ForeignKey('tasks.id')),
    Column('team_id', Integer, ForeignKey('teams.id')),
    Column('point', Integer),
    Column('created_at', DateTime)
)

submit_log = Table(
    'submit_logs', meta,
    Column('id', Integer, primary_key = True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('task_id', Integer, ForeignKey('tasks.id')),
    Column('team_id', Integer, ForeignKey('teams.id')),
    Column('flag', String(255)),
    Column('created_at', DateTime)
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    Table('users', meta, autoload=True)
    Table('teams', meta, autoload=True)
    Table('tasks', meta, autoload=True)
    user_solved.create()
    submit_log.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    Table('users', meta, autoload=True)
    Table('teams', meta, autoload=True)
    Table('tasks', meta, autoload=True)
    user_solved.drop()
    submit_log.drop()
