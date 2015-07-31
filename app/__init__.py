import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.admin import Admin
from flask_mail import Mail
import base64

# the block size for the cipher object; must be 16, 24, or 32 for AES
BLOCK_SIZE = 32

# the character used for padding--with a block cipher such as AES, the value
# you encrypt must be a multiple of BLOCK_SIZE in length.  This character is
# used to ensure that your value is always a multiple of BLOCK_SIZE
PADDING = '{'

# one-liner to sufficiently pad the text to be encrypted
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING

# one-liners to encrypt/encode and decrypt/decode a string
# encrypt with AES, encode with base64
EncodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))
DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

mail = Mail(app)

from app import views, models

admin = Admin(app, url='/db')
admin.add_view(views.UserView(db.session, name='Users'))
admin.add_view(views.TeamView(db.session, name='Teams'))
admin.add_view(views.SubmitLogView(db.session, name='Submit Logs'))
admin.add_view(views.TaskForTeamView(db.session, name='Task For Teams'))
admin.add_view(views.CategoryView(db.session, name='Category'))
admin.add_view(views.UserSolvedView(db.session, name='User Solved'))