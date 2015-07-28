import json
from Crypto.Cipher import AES
from functools import wraps
from flask import render_template, flash, redirect, url_for, request, g, make_response, send_from_directory, abort, jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, EncodeAES, DecodeAES
from forms import LoginForm, SignupForm, CreateTeamForm, JoinTeamForm, LeaveTeamForm, CreateTaskForm, SubmitFlagForm, \
    CreateHintForm, TeamForm, UserForm, ChangePasswordForm, HintForm, TaskForm, SendForgotPasswordForm, ResetPasswordForm
from models import User, Team, Task, Hint, UserSolved, SubmitLogs, ROLE_ADMIN, get_object_or_404, TaskForTeam, Category, UserForgotPassword
from sqlalchemy import desc
from flask.ext.admin.contrib.sqla import ModelView
from hashlib import md5
import time
import math
from utils import generate_token, send_email
from flask_admin.model.template import macro

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user or g.user.role != ROLE_ADMIN:
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function


@app.before_request
def before_request():
    g.user = current_user
    g.cookie = request.cookies.get('ss_sign')


def set_all_cookie(response, sign_cookie):
    response.set_cookie('ss_sign', sign_cookie)
    response.set_cookie('ss_user_id', str(g.user.id))
    response.set_cookie('ss_user_name', g.user.name)
    if g.user.team:
        response.set_cookie('ss_team_name', g.user.team.name)
    else:
        response.set_cookie('ss_team_name', g.user.name)


def delete_all_cookie(response):
    response.delete_cookie('ss_sign')
    response.delete_cookie('ss_user_id')
    response.delete_cookie('ss_user_name')
    response.delete_cookie('ss_team_name')


@app.after_request
def set_encrypted_cookie(response):
    if g.user.is_authenticated():
        if not g.cookie or g.cookie != compute_sign_hash([str(g.user.id)]):
            g.cookie = compute_sign_hash([str(g.user.id)])
            set_all_cookie(response, g.cookie)
    elif g.cookie:
        delete_all_cookie(response)
    return response


@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/activities')
@login_required
def show_activities():
    activities = UserSolved.query.order_by(desc(UserSolved.created_at)).limit(50).all()
    return render_template(
        'activities.html',
        activities=activities,
        user=g.user
    )


@app.route('/')
@app.route('/index')
def index():
    return render_template(
        'index.html',
    )


@app.route('/about')
def about():
    return render_template(
        'about.html',
    )


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        new_user = User(form.username.data, form.email.data, form.password.data)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash('Signed up successfully.', category='success')
        return redirect(url_for('profile'))
    return render_template('signup.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        # login and validate the user...
        user = User.query.filter_by(username=form.username.data).first()
        login_user(user)
        flash('Logged in successfully.', category='success')
        return redirect(request.args.get('next') or url_for('index'))
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', category='success')
    resp = make_response(redirect(url_for('index')))
    resp.delete_cookie('ss_sign')
    return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
def profile(user_id=None):
    if user_id is None or user_id == g.user.id:
        join_team_form = JoinTeamForm()
        leave_team_form = LeaveTeamForm()
        if not app.config['LOCK_TEAM']:
            if join_team_form.invite_code.data and join_team_form.validate_on_submit() and not g.user.team:
                team = Team.query.filter_by(invite_code=join_team_form.invite_code.data).first()
                g.user.team = team
                db.session.add(g.user)
                db.session.commit()
                flash("You've joined team <strong>%s</strong> !" % team.name, category='success')
            if leave_team_form.team_id.data and leave_team_form.validate_on_submit() and g.user.team:
                team = Team.query.get(leave_team_form.team_id.data)
                if g.user.team == team:
                    g.user.team = None
                    db.session.add(g.user)
                    db.session.commit()
                    flash("You've left team <strong>%s</strong> !" % team.name, category='success')

        return render_template(
            'profile.html',
            user=g.user,
            join_team_form=join_team_form,
            leave_team_form=leave_team_form,
            locked_team=app.config['LOCK_TEAM'],
            locked_profile=app.config['LOCK_PROFILE']
        )
    else:
        user = get_object_or_404(User, User.id == user_id)
        return render_template('profile.html', user=user)


@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if app.config['LOCK_PROFILE']:
        return redirect(url_for('index'))
    model = User.query.get(g.user.id)
    form = UserForm(obj=model)

    if form.validate_on_submit():
        form.populate_obj(model)
        db.session.add(model)
        db.session.commit()
        flash('Profile updated', category='success')
        return redirect(url_for('profile'))
    return render_template('edit_profile.html', user=g.user, form=form)


@app.route('/change_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def change_password(user_id=None):
    if g.user.is_admin():
        user = get_object_or_404(User, User.id == user_id)
    else:
        user = User.query.get(g.user.id)
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.add(user)
        db.session.commit()
        flash('Password changed successfully.', category='success')
        return redirect(url_for('profile', user_id=user.id))
    return render_template('change_password.html', user=user, form=form)


@app.route('/password/forgot', methods=['GET', 'POST'])
def forgot_password():
    form = SendForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        user_forgot_password = UserForgotPassword.query.filter_by(user_id=user.id).first()
        if not user_forgot_password:
            user_forgot_password = UserForgotPassword(user)
        else:
            user_forgot_password.refresh()
        db.session.add(user_forgot_password)
        db.session.commit()

        token = user_forgot_password.token.encode('base64').strip().replace('=', '_')
        send_email(
            'Framgia CTF - Reset Password',
            app.config['MAIL_SENDERS']['admin'],
            [user.email],
            'reset_password',
            dict(token=token)
        )
        flash('Reset password mail sent.', category='success')
        return render_template('reset_password_sent.html', user=user)

    return render_template('forgot_password.html', form=form)


@app.route('/password/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        token = token.replace('_', '=').decode('base64')
    except Exception, e:
        abort(404)
    user_forgot_password = UserForgotPassword.query.filter_by(token=token).first_or_404()

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user_forgot_password.user.set_password(form.new_password.data)
        user_forgot_password.refresh()
        db.session.add(user_forgot_password)
        db.session.commit()
        flash('Password changed successfully.', category='success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', form=form, username=user_forgot_password.user.username)


@app.route('/team/create', methods=['GET', 'POST'])
@login_required
def create_team():
    if g.user.team:
        return redirect(url_for('team', team_id=g.user.team.id))
    form = CreateTeamForm()
    if form.validate_on_submit():
        new_team = Team(form.name.data, form.description.data)
        g.user.team = new_team
        db.session.add(new_team)
        db.session.add(g.user)
        db.session.commit()
        flash('Team created successfully.', category='success')
        return redirect(url_for('team', team_id=g.user.team.id))
    return render_template('create_team.html', form=form)


@app.route('/team/<int:team_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_team(team_id=None):
    model = get_object_or_404(Team, Team.id == team_id)
    if g.user not in model.members and not g.user.is_admin():
        return redirect(url_for('index'))
    form = TeamForm(obj=model)

    if form.validate_on_submit():
        form.populate_obj(model)
        db.session.add(model)
        db.session.commit()
        flash('Team updated', category='success')
        return redirect(url_for('team', team_id=model.id))
    return render_template('edit_team.html', team=model, form=form)


@app.route('/task/create', methods=['GET', 'POST'])
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
    return render_template('create_task.html', form=form)


@app.route('/team', methods=['GET', 'POST'])
@app.route('/team/<int:team_id>', methods=['GET', 'POST'])
@login_required
def team(team_id=None):
    if team_id is None:
        if g.user.team:
            return render_template('team.html', team=g.user.team)
        else:
            return redirect(url_for('profile'))

    team = get_object_or_404(Team, Team.id == team_id)
    return render_template('team.html', team=team)


@app.route('/team/all', methods=['GET', 'POST'])
@login_required
def all_team():
    teams = Team.query.all()
    return render_template('all_team.html', teams=teams)


@app.route('/task/all', methods=['GET', 'POST'])
@login_required
def all_task():
    categories = Category.query.all()
    return render_template('all_task.html', categories=categories)


@app.route('/task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def task(task_id=None):
    task = get_object_or_404(Task, Task.id == task_id)
    if not task.can_access_by(g.user):
        if task.is_team_only():
            flash('This task is for selected team only', category='danger')
        return redirect(url_for('all_task'))
    form = SubmitFlagForm(task.id)
    if form.validate_on_submit():
        log_data = SubmitLogs(g.user, task, form.flag.data)
        db.session.add(log_data)
        db.session.commit()
        if form.flag.data == task.flag:
            if UserSolved.query.filter_by(user_id=g.user.id, task_id=task.id).first():
                flash('Correct flag but you already solved this task.', category='success')
                return redirect(url_for('task', task_id=task.id))
            elif g.user.team and task in g.user.team.solved_tasks():
                flash('Correct flag but your team-mate already solved this task.', category='success')
            else:
                flash('Correct Flag. Congrats!', category='success')
            solved_data = UserSolved(g.user, task)
            db.session.add(solved_data)
            db.session.commit()
            return redirect(url_for('task', task_id=task.id))
        else:
            flash('Wrong Flag. Bad luck. Please try harder!', category='danger')
    return render_template('task.html', task=task, form=form)


@app.route('/task/<int:task_id>/<string:toggle>', methods=['GET', 'POST'])
@login_required
@admin_required
def toggle_task(task_id=None, toggle=''):
    task = get_object_or_404(Task, Task.id == task_id)
    if toggle not in ['open', 'close']:
        return redirect(url_for('index'))
    else:
        task.is_open = True if toggle == 'open' else False
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('admin'))


@app.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_task(task_id=None):
    model = get_object_or_404(Task, Task.id == task_id)
    form = TaskForm(obj=model)

    if form.validate_on_submit():
        form.populate_obj(model)
        db.session.add(model)
        db.session.commit()
        flash('Task updated', category='success')
        return redirect(url_for('admin'))
    return render_template('edit_task.html', task=model, form=form)


@app.route('/task/<int:task_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def confirm_delete_task(task_id=None):
    task = get_object_or_404(Task, Task.id == task_id)
    if request.method == 'POST':
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted', category='success')
        return redirect(url_for('admin'))
    return render_template('confirm_delete_task.html', task=task)


@app.route('/hint/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_hint():
    form = CreateHintForm()
    if form.validate_on_submit():
        new_hint = Hint(form.description.data, form.is_open.data, form.task.data)
        db.session.add(new_hint)
        db.session.commit()
        flash('Hint created successfully.', category='success')
        return redirect(url_for('task', task_id=form.task.data.id))
    return render_template('create_hint.html', form=form)


@app.route('/hint/<int:hint_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_hint(hint_id=None):
    model = get_object_or_404(Hint, Hint.id == hint_id)
    form = HintForm(obj=model)

    if form.validate_on_submit():
        form.populate_obj(model)
        db.session.add(model)
        db.session.commit()
        flash('Hint updated', category='success')
        return redirect(url_for('task', task_id=model.task.id))
    return render_template('edit_hint.html', task=model, form=form)


@app.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin():
    teams = Team.query.all()
    users = User.query.all()
    tasks = Task.query.all()
    return render_template('admin.html', teams=teams, users=users, tasks=tasks)


@app.route('/scoreboard', methods=['GET', 'POST'])
@login_required
def scoreboard():
    users_data = sorted(UserSolved.get_users_score(), key=lambda data: data[1], reverse=True)
    max_user_score = 0
    if len(users_data):
        max_user_score = max(users_data, key=lambda data: data[1])[1]
    teams = Team.query.all()
    teams_data = []

    for team in teams:
        if team.get_total_score():
            teams_data.append((team, team.get_total_score()))
    teams_data = sorted(teams_data, key=lambda data: data[1], reverse=True)
    max_team_score = 0
    if len(teams_data):
        max_team_score = max(teams_data, key=lambda data: data[1])[1]
    return render_template('scoreboard.html',
                           users_data=users_data, teams_data=teams_data,
                           max_user_score=max_user_score, max_team_score=max_team_score
    )


@app.route('/admin/log_submit/<int:page>', methods=['GET', 'POST'])
@login_required
@admin_required
def log_submit(page=1):
    logs = SubmitLogs.query.order_by(desc(SubmitLogs.created_at)). \
        paginate(page, per_page=100, error_out=True)
    return render_template('log_submit.html', logs=logs)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/uploads/<path:filename>')
def download_file(filename):
    if '..' in filename or filename.startswith('/'):
        abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


# admin pages
class UserView(ModelView):
    # Disable model creation
    can_create = False

    # Override displayed fields
    column_list = ('username', 'name', 'email', 'team', 'role')
    column_filters = ('username', 'name', 'email', 'team')

    form_excluded_columns = ('solved_tasks', 'solved_data', 'password', 'log_submit')

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(UserView, self).__init__(User, session, **kwargs)

    def is_accessible(self):
        return g.user.is_authenticated() and g.user.is_admin()


class TeamView(ModelView):
    # Override displayed fields
    column_list = ('name', 'description', 'invite_code', 'members')
    column_filters = ('name', 'description', 'invite_code', 'members')

    form_excluded_columns = ('task_for_team_data', 'team_only_tasks')

    column_formatters = dict(members=macro('render_members'))

    list_template = 'admin/team_list.html'

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(TeamView, self).__init__(Team, session, **kwargs)

    def is_accessible(self):
        return g.user.is_authenticated() and g.user.is_admin()


class SubmitLogView(ModelView):
    # Disable model creation
    can_create = False
    can_edit = False

    # Override displayed fields
    column_list = ('user', 'flag', 'task', 'user.team', 'created_at')
    column_filters = ('user', 'task', 'created_at')

    column_default_sort = ('created_at', True)

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(SubmitLogView, self).__init__(SubmitLogs, session, **kwargs)

    def is_accessible(self):
        return g.user.is_authenticated() and g.user.is_admin()


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


def compute_sign_hash(values):
    values.append(app.config['AES_KEY'])
    raw = '_'.join(values)
    return md5(raw).hexdigest()


# API
@app.route('/api/v1/get_result', methods=['GET'])
def get_result():
    resp = {'success': 0}
    user = User.query.get(request.args.get('user_id', ''))
    code = request.args.get('code', '')
    task_type = request.args.get('type', '').lower()
    category = Category.query.filter(Category.description == task_type).first()
    if category and user and compute_sign_hash([str(user.id), task_type]) == code:
        if user.team:
            resp['solved'] = [t in user.team.solved_tasks() for t in category.tasks if t.can_access_by_team(user.team)]
        else:
            resp['solved'] = [t in user.solved_tasks for t in category.tasks if t.can_access_by(user)]
        resp['success'] = 1
    else:
        pass
    return jsonify(resp)

@app.route('/api/v1/post_result', methods=['GET'])
def post_result():
    resp = {'success': 0}
    user = User.query.get(request.args.get('user_id', ''))
    task = Task.query.get(request.args.get('task_id', ''))
    timestamp = request.args.get('time', '')
    code = request.args.get('code', '')
    if task and user and timestamp and compute_sign_hash([str(user.id), str(task.id), timestamp]) == code:
        if (user.team and task not in user.team.solved_tasks()) or task not in user.solved_tasks:
            log_data = SubmitLogs(user, task, '########[API-CENSORED]########')
            db.session.add(log_data)
            solved_data = UserSolved(user, task)
            db.session.add(solved_data)
            db.session.commit()
            resp['success'] = 1

    return jsonify(resp)