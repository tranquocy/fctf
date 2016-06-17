import string
import random
from sqlalchemy.sql import text

from app import db
import app.user.models
from app.common.utils import compute_color_value, ordinal

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

    @staticmethod
    def get_team_points():
        results = db.session.execute(text("select team_id, sum(point) as total_point from (select team_id, task_id, max(point) as point from user_solved group by team_id, task_id) a group by team_id order by total_point desc"))
        teams_data = []
        for team_id, point in results:
            if team_id:
                team = Team.query.get(team_id)
                teams_data.append((team, point))

        return teams_data

    def get_total_score(self):
        sql = text("select sum(point) as total_point from (select team_id, task_id, point from user_solved group by team_id, task_id) a where team_id = :team_id group by team_id order by total_point desc")
        result = db.session.execute(sql, {'team_id': self.id})

        for point in result:
            return point[0] if point[0] else 0

    def get_place(self):
        place = 1
        for team, point in Team.get_team_points():
            if self == team:
                return ordinal(place)
            place += 1

        return ordinal(999)

    def solved_tasks(self):
        tasks = []
        for user in self.members:
            tasks += user.solved_tasks
        return set(tasks)

    def color_hash(self):
        return compute_color_value(str(self.id) + self.name.encode('utf-8'))
