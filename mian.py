from functools import wraps
from flask import Flask, request, session, Response, render_template, redirect, url_for
import flask.ext.login as flask_login
from flask.ext.login import current_user
from werkzeug import secure_filename
from sqlite3 import dbapi2 as sqlite3
import os 
import random
import string
import json
import hashlib

import analysis

DB_NAME = "mian.db"
RELATIVE_PATH = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = os.path.join(RELATIVE_PATH, "data")

# Initialize the web app
app = Flask(__name__)

# Initialize the login manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

def createSalt():
	ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
	chars=[]
	for i in range(16):
		chars.append(random.choice(ALPHABET))
	return "".join(chars)

def addUser(username, password):
	db = sqlite3.connect(DB_NAME)
	c = db.cursor()
	t = (username,)

	salt = createSalt()
	calculatedPassword = hashlib.md5( salt + password ).hexdigest()
	c.execute('INSERT INTO accounts (user_email, password_hash, salt) VALUES (?,?,?)', (username, calculatedPassword, salt))
	db.commit()
	db.close()

def getUserEmail(userID):
	db = sqlite3.connect(DB_NAME)
	c = db.cursor()
	t = (userID,)
	c.execute('SELECT id, user_email FROM accounts WHERE id=?', t)
	row = c.fetchone()
	if row is None:
		return ""
	db.close()
	return row[1]


def checkAuth(username, password):
	db = sqlite3.connect(DB_NAME)
	c = db.cursor()
	t = (username,)
	c.execute('SELECT password_hash, salt, id FROM accounts WHERE user_email=?', t)
	row = c.fetchone()
	db.close()

	if row is None:
		# No user exists
		return False, -1
	else:
		knownPassword = row[0]
		salt = row[1]
		id = row[2]
		calculatedPassword = hashlib.md5( salt + password ).hexdigest()
		okay = calculatedPassword == knownPassword
		if okay:
			return okay, id
		else:
			return okay, -1

class User(flask_login.UserMixin):
    def __init__(self, name, id, active=True):
        self.name = name
        self.id = id
        self.active = active

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

@login_manager.user_loader
def user_loader(id):
	print id
	userEmail = getUserEmail(id)
	if userEmail == "":
		return
	user = User(userEmail, id, True)
	return user


# 
# -------------------------------------------
# 

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
	if request.method == 'GET':
		return render_template('signup.html')
	else:
		email = request.form['inputName']
		password = request.form['inputPassword']
		addUser(email, password)

		# Checks that the user does not already exist
		isAuth, userID = checkAuth(email, password)
		if isAuth:
			return 'User already exists'

		# Sets up the user folder
		dataPath = os.path.join(RELATIVE_PATH, 'data')
		dataPath = os.path.join(dataPath, userID)
		if not os.path.exists(dataPath):
			os.makedirs(dataPath)

		# Auto logs in the user
		isAuth, userID = checkAuth(email, password)
		if isAuth:
			user = User(email, userID, True)
			flask_login.login_user(user)
			return redirect(url_for('projects', signup=1))

		return 'Internal Signup Error. :( Please try again later.'

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		return render_template('login.html')
	else:
		email = request.form['email']
		password = request.form['password']

		isAuth, userID = checkAuth(email, password)
		if isAuth:
			user = User(email, userID, True)
			flask_login.login_user(user)
			return redirect(url_for('projects'))

		return 'Bad login'

@app.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect(url_for('login'))

@app.route('/projects')
@flask_login.login_required
def projects():
	newSignup = False
	if request.args.get('signup', '') == '1':
		newSignup = True

	items = {}
	projectNames = []

	userDir = os.path.join(UPLOAD_FOLDER, current_user.id)
	for subdir, dirs, files in os.walk(userDir):
	    for dir in dirs:
	    	if dir != "temp":
	    		projectName = dir
		    	item = {}
		    	dirPath = os.path.join(subdir, dir)
		    	mapPath = os.path.join(dirPath, 'map.txt')
		    	print mapPath
		    	with open(mapPath) as outfile:
					item = json.load(outfile)
		    	items[dir] = item
		    	projectNames.append(projectName)

	return render_template('projects.html', newSignup=newSignup, projectNames=projectNames, items=items)

@app.route('/create', methods=['GET', 'POST'])
@flask_login.login_required
def create():
	if request.method == 'GET':
		return render_template('create.html')
	else:
		projectName = request.form['projectName']
		projectOTUTableName = request.form['projectOTUTableName']
		projectTaxaMapName = request.form['projectTaxaMapName']
		projectSampleIDName = request.form['projectSampleIDName']

		dataMap = {}
		dataMap["otuTable"] = projectOTUTableName
		dataMap["otuTaxonomyMapping"] = projectTaxaMapName
		dataMap["otuMetadata"] = projectSampleIDName
		
		userUploadFolder = os.path.join(UPLOAD_FOLDER, current_user.id)
		tempFolder = os.path.join(userUploadFolder, 'temp')
		mapFile = os.path.join(tempFolder, 'map.txt')
		destFolder = os.path.join(userUploadFolder, projectName)

		with open(mapFile, 'w') as outfile:
			json.dump(dataMap, outfile)

		os.rename(os.path.join(tempFolder, projectOTUTableName), os.path.join(tempFolder, 'otuTable.csv'))
		os.rename(os.path.join(tempFolder, projectTaxaMapName), os.path.join(tempFolder, 'otuTaxonomyMapping.csv'))
		os.rename(os.path.join(tempFolder, projectSampleIDName), os.path.join(tempFolder, 'otuMetadata.csv'))

		# TODO: Clean project name
		os.rename(tempFolder, destFolder)

		return redirect(url_for('projects'))

@app.route('/')
def home():
	if current_user.is_authenticated:
		return redirect(url_for('projects'))
	else:
		return render_template('index.html')

# ----- Analysis Pages -----

@app.route('/abundance_boxplots')
@flask_login.login_required
def abundance_boxplots():
	projectNames = getAllProjects(current_user.id)
	return render_template('abundance_boxplots.html', projectNames=projectNames)


# ----- Visualization endpoints -----

@app.route('/taxonomies')
@flask_login.login_required
def getTaxonomies():
	user = current_user.id
	pid = request.args.get('pid', '')
	if pid == '':
		return json.dumps({})

	abundances = analysis.getTaxonomyMapping(user, pid)
	return json.dumps(abundances)


@app.route('/metadata_headers')
@flask_login.login_required
def getMetadataHeaders():
	user = current_user.id
	pid = request.args.get('pid', '')
	if pid == '':
		return json.dumps({})

	abundances = analysis.getMetadataHeaders(user, pid)
	return json.dumps(abundances)

@app.route('/abundances', methods=['POST'])
@flask_login.login_required
def getAbundances():
	user = current_user.id

	pid = request.form['pid']
	level = request.form['level']
	taxonomy = request.form['taxonomy']
	catvar = request.form['catvar']

	abundances = analysis.getAbundanceForOTUs(user, pid, level, taxonomy, catvar)
	return json.dumps(abundances)


# ----- Data processing endpoints -----
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ["csv"]

@app.route('/upload', methods=['POST'])
@flask_login.login_required
def upload():
	if request.method == 'POST':
		file = request.files['upload']
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)

			userUploadFolder = os.path.join(UPLOAD_FOLDER, current_user.id)
			uploadFolder = os.path.join(userUploadFolder, 'temp')

			if not os.path.exists(uploadFolder):
				os.makedirs(uploadFolder)

			file.save(os.path.join(uploadFolder, filename))
			return "Saved"

		return "Error"

# ------------------
# Helpers
# ------------------

def getAllProjects(userID):
	projectNames = []
	userDir = os.path.join(UPLOAD_FOLDER, userID)
	for subdir, dirs, files in os.walk(userDir):
		for dir in dirs:
			if dir != "temp":
				projectName = dir
				projectNames.append(projectName)
	return projectNames

# @app.route('/abundances')
# def abundances():
# 	user = request.get_cookie("user")
# 	if user:
# 		otuTable, taxaMap, metadata = didUserUploadRequiredFiles(user)
# 		if otuTable == 1 and taxaMap == 1 and metadata == 1:
# 			return template('abundances', otuTable=otuTable, taxaMap=taxaMap, metadata=metadata)
	

# # @route('/static/<filepath:path>')
# # def server_static(filepath):
# # 	print filepath, RELATIVE_PATH + '/static'
# # 	return static_file(filepath, root=RELATIVE_PATH + '/static')

# @app.route('/static/<path:path>')
# def send_static(path):
#     return send_from_directory('static', path)


# # 
# # GET/POST API Requests
# # 

# # ----- Auth endpoints -----
# @app.route('/auth')
# def show(db):
# 	username = "abc@example.com"
# 	db.execute('SELECT * from accounts where user_email="%s"', (username,))
# 	row = db.fetchone()
# 	if row:
# 		print row
#     	# return template('showitem', page=row)
# 	return HTTPError(404, "Page not found")


# # ----- Data processing endpoints -----

# @app.route('/upload', methods=['POST'])
# @requires_auth
# def doUpload():
# 	user = request.get_cookie("user")
# 	category = request.forms.get('category')
# 	upload = request.files.get('upload')
# 	name, ext = os.path.splitext(upload.filename)
# 	if ext not in ('.csv'):
# 		return 'File extension not allowed.'

# 	# TODO: Need more security
# 	# TODO: Check file validity
# 	saveDir = RELATIVE_PATH + '/data/' + user
# 	filename = category + ".csv"
# 	filepath = os.path.join(saveDir, filename)
# 	upload.save(filepath, True)

# 	return 'OK'




if __name__ == '__main__':
	app.secret_key = 'Twilight Sparkle'
	app.config['SESSION_TYPE'] = 'filesystem'
	app.run(debug=True, port=8080)