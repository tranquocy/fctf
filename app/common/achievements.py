import datetime

from app import app, db
from app.task.models import Task, Category
from app.user.forms import SubmitFlagForm
from app.user.models import UserSolved, SubmitLogs
from app.common.utils import admin_required, check_recaptcha_response
from sqlalchemy.sql.expression import *


ACHIEVEMENTS = {
    "FIRST_BLOOD": 69,
    "FIRST_GAME": 70,
    "FIRST_CODE": 71,
    "FIRST_CTF": 72,
    "MOVIE_ADDICT": 73,
    "HARD_CODE_3": 74,
    "HARD_CODE_5": 75,
    "BEST_BEST": 76,
    "TIME_AM": 77,
    "TIME_NOON": 78,
    "TIME_PM": 79,
}

ACHIEVEMENT_CFGS = {
    69: {
        "icon": "fa-bolt",
        "color": "#1abc9c"
    },
    70: {
        "icon": "fa-gamepad",
        "color": "#e67e22"
    },
    71: {
        "icon": "fa-file-code-o",
        "color": "#9b59b6"
    },
    72: {
        "icon": "fa-flag",
        "color": "#2c3e50"
    },
    73: {
        "icon": "fa-video-camera",
        "color": "#d35400"
    },
    74: {
        "icon": "fa-user",
        "color": "#e74c3c"
    },
    75: {
        "icon": "fa-users",
        "color": "#8e44ad"
    },
    76: {
        "icon": "fa-rocket",
        "color": "#16a085"
    },
    77: {
        "icon": "fa-child",
        "color": "#f1c40f"
    },
    78: {
        "icon": "fa-sun-o",
        "color": "#c0392b"
    },
    79: {
        "icon": "fa-moon-o",
        "color": "#27ae60"
    }
}

def is_first_solved_data(solved_data):
    return solved_data.id == 1

def is_continuous_log(log_data, count=2):
    if log_data.id <= count:
        return False
    start_id = log_data.id - count + 1
    logs = SubmitLogs.query.join(SubmitLogs.task).filter(SubmitLogs.id.in_(range(start_id, log_data.id + 1))).all()
    if len(logs) == count:
        for log in logs:
            if log.task.category_id != log_data.task.category_id or log.team_id != log_data.team_id or log.task_id != log_data.task_id:
                return False
        return True
    else:
        return False

def is_solved_in_time(solved_data, start_time, end_time):
    return start_time <= solved_data.created_at and solved_data.created_at <= end_time


def is_place_solved_by_category(solved_data, place=1):
    tasks = solved_data.task.category.tasks
    pres = UserSolved.query.filter(UserSolved.task_id.in_([task.id for task in tasks])).filter(UserSolved.id < solved_data.id).all()

    return len(pres) == place - 1

def try_unlock_achievements(log_data, solved_data):
    if is_first_solved_data(solved_data):
       do_unlock_achievements("FIRST_BLOOD", log_data, solved_data)

    if is_place_solved_by_category(solved_data):
        if solved_data.task.category.description == 'cc':
            do_unlock_achievements("FIRST_CODE", log_data, solved_data)
        if solved_data.task.category.description == 'game':
            do_unlock_achievements("FIRST_GAME", log_data, solved_data)
        if solved_data.task.category.description == 'ctf':
            do_unlock_achievements("FIRST_CTF", log_data, solved_data)

    if is_continuous_log(log_data, 3):
        do_unlock_achievements("HARD_CODE_3", log_data, solved_data)

    if is_continuous_log(log_data, 5):
        do_unlock_achievements("HARD_CODE_5", log_data, solved_data)

    if solved_data.task_id == 16:
        do_unlock_achievements("MOVIE_ADDICT", log_data, solved_data)

    if solved_data.task_id == 14:
        do_unlock_achievements("BEST_BEST", log_data, solved_data)

    start = datetime.datetime.now().replace(hour=4, minute=0, second=0)
    end = datetime.datetime.now().replace(hour=5, minute=0, second=0)
    print solved_data.created_at, start, end
    if is_solved_in_time(solved_data, start, end):
        do_unlock_achievements("TIME_AM", log_data, solved_data)

    start = datetime.datetime.now().replace(hour=12, minute=30, second=0)
    end = datetime.datetime.now().replace(hour=13, minute=30, second=0)
    if is_solved_in_time(solved_data, start, end):
        do_unlock_achievements("TIME_NOON", log_data, solved_data)

    start = datetime.datetime.now().replace(hour=19, minute=00, second=0)
    end = datetime.datetime.now().replace(hour=20, minute=00, second=0)
    if is_solved_in_time(solved_data, start, end):
        do_unlock_achievements("TIME_PM", log_data, solved_data)


def do_unlock_achievements(achievement_str, log_data, solved_data):
    achievement_id = ACHIEVEMENTS[achievement_str]
    achievement = Task.query.get_or_404(achievement_id)
    done = UserSolved.query.filter_by(task_id=achievement_id).first()

    if not done:
        solved_data = UserSolved(solved_data.user, achievement)
        log_data = SubmitLogs(log_data.user, achievement, "Unlocked by system")
        db.session.add(solved_data)
        db.session.add(log_data)
        db.session.commit()
        return True
    else:
        return False
