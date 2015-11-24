from flask import Blueprint, render_template, flash, redirect, url_for, g
from flask_login import login_required
from flask_admin.model.template import macro
from flask_admin.contrib.sqla import ModelView

from app import db
from app.team.forms import CreateTeamForm, TeamForm
from app.team.models import Team

team_module = Blueprint('team', __name__)


@team_module.route('/', methods=['GET', 'POST'])
@team_module.route('/<int:team_id>', methods=['GET', 'POST'])
@login_required
def show_team(team_id=None):
    if team_id is None:
        if g.user.team:
            return render_template('team/team.html', team=g.user.team)
        else:
            return redirect(url_for('user.profile'))
    team = Team.query.get_or_404(team_id)

    return render_template('team/team.html', team=team)


@team_module.route('/all', methods=['GET', 'POST'])
@login_required
def all_team():
    teams = Team.query.all()

    return render_template('team/all_team.html', teams=teams)


@team_module.route('/create', methods=['GET', 'POST'])
@login_required
def create_team():
    if g.user.team:
        return redirect(url_for('tea,.show_team', team_id=g.user.team.id))
    form = CreateTeamForm()
    if form.validate_on_submit():
        new_team = Team(form.name.data, form.description.data)
        g.user.team = new_team
        db.session.add(new_team)
        db.session.add(g.user)
        db.session.commit()
        flash('Team created successfully.', category='success')
        return redirect(url_for('team.show_team', team_id=g.user.team.id))
    return render_template('team/create_team.html', form=form)


@team_module.route('/<int:team_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_team(team_id=None):
    model = Team.query.get_or_404(team_id)
    if g.user not in model.members and not g.user.is_admin():
        return redirect(url_for('index'))
    form = TeamForm(obj=model)

    if form.validate_on_submit():
        form.populate_obj(model)
        db.session.add(model)
        db.session.commit()
        flash('Team updated', category='success')
        return redirect(url_for('team.show_team', team_id=model.id))
    return render_template('team/edit_team.html', team=model, form=form)


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