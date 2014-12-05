#!venv/bin/python
from app import db
from app.models import Team, Task, UserSolved, SubmitLogs
import requests
import datetime

CC_TASK = {
    9: 49,
    10: 58,
}

teams = Team.query.filter(Team.id.in_([1, 2])).all()
print '>>>>>>> START CHECKING: %s <<<<<<<' % datetime.datetime.now()
for ctf_task_id, cc_task_id in CC_TASK.items():
    try:
        ctf_task = Task.query.get(ctf_task_id)
        print '[?] - Check task: ', ctf_task
        for team in teams:
            print '[?] -- Check team', team.name
            if ctf_task not in team.solved_tasks():
                for user in team.members:
                    payload = {'email': user.email, 'format': 'json'}
                    url = 'http://118.70.170.72:8082/api/v1/problems/%d' % cc_task_id
                    r = requests.get(url, params=payload)
                    resp = r.json()
                    if resp['success'] and resp.get('point', None):
                        print '[+] ---- Update point %d by user %s' % (ctf_task.point, user.email)
                        log_data = SubmitLogs(user, ctf_task, 'updated by cron')
                        db.session.add(log_data)
                        solved_data = UserSolved(user, ctf_task)
                        db.session.add(solved_data)
                        db.session.commit()
            else:
                print '[?] --- Done task already !'
    except Exception as e:
        print '[-] Error:', e
print '>>>>>>> END CHECKING: %s <<<<<<<' % datetime.datetime.now()
