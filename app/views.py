from functools import wraps
from flask import render_template, flash, redirect, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from forms import LoginForm, SignupForm, CreateTeamForm, JoinTeamForm, LeaveTeamForm, CreateTaskForm, SubmitFlagForm, CreateHintForm
from wtforms.ext.sqlalchemy.orm import model_form
from flask_wtf import Form
from models import User, Team, Task, Hint, UserSolved, SubmitLogs, ROLE_ADMIN, get_object_or_404

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


@lm.user_loader
def load_user(userid):
    return User.query.get(int(userid))


@app.route('/')
@app.route('/index')
def index():
    return render_template(
        'index.html',
        user=g.user
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
        user = User.query.filter_by(username = form.username.data).first()
        login_user(user)
        flash('Logged in successfully.', category='success')
        return redirect(request.args.get('next') or url_for('index'))
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', category='success')
    return redirect(url_for('index'))


@app.route('/profile', methods = ['GET', 'POST'])
@app.route('/profile/<int:user_id>', methods = ['GET', 'POST'])
@login_required
def profile(user_id = None):
    if user_id is None or user_id == g.user.id:
        join_team_form = JoinTeamForm()
        leave_team_form = LeaveTeamForm()
        if join_team_form.validate_on_submit() and not g.user.team:
            team = Team.query.filter_by(invite_code = join_team_form.invite_code.data).first()
            g.user.team = team
            db.session.add(g.user)
            db.session.commit()
            flash("You've joined team <strong>%s</strong> !" % team.name, category='success')
        if leave_team_form.validate_on_submit() and g.user.team:
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
            leave_team_form=leave_team_form
        )
    else:
        user = get_object_or_404(User, User.id == user_id)
        return render_template('profile.html', user=user)


@app.route('/profile/edit', methods = ['GET', 'POST'])
@login_required
def edit_profile():
    UserForm = model_form(User, db_session=db.session,
        base_class=Form, only=['email', 'name']
    )
    model = User.query.get(g.user.id)
    form = UserForm(request.form, model)

    if form.validate_on_submit():
        form.populate_obj(model)
        db.session.add(model)
        db.session.commit()
        flash('Profile updated', category='success')
        return redirect(url_for('profile'))
    return render_template('edit_profile.html', user=g.user, form=form)


@app.route('/team/create', methods = ['GET', 'POST'])
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


@app.route('/task/create', methods = ['GET', 'POST'])
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
            is_open=form.is_open.data
        )
        db.session.add(new_task)
        db.session.commit()
        flash('Task created successfully.', category='success')
        return redirect(url_for('admin'))
    return render_template('create_task.html', form=form)


@app.route('/team', methods = ['GET', 'POST'])
@app.route('/team/<int:team_id>', methods = ['GET', 'POST'])
@login_required
def team(team_id = None):
    if team_id is None:
        if g.user.team:
            return render_template('team.html', team=g.user.team)
        else:
            return redirect(url_for('profile'))

    team = get_object_or_404(Team, Team.id == team_id)
    return render_template('team.html', team=team)


@app.route('/team/all', methods = ['GET', 'POST'])
@login_required
def all_team():
    teams = Team.query.all()
    return render_template('all_team.html', teams=teams)


@app.route('/task/all', methods = ['GET', 'POST'])
@login_required
def all_task():
    tasks = Task.query.all()
    return render_template('all_task.html', tasks=tasks)


@app.route('/task/<int:task_id>', methods = ['GET', 'POST'])
@login_required
def task(task_id = None):
    task = get_object_or_404(Task, Task.id == task_id)
    form = SubmitFlagForm(task.id)
    if form.validate_on_submit():
        log_data = SubmitLogs(g.user, task, form.flag.data)
        db.session.add(log_data)
        db.session.commit()
        task = Task.query.get(form.task_id.data)
        if form.flag.data == task.flag:
            if g.user.team and UserSolved.query.filter_by(team_id = g.user.team.id, task_id = task.id).first():
                flash('Your team-mate already solved this task.', category='success')
                return redirect(url_for('task', task_id=task.id))
            elif UserSolved.query.filter_by(user_id = g.user.id, task_id = task.id).first():
                flash('Your already solved this task.', category='success')
                return redirect(url_for('task', task_id=task.id))
            else:
                solved_data = UserSolved(g.user, task)
                db.session.add(solved_data)
                db.session.commit()
                flash('Correct Flag. Congrats!', category='success')
                return redirect(url_for('task', task_id=task.id))
        else:
            flash('Wrong Flag. Bad luck!', category='danger')
    return render_template('task.html', task=task, form=form)


@app.route('/task/<int:task_id>/<string:toggle>', methods = ['GET', 'POST'])
@login_required
@admin_required
def toggle_task(task_id = None, toggle = ''):
    task = get_object_or_404(Task, Task.id == task_id)
    if toggle not in ['open', 'close']:
        return redirect(url_for('index'))
    else:
        task.is_open = True if toggle == 'open' else False
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('admin'))


@app.route('/task/<int:task_id>/edit', methods = ['GET', 'POST'])
@login_required
@admin_required
def edit_task(task_id = None):
    model = get_object_or_404(Task, Task.id == task_id)
    TaskForm = model_form(Task, db_session=db.session, base_class=Form)
    form = TaskForm(request.form, model)

    if form.validate_on_submit():
        form.populate_obj(model)
        db.session.add(model)
        db.session.commit()
        flash('Task updated', category='success')
        return redirect(url_for('admin'))
    return render_template('edit_task.html', task=model, form=form)


@app.route('/task/<int:task_id>/delete', methods = ['GET', 'POST'])
@login_required
@admin_required
def confirm_delete_task(task_id = None):
    task = get_object_or_404(Task, Task.id == task_id)
    print task
    if request.method == 'POST':
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted', category='success')
        return redirect(url_for('admin'))
    return render_template('confirm_delete_task.html', task=task)


@app.route('/hint/create', methods = ['GET', 'POST'])
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


@app.route('/hint/<int:hint_id>/edit', methods = ['GET', 'POST'])
@login_required
@admin_required
def edit_hint(hint_id = None):
    model = get_object_or_404(Hint, Hint.id == hint_id)
    HintForm = model_form(Hint, db_session=db.session, base_class=Form)
    form = HintForm(request.form, model)

    if form.validate_on_submit():
        form.populate_obj(model)
        db.session.add(model)
        db.session.commit()
        flash('Hint updated', category='success')
        return redirect(url_for('task', task_id=model.task.id))
    return render_template('edit_hint.html', task=model, form=form)


@app.route('/admin', methods = ['GET', 'POST'])
@login_required
@admin_required
def admin():
    teams = Team.query.all()
    users = User.query.all()
    tasks = Task.query.all()
    return render_template('admin.html', teams=teams, users=users, tasks=tasks)


@app.route('/scoreboard', methods = ['GET', 'POST'])
@login_required
def scoreboard():
    users_data = sorted(UserSolved.get_users_score(), key=lambda data: data[1], reverse=True)
    max_user_score = 0
    if len(users_data):
        max_user_score = max(users_data, key=lambda data: data[1])[1]
    teams = Team.query.all()
    teams_data = []
    for team in teams:
        score = 0
        for user in team.members:
            score += sum([task.point for task in user.solved_tasks])
        teams_data.append((team, score))
    max_team_score = 0
    if len(teams_data):
        max_team_score = max(teams_data, key=lambda data: data[1])[1]
    return render_template('scoreboard.html',
        users_data=users_data, teams_data=teams_data,
        max_user_score=max_user_score, max_team_score=max_team_score
    )


@app.route('/admin/log_submit/<int:page>', methods = ['GET', 'POST'])
@login_required
@admin_required
def log_submit(page = 1):
    logs = SubmitLogs.query.paginate(page, per_page=100, error_out=True)
    return render_template('log_submit.html', logs=logs)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
