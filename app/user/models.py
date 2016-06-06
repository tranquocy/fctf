import json
import hashlib
import datetime
from flask import url_for
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
from sqlalchemy.orm import backref

from app import db
from app.common.utils import generate_token
from app.user import constants as USER
from app.common.utils import compute_color_value, generate_random_string
import app.task.models
import app.team.models


class User(db.Model):

    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(100))
    name = db.Column(db.String(50))
    email = db.Column(db.String(45), unique=True, nullable=False)
    role = db.Column(db.SmallInteger, default=USER.ROLE_USER)
    is_actived = db.Column(db.SmallInteger, default=USER.UNACTIVATED)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    solved_tasks = db.relationship(app.task.models.Task, secondary='user_solved', backref='solved_users')

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
        return self.is_actived == USER.ACTIVATED

    def activate(self):
        self.is_actived = USER.ACTIVATED

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % self.username

    def __str__(self):
        return self.username

    def get_avatar_url(self, size=160):
        email_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return u'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % (email_hash, size)

    def get_avatar_img(self, size=160):
        return u'<img src="{0:s}" alt="{1:s}" title="{2:s}"/></img>'.format(self.get_avatar_url(size), self.name,
                                                                            self.name)

    def is_solved_task(self, task):
        if self in task.solved_users:
            return True
        if self.team and task in self.team.solved_tasks():
            return True
        return False

    def get_total_score(self):
        return sum(data.point for data in self.solved_data)

    def is_admin(self):
        return self.role == USER.ROLE_ADMIN

    def is_normal_user(self):
        return self.role == USER.ROLE_USER

    def get_profile_link(self, with_avatar=True):
        class_name = 'text-danger' if self.is_admin() else 'text-default'
        profile_link = url_for('user.profile', user_id=self.id)
        avatar = self.get_avatar_img(24) if with_avatar else ''
        return u'<a href="{0:s}">{1:s}&nbsp;<span class="{2:s}">{3:s}</span></a>'.format(profile_link, avatar,
                                                                                         class_name,
                                                                                         self.name)

    def color_hash(self):
        return compute_color_value(str(self.id) + self.email.encode('utf-8'))


class UserSolved(db.Model):

    __tablename__ = 'user_solved'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    point = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)
    user = db.relationship(User, uselist=False, backref="solved_data")
    task = db.relationship('app.task.models.Task', uselist=False, backref=backref("solved_data", cascade="all, delete-orphan"))
    team = db.relationship('app.team.models.Team', uselist=False, backref=backref("solved_data", cascade="all, delete-orphan"))

    def __init__(self, user, task):
        self.user_id = user.id
        self.team_id = user.team.id if user.team else None
        self.task_id = task.id
        self.point = task.point
        self.created_at = datetime.datetime.now()

    @staticmethod
    def get_users_score():
        raw_data = UserSolved.query.with_entities(func.sum(UserSolved.point),
                                                  UserSolved.user_id).group_by(UserSolved.user_id).all()
        return [(User.query.get_or_404(user_id), total_score) for total_score, user_id in raw_data if
                total_score > 0]


class UserForgotPassword(db.Model):

    __tablename__ = 'user_forgot_passwords'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    token = db.Column(db.String(40))
    expire_at = db.Column(db.DateTime, default=datetime.datetime.now() + datetime.timedelta(minutes=30))

    user = db.relationship(User, backref=db.backref('forgot_password', lazy='dynamic', cascade='all'))

    def __init__(self, user):
        self.user = user
        self.token = generate_token()

    def refresh(self):
        self.token = generate_token()
        self.expire_at = datetime.datetime.now() + datetime.timedelta(minutes=30)

    def is_expired(self):
        return datetime.datetime.now() >= self.expire_at


class UserMailActivation(db.Model):

    __tablename__ = 'user_mail_activations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    token = db.Column(db.String(40))
    expire_at = db.Column(db.DateTime, default=datetime.datetime.now() + datetime.timedelta(days=1))

    user = db.relationship('User', backref=db.backref('mail_activation', lazy='dynamic', cascade='all'))

    def __init__(self, user):
        self.user = user
        self.token = generate_token()

    def refresh(self):
        self.token = generate_token()
        self.expire_at = datetime.datetime.now() + datetime.timedelta(days=1)

    def is_expired(self):
        return datetime.datetime.now() >= self.expire_at


class SubmitLogs(db.Model):

    __tablename__ = 'submit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    flag = db.Column(db.String(255))
    created_at = db.Column(db.DateTime)
    user = db.relationship(User, backref=db.backref('log_submit', lazy='dynamic'))
    task = db.relationship('app.task.models.Task', backref=db.backref('log_submit', cascade="all, delete-orphan", lazy='dynamic'))
    team = db.relationship('app.team.models.Team', backref=db.backref('log_submit', cascade="all, delete-orphan", lazy='dynamic'))

    def __init__(self, user, task, flag):
        self.user_id = user.id
        self.team_id = user.team.id if user.team else None
        self.task_id = task.id
        self.flag = flag
        self.created_at = datetime.datetime.now()


class UserData(db.Model):

    __tablename__ = 'user_data'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    token = db.Column(db.String(64))
    data = db.Column(db.Text)
    expire_at = db.Column(db.DateTime, default=datetime.datetime.now() + datetime.timedelta(minutes=30))

    user = db.relationship('User', backref=db.backref('storage', cascade='all', uselist=False))


    def __init__(self, user):
        self.user_id = user.id
        self.token = generate_random_string(64)
        self.data = json.dumps({})

    def refresh(self):
        self.token = generate_random_string(64)        
        self.expire_at = datetime.datetime.now() + datetime.timedelta(minutes=30)

    def is_expired(self):
        return datetime.datetime.now() >= self.expire_at
