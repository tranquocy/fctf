#!/usr/bin/env python

import datetime
import hashlib
import string
import random
import os
import io
import json
import requests

from werkzeug.utils import secure_filename
from flask import render_template
from flask_mail import Message
from app import app, mail


def generate_random_string(n=7):
    return ''.join([c for i in range(n) for c in random.choice(string.letters)])


def generate_token():
    random_string = generate_random_string()
    return hashlib.sha1(random_string + str(datetime.datetime.now())).hexdigest()


def send_email(subject, sender, recipients, template_name, args):
    msg = Message(subject, sender=sender, recipients=recipients)
    txt_template = os.path.join(app.config['MAIL_TEMPLATE_FOLDER'], '%s.txt' % template_name)
    html_template = os.path.join(app.config['MAIL_TEMPLATE_FOLDER'], '%s.html' % template_name)
    msg.body = render_template(txt_template, **args)
    msg.html = render_template(html_template, **args)
    mail.send(msg)
