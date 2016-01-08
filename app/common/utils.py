import datetime
import hashlib
import string
import random
import os
import smtplib
import requests
from functools import wraps

from flask import render_template, redirect, url_for, g
from flask_mail import Message

from app import app, mail


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user or not g.user.is_admin():
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function


def generate_random_string(n=7):
    return ''.join([c for i in range(n) for c in random.choice(string.letters)])


def generate_token():
    random_string = generate_random_string()
    return hashlib.sha1(random_string + str(datetime.datetime.now())).hexdigest()


def send_email(subject, sender, recipients, template_name, args):
    try:
        msg = Message(subject, sender=sender, recipients=recipients)
        txt_template = os.path.join(app.config['MAIL_TEMPLATE_FOLDER'], '%s.txt' % template_name)
        html_template = os.path.join(app.config['MAIL_TEMPLATE_FOLDER'], '%s.html' % template_name)
        msg.body = render_template(txt_template, **args)
        msg.html = render_template(html_template, **args)
        mail.send(msg)

        return (True, 'OK')
    except smtplib.SMTPRecipientsRefused:
        return (False, 'Email address does not exist')
    except Exception, e:
        return (False, 'Unknown error. Please try again later')


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


def compute_sign_hash(values):
    values.append(app.config['AES_KEY'])
    raw = '_'.join(values)
    return hashlib.md5(raw).hexdigest()


def compute_color_value(value):
    return "#" + hashlib.md5(value).hexdigest()[:6]


def ordinal(n):
    return "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])


def check_recaptcha_response(response, remote_ip):
    payload = {
        'secret': app.config['RECAPTCHA_PRIVATE_KEY'],
        'response': response,
        'remoteip': remote_ip
    }
    verify_request = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data=payload
    )
    if verify_request.status_code == 200 and verify_request.json()['success']:
        return (True, 'OK')

    return (False, 'Verify reCAPTCHA response failed')