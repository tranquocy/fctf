#!venv/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)

from app import app

if not app.debug:
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler(
        app.config['MAIL_SERVER'],
        'server-error@ctf.framgia.vn',
        app.config['ADMINS'],
        'Your CTF Application Failed'
    )
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

from app import app as application

if __name__ == '__main__':
    import logging
    logging.basicConfig(filename='error.log',level=logging.DEBUG)
    app.run(host='0.0.0.0', debug = True)
