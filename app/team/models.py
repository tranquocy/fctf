import string
import random

from app import db
import app.user.models

class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.Text)
    invite_code = db.Column(db.String(16), unique=True, nullable=False)
    members = db.relationship('User', backref='team', lazy='dynamic')
    team_only_tasks = db.relationship('app.task.models.Task', secondary='task_for_teams', backref='for_teams')

    def __repr__(self):
        return '<Team %r>' % self.name

    def __str__(self):
        return self.name

    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.invite_code = self.generate_invite_code()

    @staticmethod
    def generate_invite_code():
        charset = string.ascii_letters + string.digits
        return ''.join(random.choice(charset) for _ in range(16))

    def get_total_score(self):
        total = 0
        for task in self.solved_tasks():
            results = app.user.models.UserSolved.query.filter(app.user.models.UserSolved.task == task).all()
            total += max([data.point for data in results if data.user in task.solved_users])
        return total

    def solved_tasks(self):
        tasks = []
        for user in self.members:
            tasks += user.solved_tasks
        return set(tasks)
