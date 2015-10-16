from flask import g
from flask_wtf import Form
from wtforms import TextField, SubmitField, validators, HiddenField
from wtforms_alchemy import model_form_factory

from app import app
from app.team.models import Team

ModelForm = model_form_factory(Form)


class TeamForm(ModelForm):
    class Meta:
        model = Team
        only = ['name', 'description']


class CreateTeamForm(Form):
    name = TextField('Name',  [
        validators.Required('Please enter your team name.'),
        validators.Length(max=30, message='Team name is at most 30 characters.'),
    ])
    description = TextField('Description')
    submit = SubmitField('Create team')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        team = Team.query.filter_by(name=self.name.data).first()
        if team:
            self.name.errors.append('That team name is already taken.')
            return False
        else:
            return True


class JoinTeamForm(Form):
    invite_code = TextField('Invite Code', [
        validators.Required('Please enter invite code'),
        validators.Length(max=32, message='Invite code is at most 32 characters.'),
    ])
    submit = SubmitField('Join Team')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        team = Team.query.filter_by(invite_code=self.invite_code.data).first()
        if not team:
            self.invite_code.errors.append('The invite code is invalid.')
            return False
        elif g.user in team.members:
            self.invite_code.errors.append('You already in team.')
            return False
        elif team.members.count() >= app.config['MAX_MEMBER']:
            self.invite_code.errors.append('Team "%s" is full. Please select another team.' % team.name)
            return False
        else:
            return True


class LeaveTeamForm(Form):
    team_id = HiddenField('team_id')
    submit = SubmitField('Join Team')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        team = Team.query.get(self.team_id.data)
        if not team or g.user not in team.members:
            return False
        else:
            return True
