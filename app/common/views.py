from flask import Blueprint, render_template, request, g, send_from_directory, abort, jsonify
from flask_login import current_user, login_required
from sqlalchemy import desc

from app import app, db, lm
from app.common.utils import compute_sign_hash, set_all_cookie, delete_all_cookie, admin_required
from app.user.models import User, UserSolved, SubmitLogs
from app.team.models import Team
from app.task.models import Task, Category


@app.before_request
def before_request():
    g.user = current_user
    g.cookie = request.cookies.get('ss_sign')


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
        'common/activities.html',
        activities=activities,
        user=g.user
    )


@app.route('/')
@app.route('/index')
def index():
    return render_template(
        'common/index.html',
    )


@app.route('/about')
def about():
    return render_template(
        'common/about.html',
    )

@app.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin():
    teams = Team.query.all()
    users = User.query.all()
    tasks = Task.query.all()
    return render_template('common/admin.html', teams=teams, users=users, tasks=tasks)


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
    return render_template('common/scoreboard.html',
                           users_data=users_data, teams_data=teams_data,
                           max_user_score=max_user_score, max_team_score=max_team_score
    )


@app.route('/admin/log_submit/<int:page>', methods=['GET', 'POST'])
@login_required
@admin_required
def log_submit(page=1):
    logs = SubmitLogs.query.order_by(desc(SubmitLogs.created_at)). \
        paginate(page, per_page=100, error_out=True)
    return render_template('common/log_submit.html', logs=logs)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/uploads/<path:filename>')
def download_file(filename):
    if '..' in filename or filename.startswith('/'):
        abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
