from flask_wtf import Form
from wtforms import TextField, BooleanField
from models import Hint
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms_alchemy import model_form_factory

from app.task.models import Task

ModelForm = model_form_factory(Form)


def task_query():
    return Task.query.all()


class HintForm(ModelForm):
    class Meta:
        model = Hint


class CreateHintForm(Form):
    description = TextField('Description')
    is_open = BooleanField('Is Open')
    task = QuerySelectField(query_factory=task_query, get_label='name')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
