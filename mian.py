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
import shutil

import analysis
import analysis_diversity
import analysis_r_visualizations
import analysis_stats

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

@app.route('/alpha_diversity')
@flask_login.login_required
def alpha_diversity():
	projectNames = getAllProjects(current_user.id)
	return render_template('alpha_diversity.html', projectNames=projectNames)

@app.route('/beta_diversity')
@flask_login.login_required
def beta_diversity():
	projectNames = getAllProjects(current_user.id)
	return render_template('beta_diversity.html', projectNames=projectNames)

@app.route('/cluster_gravity')
@flask_login.login_required
def cluster_gravity():
	projectNames = getAllProjects(current_user.id)
	return render_template('cluster_gravity.html', projectNames=projectNames)

@app.route('/pca')
@flask_login.login_required
def pca():
	projectNames = getAllProjects(current_user.id)
	return render_template('pca.html', projectNames=projectNames)

@app.route('/nmds')
@flask_login.login_required
def nmds():
	projectNames = getAllProjects(current_user.id)
	return render_template('nmds.html', projectNames=projectNames)

@app.route('/correlations')
@flask_login.login_required
def correlations():
	# TODO: Consider using only factors in the future for catVars
	projectNames = getAllProjects(current_user.id)
	catVars, otuMetadata = analysis.getMetadataHeadersWithMetadata(current_user.id, projectNames[0])
	numericCatVars = analysis.getNumericMetadata(otuMetadata)
	return render_template('correlations.html', projectNames=projectNames, catVars=catVars, numericCatVars=numericCatVars)

@app.route('/fisher_exact')
@flask_login.login_required
def fisher_exact():
	projectNames = getAllProjects(current_user.id)
	# TODO: Use default project name
	catVars = analysis.getMetadataHeaders(current_user.id, projectNames[0])
	uniqueCatVals = analysis.getMetadataUniqueVals(current_user.id, projectNames[0], catVars[0])
	numericCatVars

	return render_template('fisher_exact.html', projectNames=projectNames, catVars=catVars, uniqueCatVals=uniqueCatVals)

@app.route('/enriched_selection')
@flask_login.login_required
def enriched_selection():
	projectNames = getAllProjects(current_user.id)
	# TODO: Use default project name
	catVars = analysis.getMetadataHeaders(current_user.id, projectNames[0])
	uniqueCatVals = analysis.getMetadataUniqueVals(current_user.id, projectNames[0], catVars[0])
	return render_template('enriched_selection.html', projectNames=projectNames, catVars=catVars, uniqueCatVals=uniqueCatVals)

@app.route('/tree')
@flask_login.login_required
def tree():
	projectNames = getAllProjects(current_user.id)
	return render_template('tree_view.html', projectNames=projectNames)

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

@app.route('/abundances_grouping', methods=['POST'])
@flask_login.login_required
def getAbundancesGrouping():
	user = current_user.id

	pid = request.form['pid']
	level = request.form['level']
	taxonomy = request.form['taxonomy']
	catvar = request.form['catvar']

	taxonomyGroupingGeneral = request.form['taxonomy_group_general']
	taxonomyGroupingSpecific = request.form['taxonomy_group_specific']

	abundances = analysis.getAbundanceForOTUsByGrouping(user, pid, level, taxonomy, catvar, taxonomyGroupingGeneral, taxonomyGroupingSpecific)
	return json.dumps(abundances)

@app.route('/tree', methods=['POST'])
@flask_login.login_required
def getTree():
	user = current_user.id

	pid = request.form['pid']
	level = request.form['level']
	taxonomy = request.form['taxonomy']
	catvar = request.form['catvar']
	taxonomy_display_level = request.form['taxonomy_display_level']
	display_values = request.form['display_values']
	exclude_unclassified = request.form['exclude_unclassified']

	abundances = analysis.getTreeGrouping(user, pid, level, taxonomy, catvar, taxonomy_display_level, display_values, exclude_unclassified)
	return json.dumps(abundances)

@app.route('/alpha_diversity', methods=['POST'])
@flask_login.login_required
def getAlphaDiversity():
	user = current_user.id

	pid = request.form['pid']
	level = request.form['level']
	taxonomy = request.form['taxonomy']
	catvar = request.form['catvar']
	alphaType = request.form['alphaType']
	alphaContext = request.form['alphaContext']

	abundances = analysis_diversity.alphaDiversity(user, pid, level, taxonomy, catvar, alphaType, alphaContext)
	return json.dumps(abundances)

@app.route('/beta_diversity', methods=['POST'])
@flask_login.login_required
def getBetaDiversity():
	user = current_user.id

	pid = request.form['pid']
	level = request.form['level']
	taxonomy = request.form['taxonomy']
	catvar = request.form['catvar']
	betaType = request.form['betaType']

	abundances = analysis_diversity.betaDiversity(user, pid, level, taxonomy, catvar, betaType)
	return json.dumps(abundances)

@app.route('/pca', methods=['POST'])
@flask_login.login_required
def getPCA():
	user = current_user.id

	pid = request.form['pid']
	level = request.form['level']
	taxonomy = request.form['taxonomy']
	catvar = request.form['catvar']
	pca1 = request.form['pca1']
	pca2 = request.form['pca2']

	abundances = analysis_r_visualizations.pca(user, pid, level, taxonomy, catvar, pca1, pca2)
	return json.dumps(abundances)

@app.route('/nmds', methods=['POST'])
@flask_login.login_required
def getNMDS():
	user = current_user.id

	pid = request.form['pid']
	level = request.form['level']
	taxonomy = request.form['taxonomy']
	catvar = request.form['catvar']

	abundances = analysis_r_visualizations.nmds(user, pid, level, taxonomy, catvar)
	return json.dumps(abundances)

@app.route('/correlations', methods=['POST'])
@flask_login.login_required
def getCorrelations():
	user = current_user.id

	pid = request.form['pid']
	level = request.form['level']
	taxonomy = request.form['taxonomy']
	corrvar1 = request.form['corrvar1']
	corrvar2 = request.form['corrvar2']
	colorvar = request.form['colorvar']
	sizevar = request.form['sizevar']
	samplestoshow = request.form['samplestoshow']

	abundances = analysis_r_visualizations.correlations(user, pid, level, taxonomy, corrvar1, corrvar2, colorvar, sizevar, samplestoshow)
	return json.dumps(abundances)

@app.route('/fisher_exact', methods=['POST'])
@flask_login.login_required
def getFisherExact():
	user = current_user.id

	pid = request.form['pid']
	level = request.form['level']
	taxonomy = request.form['taxonomy']
	catvar = request.form['catvar']
	minthreshold = request.form['minthreshold']
	keepthreshold = request.form['keepthreshold']
	pwVar1 = request.form['pwVar1']
	pwVar2 = request.form['pwVar2']

	abundances = analysis_stats.fisherExact(user, pid, level, taxonomy, catvar, minthreshold, keepthreshold, pwVar1, pwVar2)
	return json.dumps(abundances)

@app.route('/enriched_selection', methods=['POST'])
@flask_login.login_required
def getEnrichedSelection():
	user = current_user.id

	pid = request.form['pid']
	level = request.form['level']
	taxonomy = request.form['taxonomy']
	catvar = request.form['catvar']
	enrichedthreshold = request.form['enrichedthreshold']
	pwVar1 = request.form['pwVar1']
	pwVar2 = request.form['pwVar2']

	abundances = analysis_stats.enrichedSelection(user, pid, level, taxonomy, catvar, pwVar1, pwVar2, enrichedthreshold)
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

@app.route('/deleteProject', methods=['POST'])
@flask_login.login_required
def deleteProject():
	if request.method == 'POST':
		project = request.form['project']
		deleteConfirm = request.form['delete']
		if deleteConfirm == "delete" and project != "":
			userUploadFolder = os.path.join(UPLOAD_FOLDER, current_user.id)
			userProjectFolder = os.path.join(userUploadFolder, project)
			if os.path.exists(userProjectFolder):
				shutil.rmtree(userProjectFolder)
				return "OK"
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

if __name__ == '__main__':
	app.secret_key = 'Twilight Sparkle'
	app.config['SESSION_TYPE'] = 'filesystem'
	app.run(debug=True, port=8080)