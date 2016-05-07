from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from sqlite3 import dbapi2 as sqlite3
import os 
import random
import string
import json
import hashlib

import analysis

RELATIVE_PATH = os.path.dirname(os.path.realpath(__file__))


# Initialize the web app
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))


app.config.from_envvar('FLASKR_SETTINGS', silent=True)
app = bottle.Bottle()
# dbhost is optional, default is localhost
plugin = bottle_mysql.Plugin(dbuser='user', dbpass='pass', dbname='some_db')
app.install(plugin)

def didUserUploadRequiredFiles(user):
	otuTable = 0
	taxaMap = 0
	metadata = 0
	for f in os.listdir(RELATIVE_PATH + '/data/' + user):
		if f == "otuTable.csv":
			otuTable = 1
		if f == "otuTaxonomyMapping.csv":
			taxaMap = 1
		if f == "otuMetadata.csv":
			metadata = 1
	return otuTable, taxaMap, metadata


# 
# -------------------------------------------
# 

@route('/')
def hello():
	user = request.get_cookie("user")
	if user:
		otuTable, taxaMap, metadata = didUserUploadRequiredFiles(user)
		return template('index', otuTable=otuTable, taxaMap=taxaMap, metadata=metadata)
	else:
		# Generate a user token
		user = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))

		# Sets up the user folder
		if not os.path.exists(RELATIVE_PATH + '/data/' + user):
			os.makedirs(RELATIVE_PATH + '/data/' + user)

		response.set_cookie("user", user)
		return template('index', name=user)

@route('/abundances')
def abundances():
	user = request.get_cookie("user")
	if user:
		otuTable, taxaMap, metadata = didUserUploadRequiredFiles(user)
		if otuTable == 1 and taxaMap == 1 and metadata == 1:
			return template('abundances', otuTable=otuTable, taxaMap=taxaMap, metadata=metadata)
	

@route('/static/<filepath:path>')
def server_static(filepath):
	print filepath, RELATIVE_PATH + '/static'
	return static_file(filepath, root=RELATIVE_PATH + '/static')


# 
# GET/POST API Requests
# 

# ----- Auth endpoints -----
@route('/auth')
def show(db):
	username = "abc@example.com"
	db.execute('SELECT * from accounts where user_email="%s"', (username,))
	row = db.fetchone()
	if row:
		print row
    	# return template('showitem', page=row)
	return HTTPError(404, "Page not found")


# ----- Data processing endpoints -----

@route('/upload', method='POST')
def doUpload():
	user = request.get_cookie("user")
	category = request.forms.get('category')
	upload = request.files.get('upload')
	name, ext = os.path.splitext(upload.filename)
	if ext not in ('.csv'):
		return 'File extension not allowed.'

	# TODO: Need more security
	# TODO: Check file validity
	saveDir = RELATIVE_PATH + '/data/' + user
	filename = category + ".csv"
	filepath = os.path.join(saveDir, filename)
	upload.save(filepath, True)

	return 'OK'



# ----- Visualization endpoints -----

@route('/taxonomies', method='GET')
def getTaxonomies():
	user = request.get_cookie("user")
	abundances = analysis.getTaxonomyMapping(user)
	return json.dumps(abundances)

@route('/metadata_headers', method='GET')
def getMetadataHeaders():
	user = request.get_cookie("user")
	abundances = analysis.getMetadataHeaders(user)
	return json.dumps(abundances)

@route('/abundances', method='POST')
def getAbundances():
	user = request.get_cookie("user")
	# user = request.forms.get('user')
	level = request.forms.get('level')
	taxonomy = request.forms.get('taxonomy')
	catvar = request.forms.get('catvar')

	abundances = analysis.getAbundanceForOTUs(user, level, taxonomy, catvar)
	return json.dumps(abundances)


run(host='localhost', port=8080, debug=True)

