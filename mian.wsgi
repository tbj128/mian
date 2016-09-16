#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stdout)
sys.path.insert(0,"/var/www/mian/")
#sys.path.insert(0,"/home/tbj128/.local/lib/python2.7/site-packages")
sys.path.insert(0,"/var/www/mian/venv/lib/python2.7/site-packages")

import os
print os.getegid()

#import flask
print sys.path
#import flask as f
#f

# Setup R libraries if they do not already exist
import r_package_install
r_package_install.importr_custom("vegan")
r_package_install.importr_custom("RColorBrewer")
r_package_install.importr_custom("ranger")
r_package_install.importr_custom("Boruta")
r_package_install.importr_custom("glmnet")


from mian import app as application
#from test import app as application

#from test import app as application
application.secret_key = 'Twilight Sparkle'
