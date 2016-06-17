from sqlalchemy.orm import backref

from app import app, db
import app.hint.models
import app.team.models

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    description = db.Column(db.Text)
    point = db.Column(db.Integer, default=0)
    flag = db.Column(db.String(255))
    is_open = db.Column(db.Boolean)
    hints = db.relationship(app.hint.models.Hint, backref=backref('task'), lazy='dynamic')
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    def __repr__(self):
        return '<Task %r>' % self.name

    def __str__(self):
        return self.name

    def is_team_only(self):
        return self.task_for_team_data

    def __init__(self, name='', description='', flag='', point=0, is_open=False, category=None):
        self.name = name
        self.description = description
        self.point = point
        self.flag = flag
        self.is_open = is_open
        self.category = category

    def can_access_by(self, user):
        if user.is_admin():
            return True
        if self.is_team_only():
            return user.team in self.for_teams and self.is_open
        else:
            return self.is_open

    def can_access_by_team(self, team):
        if not self.is_team_only():
            return True
        else:
            return team in self.for_teams


class TaskForTeam(db.Model):
    __tablename__ = 'task_for_teams'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    created_at = db.Column(db.DateTime)
    task = db.relationship(Task, uselist=False, backref=backref("task_for_team_data", cascade="all, delete-orphan"))
    team = db.relationship(app.team.models.Team, uselist=False, backref="task_for_team_data")


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    description = db.Column(db.Text)
    tasks = db.relationship(Task, backref='category', lazy='dynamic')

    def __repr__(self):
        return '<Category %r>' % self.name

    def __str__(self):
        return self.name

    def is_achievement(self):
        return self.description == "ac"
