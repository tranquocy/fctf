from app import db

class Hint(db.Model):
    __tablename__ = 'hints'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    is_open = db.Column(db.Boolean)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))

    def __repr__(self):
        return '<Hint %r>' % self.task

    def __init__(self, description='', is_open=False, task=None):
        self.description = description
        self.is_open = is_open
        self.task = task
