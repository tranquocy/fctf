from flask import render_template, flash, redirect, url_for, request, abort, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from forms import LoginForm, SignupForm, CreateTeamForm, JoinTeamForm, LeaveTeamForm
from wtforms.ext.sqlalchemy.orm import model_form
from flask_wtf import Form
from models import User, Team, ROLE_USER, ROLE_ADMIN

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
        redirect(url_for('profile'))
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
        user = User.query.get(user_id)
        if user:
            return render_template('profile.html', user=user)
        else:
            abort(404)


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


@app.route('/team', methods = ['GET', 'POST'])
@app.route('/team/<int:team_id>', methods = ['GET', 'POST'])
@login_required
def team(team_id = None):
    if team_id is None:
        if g.user.team:
            return render_template('team.html', team=g.user.team)
        else:
            return redirect(url_for('profile'))

    team = Team.query.get(team_id)
    if team:
        return render_template('team.html', team=team)
    else:
        abort(404)


@app.route('/all_team', methods = ['GET', 'POST'])
@login_required
def all_team():
    teams = Team.query.all()
    return render_template('all_team.html', teams=teams)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
