import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'mysql://ctf_admin:ctf_admin@localhost/ctf'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

CSRF_ENABLED = True
SECRET_KEY = '&%^%&12o)!JHGHVJBK671i2lkj;^*&:'

AES_KEY = 'alskd8q@%pohasdasdaIUA131asdlkas'

MAX_MEMBER = 5
LOCK_TEAM = False
LOCK_PROFILE = False
GAME_STARTED = False

UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'files')
