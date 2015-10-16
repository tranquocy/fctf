from flask import Blueprint, render_template, request, g, send_from_directory, abort, jsonify
from flask_login import current_user, login_required
from sqlalchemy import desc

from app import app, db, lm
from app.common.utils import compute_sign_hash, set_all_cookie, delete_all_cookie, admin_required
from app.user.models import User, UserSolved, SubmitLogs
from app.team.models import Team
from app.task.models import Task, Category

api_v1_module = Blueprint('api_v1', __name__)


@app.route('/get_result', methods=['GET'])
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


@app.route('/post_result', methods=['GET'])
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
