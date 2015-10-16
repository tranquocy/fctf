from flask_wtf import Form
from wtforms import TextField, SubmitField, validators, PasswordField, HiddenField
from app.user.models import User
from app.task.models import Task
from wtforms_alchemy import model_form_factory

ModelForm = model_form_factory(Form)


class UserForm(ModelForm):
    class Meta:
        model = User
        only = ['name', 'email']


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

        user = User.query.filter_by(username=self.username.data).first()
        if user and user.check_password(self.password.data):
            return True
        else:
            self.password.errors.append('Invalid username or password')
            return False


class SendForgotPasswordForm(Form):
    email = TextField('Email',  [
        validators.Length(max=40, message='email is at most 40 characters.'),
        validators.Required('Please enter your email address.'),
        validators.Email('Please enter a valid email address.')
    ])
    submit = SubmitField('Send Forgot Password Email')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        user = User.query.filter_by(email=self.email.data).first()
        if not user:
            self.email.errors.append('This email is not registered yet')
            return False
        else:
            return True


class ResetPasswordForm(Form):
    new_password = PasswordField('Password', [
        validators.Required('Please enter new password.'),
        validators.Length(min=6, message='Passwords is at least 6 characters.'),
        validators.EqualTo('new_confirm', message='Passwords must match')
    ])
    new_confirm = PasswordField('Repeat Password')
    submit = SubmitField('Reset password')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        return True


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