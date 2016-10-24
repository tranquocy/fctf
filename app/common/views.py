
from flask import Blueprint, render_template, request, g, send_from_directory, abort, jsonify, url_for
from flask_login import current_user, login_required
from sqlalchemy import desc, asc

from app import app, db, lm
from app.common.utils import compute_sign_hash, set_all_cookie, delete_all_cookie, admin_required
from app.user.models import User, UserSolved, SubmitLogs
from app.team.models import Team
from app.task.models import Task, Category
from app.common.achievements import ACHIEVEMENT_CFGS as AC_CFGS


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
    activities = UserSolved.query.order_by(desc(UserSolved.id)).limit(20).all()
    return render_template(
        'common/activities.html',
        activities=activities,
        user=g.user
    )

@app.route('/activities/more', methods=['POST'])
@login_required
def more_activities():
    last_id = request.form.get('id')
    activities = UserSolved.query.filter(UserSolved.id < last_id).order_by(desc(UserSolved.id)).limit(20).all()
    resp = []
    for activity in activities:
        item = {
            'id': activity.id,
            'time': activity.created_at.strftime('%b %d %H:%M'),
            'avatar': activity.user.get_avatar_url(64),
            'profile': activity.user.get_profile_link(False),
            'team': "<span>%s</span>" % activity.user.team.name if activity.user.team else "",
        }

        if not activity.task.category.is_achievement():
            item['body'] = u'<p> solved task <a href="{0:s}">{1:s}</a> and scored <strong>{2:s} points</strong></p>'.format(url_for('task.show_task', task_id=activity.task.id), activity.task.name, str(activity.task.point))
        else:
            item['body'] = u'<p> unlocked an Achievement: <a href="{0:s}">{1:s}</a> and get bonused <strong>{2:s} points</strong></p>'.format(url_for('task.all_task'), activity.task.name, str(activity.task.point))

        resp.append(item)

    return jsonify(result=resp)


@app.route('/')
@app.route('/index')
@app.route('/index/vi')
def index():
    return render_template(
        'common/index.html',
    )

@app.route('/index/en')
def index_en():
    return render_template(
        'common/index_en.html',
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


def user_comparator(a, b):
    if not a[1] - b[1]:
        return (b[0].solved_data[-1].created_at - a[0].solved_data[-1].created_at).days

    return int(a[1] - b[1])


def team_comparator(a, b):
    if not a[1] - b[1]:
        c = UserSolved.query.filter_by(team_id=a[0].id).group_by(UserSolved.task_id).order_by(desc(UserSolved.created_at)).first()
        d = UserSolved.query.filter_by(team_id=b[0].id).group_by(UserSolved.task_id).order_by(desc(UserSolved.created_at)).first()

        return (d.created_at - c.created_at).days

    return int(a[1] - b[1])


@app.route('/scoreboard', methods=['GET', 'POST'])
@login_required
def scoreboard():
    users_data = sorted(UserSolved.get_users_score(), cmp=user_comparator, reverse=True)
    max_user_score = 0
    if len(users_data):
        max_user_score = max(users_data, key=lambda data: data[1])[1]
    if not max_user_score:
        max_user_score = 1

    teams_data = sorted(Team.get_team_points(), cmp=team_comparator, reverse=True)
    max_team_score = 1
    if len(teams_data):
        max_team_score = max(teams_data, key=lambda data: data[1])[1]
    if not max_user_score:
        max_user_score = 1

    all_team_data = []
    xs_data = []
    for team, _ in teams_data[:10]:
        periods = UserSolved.query.filter_by(team_id=team.id).group_by(UserSolved.task_id).order_by(asc(UserSolved.created_at)).all()
        sum_point = 0
        period_data = []
        x_data = []
        for period in periods:
            sum_point += period.point
            period_data.append(sum_point)
            x_data.append("'%s'" % str(period.created_at))
        all_team_data.append((team, ", ".join(map(str, period_data))))
        xs_data.append((team, ", ".join(x_data)))

    achievements = [task for task in Task.query.all() if task.category.is_achievement()]

    return render_template('common/scoreboard.html',
                           users_data=users_data, teams_data=teams_data,
                           max_user_score=max_user_score, max_team_score=max_team_score,
                           data=all_team_data, xs_data=xs_data, achievements=achievements, cfgs=AC_CFGS
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
