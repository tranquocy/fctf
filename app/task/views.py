from flask import Blueprint, render_template, flash, redirect, url_for, g, request
from flask_login import login_required
from flask_admin.contrib.sqla import ModelView

from app import db
from app.task.forms import CreateTaskForm, TaskForm
from app.task.models import Task, Category, TaskForTeam
from app.user.forms import SubmitFlagForm
from app.user.models import UserSolved, SubmitLogs
from app.common.utils import admin_required

task_module = Blueprint('task', __name__)


@task_module.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_task():
    form = CreateTaskForm()
    if form.validate_on_submit():
        new_task = Task(
            name=form.name.data,
            description=form.description.data,
            point=form.point.data,
            flag=form.flag.data,
            is_open=form.is_open.data,
            category=form.category.data,
        )
        db.session.add(new_task)
        db.session.commit()
        flash('Task created successfully.', category='success')
        return redirect(url_for('admin'))
    return render_template('task/create_task.html', form=form)


@task_module.route('/all', methods=['GET', 'POST'])
@login_required
def all_task():
    categories = Category.query.all()
    return render_template('task/all_task.html', categories=categories)


@task_module.route('/<int:task_id>', methods=['GET', 'POST'])
@login_required
def show_task(task_id=None):
    task = Task.query.get_or_404(task_id)
    if not task.can_access_by(g.user):
        if task.is_team_only():
            flash('This task is for selected team only', category='danger')
        return redirect(url_for('task.all_task'))
    form = SubmitFlagForm(task.id)
    if form.validate_on_submit():
        log_data = SubmitLogs(g.user, task, form.flag.data)
        db.session.add(log_data)
        db.session.commit()
        if form.flag.data == task.flag:
            if UserSolved.query.filter_by(user_id=g.user.id, task_id=task.id).first():
                flash('Correct flag but you already solved this task.', category='success')
                return redirect(url_for('task.show_task', task_id=task.id))
            elif g.user.team and task in g.user.team.solved_tasks():
                flash('Correct flag but your team-mate already solved this task.', category='success')
            else:
                flash('Correct Flag. Congrats!', category='success')
            solved_data = UserSolved(g.user, task)
            db.session.add(solved_data)
            db.session.commit()
            return redirect(url_for('task.show_task', task_id=task.id))
        else:
            flash('Wrong Flag. Bad luck. Please try harder!', category='danger')
    return render_template('task/task.html', task=task, form=form)


@task_module.route('/<int:task_id>/<string:toggle>', methods=['GET', 'POST'])
@login_required
@admin_required
def toggle_task(task_id=None, toggle=''):
    task = Task.query.get_or_404(task_id)
    if toggle not in ['open', 'close']:
        return redirect(url_for('index'))
    else:
        task.is_open = True if toggle == 'open' else False
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('admin'))


@task_module.route('/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_task(task_id=None):
    model = Task.query.get_or_404(task_id)
    form = TaskForm(obj=model)

    if form.validate_on_submit():
        form.populate_obj(model)
        db.session.add(model)
        db.session.commit()
        flash('Task updated', category='success')
        return redirect(url_for('admin'))
    return render_template('task/edit_task.html', task=model, form=form)


@task_module.route('/<int:task_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def confirm_delete_task(task_id=None):
    task = Task.query.get_or_404(task_id)
    if request.method == 'POST':
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted', category='success')
        return redirect(url_for('admin'))
    return render_template('task/confirm_delete_task.html', task=task)


class TaskForTeamView(ModelView):

    # Override displayed fields
    column_list = ('task', 'team', 'created_at')
    column_filters = ('task', 'team')

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(TaskForTeamView, self).__init__(TaskForTeam, session, **kwargs)

    def is_accessible(self):
        return g.user.is_authenticated() and g.user.is_admin()


class CategoryView(ModelView):

    # Override displayed fields
    column_list = ('id', 'name', 'description')
    column_filters = ('name', 'description')

    form_excluded_columns = ('tasks')

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(CategoryView, self).__init__(Category, session, **kwargs)

    def is_accessible(self):
        return g.user.is_authenticated() and g.user.is_admin()
