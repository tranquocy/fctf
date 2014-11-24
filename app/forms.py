from app import app
from flask import g
from flask_wtf import Form
from wtforms import TextField, SubmitField, validators, PasswordField, HiddenField, BooleanField, IntegerField, FormField
from models import User, Team, Task, Hint
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms_alchemy import model_form_factory, ModelFieldList, ModelFormField
ModelForm = model_form_factory(Form)


class SignupForm(Form):
    username = TextField('Username',  [
        validators.Required('Please enter your username.'),
        validators.Length(max=30, message='Username is at most 30 characters.'),
    ])
    email = TextField('Email',  [
        validators.Required('Please enter your email address.'),
        validators.Email('Please enter your email address.')
    ])
    password = PasswordField('Password', [
        validators.Required('Please enter a password.'),
        validators.Length(min=6, message='Passwords is at least 6 characters.'),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    submit = SubmitField('Create account')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        user = User.query.filter_by(username=self.username.data).first()
        if user:
            self.username.errors.append('That username is already taken.')
            return False
        user_email = User.query.filter_by(email=self.email.data).first()
        if user_email:
            self.username.errors.append('That email is already taken.')
            return False

        return True


class ChangePasswordForm(Form):
    new_password = PasswordField('Password', [
        validators.Required('Please enter new password.'),
        validators.Length(min=6, message='Passwords is at least 6 characters.'),
        validators.EqualTo('new_confirm', message='Passwords must match')
    ])
    new_confirm = PasswordField('Repeat Password')
    submit = SubmitField('Change password')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        return True


class LoginForm(Form):
    username = TextField('Username',  [
        validators.Required('Please enter your username.'),
        validators.Length(max=30, message='Username is at most 30 characters.'),
    ])
    password = PasswordField('Password', [
        validators.Required('Please enter a password.'),
        validators.Length(min=6, message='Passwords is at least 6 characters.'),
    ])
    submit = SubmitField('Sign In')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        user = User.query.filter_by(username = self.username.data).first()
        if user and user.check_password(self.password.data):
            return True
        else:
            self.password.errors.append('Invalid e-mail or password')
            return False


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

        team = Team.query.filter_by(invite_code = self.invite_code.data).first()
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


class CreateTaskForm(Form):
    name = TextField('Name',  [
        validators.Required('Please enter task name.'),
        validators.Length(max=255, message='Task name is at most 255 characters.'),
    ])
    point = IntegerField('Point')
    description = TextField('Description')
    flag = TextField('Flag')
    is_open = BooleanField('Is Open')
    submit = SubmitField('Create task')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)


class SubmitFlagForm(Form):
    flag = TextField('Flag',  [
        validators.Required('Please enter the flag'),
        validators.Length(max=255, message='Flag is at most 255 characters.'),
    ])
    task_id = HiddenField('task_id')
    submit = SubmitField('Submit')

    def __init__(self, task_id):
        Form.__init__(self)
        self.task_id.data = task_id

    def validate(self):
        if not Form.validate(self):
            return False

        task = Task.query.get(self.task_id.data)
        if not task or not task.is_open:
            self.task_id.errors.append('The submitted task is invalid.')
        else:
            return True


def task_query():
    return Task.query.all()


class CreateHintForm(Form):
    description = TextField('Description')
    is_open = BooleanField('Is Open')
    task = QuerySelectField(query_factory=task_query, get_label='name')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)


class TeamForm(ModelForm):
    class Meta:
        model = Team
        only = ['name', 'description']


class UserForm(ModelForm):
    class Meta:
        model = User
        only = ['name', 'email']


class TaskForm(ModelForm):
    class Meta:
        model = Task


class HintForm(ModelForm):
    class Meta:
        model = Hint
