#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stdout)
sys.path.insert(0,"/var/www/mian/")
#sys.path.insert(0,"/home/tbj128/.local/lib/python2.7/site-packages")
sys.path.insert(0,"/var/www/mian/venv/lib/python2.7/site-packages")

from mian import app as application
#from test import app as application

#from test import app as application
application.secret_key = 'Twilight Sparkle'
