from flask_wtf import Form
from wtforms import TextField, SubmitField, validators, IntegerField, BooleanField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms_alchemy import model_form_factory

from app.task.models import Task, Category

ModelForm = model_form_factory(Form)


def category_query():
    return Category.query.all()


class CreateTaskForm(Form):
    name = TextField('Name',  [
        validators.Required('Please enter task name.'),
        validators.Length(max=255, message='Task name is at most 255 characters.'),
    ])
    category = QuerySelectField(query_factory=category_query, get_label='name')
    point = IntegerField('Point')
    description = TextField('Description')
    flag = TextField('Flag')
    is_open = BooleanField('Is Open')
    submit = SubmitField('Create task')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)


class TaskForm(ModelForm):
    class Meta:
        model = Task

    category = QuerySelectField(query_factory=category_query, get_label='name')
