import hashlib
import string
import random
import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import exc
from sqlalchemy.sql import func
from werkzeug.exceptions import abort

ROLE_USER = 0
ROLE_ADMIN = 1

def get_object_or_404(model, *criterion):
    """ Snippet byVitaliy Shishorin, http://flask.pocoo.org/snippets/115/"""
    try:
        return model.query.filter(*criterion).one()
    except exc.NoResultFound, exc.MultipleResultsFound:
        abort(404)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(30), unique = True, nullable = False)
    password = db.Column(db.String(100))
    name = db.Column(db.String(50))
    email = db.Column(db.String(45))
    role = db.Column(db.SmallInteger, default = ROLE_USER)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    solved_tasks = db.relationship('Task', secondary='user_solved', backref='solved_users')

    def __init__(self, username, email, password):
        self.username = username
        self.name = username
        self.email = email.lower()
        self.set_password(password)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.username)

    def getAvatar(self, size = 160):
        email_hash = hashlib.md5(self.email).hexdigest()
        return "http://www.gravatar.com/avatar/%s?d=mm&s=%d" % (email_hash, size)

    def is_solved_task(self, task):
        if self in task.solved_users:
            return True
        if self.team and task in self.team.solved_tasks():
            return True
        return False

    def get_total_score(self):
        return sum(task.point for task in self.solved_tasks)

    def is_admin(self):
        return self.role == ROLE_ADMIN

    def is_normal_user(self):
        return self.role == ROLE_USER


class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(30), unique = True, nullable = False)
    description = db.Column(db.Text)
    invite_code = db.Column(db.String(16), unique = True, nullable = False)
    members = db.relationship('User', backref = 'team', lazy = 'dynamic')

    def __repr__(self):
        return '<Team %r>' % (self.name)

    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.invite_code = self.genInviteCode()

    @staticmethod
    def genInviteCode():
        charset = string.ascii_letters + string.digits
        return ''.join(random.choice(charset) for _ in range(32))

    def get_total_score(self):
        return sum(task.point for task in self.solved_tasks())

    def solved_tasks(self):
        tasks = []
        for user in self.members:
            tasks += user.solved_tasks
        return set(tasks)


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(255))
    description = db.Column(db.Text)
    point = db.Column(db.Integer, default=0)
    flag = db.Column(db.String(255))
    is_open = db.Column(db.Boolean)
    hints = db.relationship('Hint', backref = 'task', lazy = 'dynamic')

    def __repr__(self):
        return '<Task %r>' % (self.name)

    def __str__(self):
        return self.name

    def __init__(self, name='', description='', flag='', point = 0, is_open=False):
        self.name = name
        self.description = description
        self.point = point
        self.flag = flag
        self.is_open = is_open

class Hint(db.Model):
    __tablename__ = 'hints'
    id = db.Column(db.Integer, primary_key = True)
    description = db.Column(db.Text)
    is_open = db.Column(db.Boolean)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))

    def __repr__(self):
        return '<Hint %r>' % (self.task)

    def __init__(self, description='', is_open=False, task=None):
        self.description = description
        self.is_open = is_open
        self.task = task


class UserSolved(db.Model):
    __tablename__ = 'user_solved'
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    point = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)
    user = db.relationship("User", uselist=False, backref="solved_data")
    task = db.relationship("Task", uselist=False, backref="solved_data")

    def __init__(self, user, task):
        self.user_id = user.id
        self.team_id = user.team.id if user.team else None
        self.task_id = task.id
        self.point = task.point
        self.created_at = datetime.datetime.now()

    @staticmethod
    def get_users_score():
        raw_data = UserSolved.query.with_entities(func.sum(UserSolved.point), \
            UserSolved.user_id).group_by(UserSolved.user_id).all()
        return [(get_object_or_404(User, User.id == user_id), total_score) for total_score, user_id in raw_data]


class SubmitLogs(db.Model):
    __tablename__ = 'submit_logs'
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    flag = db.Column(db.String(255))
    created_at = db.Column(db.DateTime)
    user = db.relationship('User', backref=db.backref('log_submit', lazy = 'dynamic'))
    task = db.relationship('Task', backref=db.backref('log_submit', lazy = 'dynamic'))

    def __init__(self, user, task, flag):
        self.user_id = user.id
        self.team_id = user.team.id if user.team else None
        self.task_id = task.id
        self.flag = flag
        self.created_at = datetime.datetime.now()
