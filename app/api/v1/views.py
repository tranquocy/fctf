import json

from flask import Blueprint, render_template, request, g, send_from_directory, abort, jsonify
from flask_login import current_user, login_required
from sqlalchemy import desc

from app import app, db, lm
from app.common.utils import compute_sign_hash, set_all_cookie, delete_all_cookie, admin_required
from app.user.models import User, UserSolved, SubmitLogs, UserData
from app.team.models import Team
from app.task.models import Task, Category

api_v1_module = Blueprint('api_v1', __name__)


@api_v1_module.route('/get_result', methods=['GET'])
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


@api_v1_module.route('/post_result', methods=['GET'])
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


@api_v1_module.route('/game/get_token', methods=['POST'])
def get_token():
    resp = {'success': 0}
    print request.form.get('email', '')
    user = User.query.filter_by(email=request.form.get('email', '')).first()
    print user
    if user and user.check_password(request.form.get('password', '')):
        if user.storage:
            if user.storage.is_expired():
                user.storage.refresh()
                db.session.add(user.storage)
                db.session.commit()
        else:
            storage = UserData(user)
            db.session.add(storage)
            db.session.commit()
        resp['token'] = user.storage.token
        resp['success'] = 1

    return jsonify(resp)


@api_v1_module.route('/game/get_data', methods=['GET'])
def get_data():
    resp = {'success': 0}
    print request.args.get('token', '')
    storage = UserData.query.filter_by(token=request.args.get('token', '')).first()
    if storage:
        if not storage.is_expired():
            resp['data'] = storage.data
            resp['success'] = 1
        else:
            resp['success'] = 0
            resp['error'] = 'Please refresh token'

    return jsonify(resp)


@api_v1_module.route('/game/set_data', methods=['POST'])
def set_data():
    resp = {'success': 0}
    try:
        print request.form.get('token', '')
        storage = UserData.query.filter_by(token=request.form.get('token', '')).first()
        if storage:
            if not storage.is_expired():
                tmp = json.loads(request.form.get('data', ''))
                storage.data = request.form.get('data', '')
                db.session.add(storage)
                db.session.commit()
                resp['success'] = 1
                resp['result'] = 'ok'
            else:
                resp['success'] = 0
                resp['error'] = 'Please refresh token'
    except Exception, e:
        print e
        pass

    return jsonify(resp)


@api_v1_module.route('/game/post_result', methods=['POST'])
def game_post_result():
    resp = {'success': 0}
    try:
        print request.form.get('token', '')
        storage = UserData.query.filter_by(token=request.form.get('token', '')).first()
        task = Task.query.get(request.form.get('task_id', 0))
        if storage and task and task.category.description == 'game':
            if not storage.is_expired():
                if (storage.user.team and task not in storage.user.team.solved_tasks()) or task not in storage.user.solved_tasks:
                    log_data = SubmitLogs(storage.user, task, '########[API-CENSORED]########')
                    db.session.add(log_data)
                    solved_data = UserSolved(storage.user, task)
                    db.session.add(solved_data)
                    db.session.commit()
                    resp['success'] = 1
                    resp['result'] = 'ok'
            else:
                resp['success'] = 0
                resp['error'] = 'Please refresh token'
    except Exception, e:
        print e
        pass

    return jsonify(resp)