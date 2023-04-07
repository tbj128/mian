import sys

sys.path.insert(0, '/opt/mian')

print("App Startup")

from mian.main import app as application

application.secret_key = 'Twilight Sparkle'
application.config['SESSION_TYPE'] = 'filesystem'
