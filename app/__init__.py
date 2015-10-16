from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_admin import Admin
from flask_mail import Mail


app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

mail = Mail(app)

from app.common import views
from app.api.v1.views import api_v1_module
from app.user.views import user_module, UserView, UserSolvedView, SubmitLogView
from app.team.views import team_module, TeamView
from app.hint.views import hint_module
from app.task.views import task_module, TaskForTeamView, CategoryView

app.register_blueprint(api_v1_module, url_prefix='/api/v1')
app.register_blueprint(user_module, url_prefix='/user')
app.register_blueprint(team_module, url_prefix='/team')
app.register_blueprint(task_module, url_prefix='/task')
app.register_blueprint(hint_module, url_prefix='/hint')

admin = Admin(app, url='/admin')
admin.add_view(UserView(db.session, name='Users'))
admin.add_view(TeamView(db.session, name='Teams'))
admin.add_view(SubmitLogView(db.session, name='Submit Logs'))
admin.add_view(TaskForTeamView(db.session, name='Task For Teams'))
admin.add_view(CategoryView(db.session, name='Category'))
admin.add_view(UserSolvedView(db.session, name='User Solved'))