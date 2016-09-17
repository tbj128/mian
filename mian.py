# ===========================================
# 
# mian Main Routing Component
# @author: tbj128
# 
# ===========================================

# 
# Generic Imports 
# 

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
from subprocess import Popen, PIPE

#
# Imports and installs R packages as needed
#
import utils.r_package_install as r_package_install
r_package_install.importr_custom("vegan")
r_package_install.importr_custom("RColorBrewer")
r_package_install.importr_custom("ranger")
r_package_install.importr_custom("Boruta")
r_package_install.importr_custom("glmnet")


#
# mian imports
#
import db.db as db
import analysis
import analysis_diversity
import analysis_r_visualizations
import analysis_stats


# 
# Global Fields 
# 

DB_NAME = "mian.db"
SCHEMA_NAME = "schema.sql"

RELATIVE_PATH = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = os.path.join(RELATIVE_PATH, "data")
DB_PATH = os.path.join(RELATIVE_PATH, DB_NAME) 
SCHEMA_PATH = os.path.join(RELATIVE_PATH, SCHEMA_NAME) 


#
# Main App
#


# Initialize the web app
app = Flask(__name__)

# Initialize the login manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

# Initialize the database if applicable
db.initDB(DB_PATH, SCHEMA_PATH)

# 
# Auth helper methods 
# 

def createSalt():
	ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
	chars=[]
	for i in range(16):
		chars.append(random.choice(ALPHABET))
	return "".join(chars)

def addUser(username, password):
	db = sqlite3.connect(DB_PATH)
	c = db.cursor()
	t = (username,)

	salt = createSalt()
	calculatedPassword = hashlib.md5( salt + password ).hexdigest()
	c.execute('INSERT INTO accounts (user_email, password_hash, salt) VALUES (?,?,?)', (username, calculatedPassword, salt))
	db.commit()
	db.close()

def getUserEmail(userID):
	db = sqlite3.connect(DB_PATH)
	c = db.cursor()
	t = (userID,)
	c.execute('SELECT id, user_email FROM accounts WHERE id=?', t)
	row = c.fetchone()
	if row is None:
		return ""
	db.close()
	return row[1]

def checkAuth(username, password):
	db = sqlite3.connect(DB_PATH)
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

# 
# Page Routes 
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

		# Checks that the user account was created properly and obtains the user ID
		isAuth, userID = checkAuth(email, password)

		# Sets up the user folder
		dataPath = os.path.join(RELATIVE_PATH, 'data')
		dataPath = os.path.join(dataPath, str(userID))
		if not os.path.exists(dataPath):
			os.makedirs(dataPath)

		# Auto logs in the user
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
		projectSubsampleType = request.form['projectSubsampleType']
		projectSubsampleTo = request.form['projectSubsampleTo']

		projectName = secure_filename(projectName)
		projectOTUTableName = secure_filename(projectOTUTableName)
		projectTaxaMapName = secure_filename(projectTaxaMapName)
		projectSampleIDName = secure_filename(projectSampleIDName)

		dataMap = {}
		dataMap["otuTable"] = projectOTUTableName
		dataMap["otuTaxonomyMapping"] = projectTaxaMapName
		dataMap["otuMetadata"] = projectSampleIDName
		
		userUploadFolder = os.path.join(UPLOAD_FOLDER, current_user.id)
		tempFolder = os.path.join(userUploadFolder, 'temp')
		mapFile = os.path.join(tempFolder, 'map.txt')
		destFolder = os.path.join(userUploadFolder, projectName)


		# Convert from shared file to appropriate file type
		# otuTablePath = os.path.join(tempFolder, projectOTUTableName)

		os.rename(os.path.join(tempFolder, projectOTUTableName), os.path.join(tempFolder, 'otuTable.shared'))
		os.rename(os.path.join(tempFolder, projectTaxaMapName), os.path.join(tempFolder, 'otuTaxonomyMapping.taxonomy'))
		os.rename(os.path.join(tempFolder, projectSampleIDName), os.path.join(tempFolder, 'otuMetadata.tsv'))

		# os.rename(os.path.join(tempFolder, projectOTUTableName), os.path.join(tempFolder, 'otuTable.csv'))
		# os.rename(os.path.join(tempFolder, projectTaxaMapName), os.path.join(tempFolder, 'otuTaxonomyMapping.csv'))
		# os.rename(os.path.join(tempFolder, projectSampleIDName), os.path.join(tempFolder, 'otuMetadata.csv'))

		# TODO: Clean project name
		os.rename(tempFolder, destFolder)

		# Perform OTU subsampling
		subsampleVal = subsampleOTUTable(current_user.id, projectName, projectSubsampleType, projectSubsampleTo)
		dataMap["subsampleVal"] = subsampleVal
		dataMap["subsampleType"] = projectSubsampleType

		with open(mapFile, 'w') as outfile:
			json.dump(dataMap, outfile)

		return redirect(url_for('projects'))

@app.route('/')
def home():
	if current_user.is_authenticated:
		return redirect(url_for('projects'))
	else:
		return render_template('index.html')

# ----- Analysis Pages -----

# 
# Visualization Pages
# 

@app.route('/boxplots')
@flask_login.login_required
def boxplots():
	projectNames = getAllProjects(current_user.id)
	currProject = request.args.get('pid', '')
	return render_template('boxplots.html', projectNames=projectNames, currProject=currProject)

@app.route('/alpha_diversity')
@flask_login.login_required
def alpha_diversity():
	projectNames = getAllProjects(current_user.id)
	currProject = request.args.get('pid', '')
	return render_template('alpha_diversity.html', projectNames=projectNames, currProject=currProject)

@app.route('/beta_diversity')
@flask_login.login_required
def beta_diversity():
	projectNames = getAllProjects(current_user.id)
	currProject = request.args.get('pid', '')
	return render_template('beta_diversity.html', projectNames=projectNames, currProject=currProject)

@app.route('/cluster_gravity')
@flask_login.login_required
def cluster_gravity():
	projectNames = getAllProjects(current_user.id)
	currProject = request.args.get('pid', '')
	return render_template('cluster_gravity.html', projectNames=projectNames, currProject=currProject)

@app.route('/composition')
@flask_login.login_required
def composition():
	projectNames = getAllProjects(current_user.id)
	currProject = request.args.get('pid', '')
	return render_template('composition.html', projectNames=projectNames, currProject=currProject)

@app.route('/correlations')
@flask_login.login_required
def correlations():
	# TODO: Consider using only factors in the future for catVars
	projectNames = getAllProjects(current_user.id)
	currProject = request.args.get('pid', '')
	if currProject == "":
		currProject = projectNames[0]
	catVars, otuMetadata = analysis.getMetadataHeadersWithMetadata(current_user.id, currProject)
	numericCatVars = analysis.getNumericMetadata(otuMetadata)
	return render_template('correlations.html', projectNames=projectNames, currProject=currProject, catVars=catVars, numericCatVars=numericCatVars)

@app.route('/pca')
@flask_login.login_required
def pca():
	projectNames = getAllProjects(current_user.id)
	currProject = request.args.get('pid', '')
	return render_template('pca.html', projectNames=projectNames, currProject=currProject)

@app.route('/nmds')
@flask_login.login_required
def nmds():
	projectNames = getAllProjects(current_user.id)
	currProject = request.args.get('pid', '')
	return render_template('nmds.html', projectNames=projectNames, currProject=currProject)

@app.route('/rarefaction')
@flask_login.login_required
def rarefaction():
	projectNames = getAllProjects(current_user.id)
	currProject = request.args.get('pid', '')
	return render_template('rarefaction.html', projectNames=projectNames, currProject=currProject)

# 
# Stats Pages
# 

@app.route('/boruta')
@flask_login.login_required
def boruta():
	projectNames = getAllProjects(current_user.id)
	currProject = request.args.get('pid', '')
	if currProject == "":
		currProject = projectNames[0]
	catVars = analysis.getMetadataHeaders(current_user.id, currProject)

	return render_template('boruta.html', projectNames=projectNames, currProject=currProject, catVars=catVars)

@app.route('/fisher_exact')
@flask_login.login_required
def fisher_exact():
	projectNames = getAllProjects(current_user.id)
	currProject = request.args.get('pid', '')
	if currProject == "":
		currProject = projectNames[0]
	catVars = analysis.getMetadataHeaders(current_user.id, currProject)
	uniqueCatVals = analysis.getMetadataUniqueVals(current_user.id, projectNames[0], catVars[0])

	return render_template('fisher_exact.html', projectNames=projectNames, currProject=currProject, catVars=catVars, uniqueCatVals=uniqueCatVals)

@app.route('/enriched_selection')
@flask_login.login_required
def enriched_selection():
	projectNames = getAllProjects(current_user.id)
	currProject = request.args.get('pid', '')
	if currProject == "":
		currProject = projectNames[0]
	catVars = analysis.getMetadataHeaders(current_user.id, currProject)
	uniqueCatVals = analysis.getMetadataUniqueVals(current_user.id, projectNames[0], catVars[0])
	return render_template('enriched_selection.html', projectNames=projectNames, currProject=currProject, catVars=catVars, uniqueCatVals=uniqueCatVals)

@app.route('/glmnet')
@flask_login.login_required
def glmnet():
	projectNames = getAllProjects(current_user.id)
	currProject = request.args.get('pid', '')
	if currProject == "":
		currProject = projectNames[0]
	catVars = analysis.getMetadataHeaders(current_user.id, currProject)

	return render_template('glmnet.html', projectNames=projectNames, currProject=currProject, catVars=catVars)

@app.route('/tree')
@flask_login.login_required
def tree():
	projectNames = getAllProjects(current_user.id)
	currProject = request.args.get('pid', '')
	return render_template('tree_view.html', projectNames=projectNames, currProject=currProject)


# ----- REST endpoints -----

# 
# Sidebar endpoints 
# 

@app.route('/samples')
@flask_login.login_required
def getSamples():
	user = current_user.id
	pid = request.args.get('pid', '')
	if pid == '':
		return json.dumps({})

	abundances = analysis.getMetadataSamples(user, pid)
	return json.dumps(abundances)

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

@app.route('/metadata_vals')
@flask_login.login_required
def getMetadataVals():
	user = current_user.id
	pid = request.args.get('pid', '')
	catvar = request.args.get('catvar', '')
	if pid == '' or catvar == '':
		return json.dumps({})

	uniqueCatVals = analysis.getMetadataUniqueVals(current_user.id, pid, catvar)
	return json.dumps(uniqueCatVals)

# 
# Visualization endpoints 
# 

@app.route('/abundances_grouping', methods=['POST'])
@flask_login.login_required
def getAbundancesGrouping():
	user = current_user.id

	pid = request.form['pid']
	taxonomyFilter = request.form['taxonomyFilter']
	taxonomyFilterVals = request.form['taxonomyFilterVals']
	sampleFilter = request.form['sampleFilter']
	sampleFilterVals = request.form['sampleFilterVals']
	catvar = request.form['catvar']

	taxonomyGroupingGeneral = request.form['taxonomy_group_general']
	taxonomyGroupingSpecific = request.form['taxonomy_group_specific']

	abundances = analysis.getAbundanceForOTUsByGrouping(user, pid, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, catvar, taxonomyGroupingGeneral, taxonomyGroupingSpecific)
	return json.dumps(abundances)

@app.route('/boxplots', methods=['POST'])
@flask_login.login_required
def getBoxplots():
	user = current_user.id

	pid = request.form['pid']
	taxonomyFilter = request.form['taxonomyFilter']
	taxonomyFilterVals = request.form['taxonomyFilterVals']
	sampleFilter = request.form['sampleFilter']
	sampleFilterVals = request.form['sampleFilterVals']
	catvar = request.form['catvar']
	yvals = request.form['yvals']
	taxLevel = request.form['level']

	if yvals == "mian-max" or yvals == "mian-abundance":
		abundances = analysis.getStatsAbundanceForOTUs(user, pid, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, catvar, taxLevel, yvals)
		return json.dumps(abundances)
	else:
		abundances = analysis.getMetadataForCategory(user, pid, sampleFilter, sampleFilterVals, catvar, yvals)
		return json.dumps(abundances)


@app.route('/composition', methods=['POST'])
@flask_login.login_required
def getComposition():
	user = current_user.id

	pid = request.form['pid']
	taxonomyFilter = request.form['taxonomyFilter']
	taxonomyFilterVals = request.form['taxonomyFilterVals']
	sampleFilter = request.form['sampleFilter']
	sampleFilterVals = request.form['sampleFilterVals']
	level = request.form['level']
	catvar = request.form['catvar']

	abundances = analysis.getCompositionAnalysis(user, pid, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, level, catvar)
	return json.dumps(abundances)

@app.route('/correlations', methods=['POST'])
@flask_login.login_required
def getCorrelations():
	user = current_user.id

	pid = request.form['pid']
	taxonomyFilter = request.form['taxonomyFilter']
	taxonomyFilterVals = request.form['taxonomyFilterVals']
	sampleFilter = request.form['sampleFilter']
	sampleFilterVals = request.form['sampleFilterVals']
	corrvar1 = request.form['corrvar1']
	corrvar2 = request.form['corrvar2']
	colorvar = request.form['colorvar']
	sizevar = request.form['sizevar']
	samplestoshow = request.form['samplestoshow']

	abundances = analysis_r_visualizations.correlations(user, pid, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, corrvar1, corrvar2, colorvar, sizevar, samplestoshow)
	return json.dumps(abundances)

@app.route('/isSubsampled', methods=['POST'])
@flask_login.login_required
def getIsSubsampled():
	user = current_user.id
	pid = request.form['pid']

	isSubsampled = analysis.getIsSubsampled(user, pid)
	if isSubsampled:
		return json.dumps(1)
	else:
		return json.dumps(0)

@app.route('/rarefaction', methods=['POST'])
@flask_login.login_required
def getRarefaction():
	user = current_user.id
	pid = request.form['pid']
	subsamplestep = int(request.form['subsamplestep'])

	userUploadFolder = os.path.join(UPLOAD_FOLDER, user)
	destFolder = os.path.join(userUploadFolder, pid)
	destPath = os.path.join(destFolder, analysis.OTU_TABLE_NAME_PRESUBSAMPLE)

	c = Popen(['mothur'], shell=True, stdin=PIPE)
	c.communicate(input="rarefaction.single(shared=" + destPath + ", freq=" + str(subsamplestep) + ")\nquit()")

	abundances = analysis.getRarefaction(user, pid)
	return json.dumps(abundances)


@app.route('/pca', methods=['POST'])
@flask_login.login_required
def getPCA():
	user = current_user.id

	pid = request.form['pid']
	taxonomyFilter = request.form['taxonomyFilter']
	taxonomyFilterVals = request.form['taxonomyFilterVals']
	sampleFilter = request.form['sampleFilter']
	sampleFilterVals = request.form['sampleFilterVals']
	level = request.form['level']
	catvar = request.form['catvar']
	pca1 = request.form['pca1']
	pca2 = request.form['pca2']

	abundances = analysis_r_visualizations.pca(user, pid, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, level, catvar, pca1, pca2)
	return json.dumps(abundances)

@app.route('/nmds', methods=['POST'])
@flask_login.login_required
def getNMDS():
	user = current_user.id

	pid = request.form['pid']
	taxonomyFilter = request.form['taxonomyFilter']
	taxonomyFilterVals = request.form['taxonomyFilterVals']
	sampleFilter = request.form['sampleFilter']
	sampleFilterVals = request.form['sampleFilterVals']
	level = request.form['level']
	catvar = request.form['catvar']

	abundances = analysis_r_visualizations.nmds(user, pid, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, level, catvar)
	return json.dumps(abundances)

@app.route('/tree', methods=['POST'])
@flask_login.login_required
def getTree():
	user = current_user.id

	pid = request.form['pid']
	taxonomyFilter = request.form['taxonomyFilter']
	taxonomyFilterVals = request.form['taxonomyFilterVals']
	sampleFilter = request.form['sampleFilter']
	sampleFilterVals = request.form['sampleFilterVals']
	catvar = request.form['catvar']
	taxonomy_display_level = request.form['taxonomy_display_level']
	display_values = request.form['display_values']
	exclude_unclassified = request.form['exclude_unclassified']

	abundances = analysis.getTreeGrouping(user, pid, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, catvar, taxonomy_display_level, display_values, exclude_unclassified)
	return json.dumps(abundances)



# 
# Alpha Diversity endpoints
# 

@app.route('/alpha_diversity', methods=['POST'])
@flask_login.login_required
def getAlphaDiversity():
	user = current_user.id

	pid = request.form['pid']
	taxonomyFilter = request.form['taxonomyFilter']
	taxonomyFilterVals = request.form['taxonomyFilterVals']
	sampleFilter = request.form['sampleFilter']
	sampleFilterVals = request.form['sampleFilterVals']
	level = request.form['level']
	catvar = request.form['catvar']
	alphaType = request.form['alphaType']
	alphaContext = request.form['alphaContext']

	abundances = analysis_diversity.alphaDiversity(user, pid, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, level, catvar, alphaType, alphaContext)
	return json.dumps(abundances)

@app.route('/beta_diversity', methods=['POST'])
@flask_login.login_required
def getBetaDiversity():
	user = current_user.id

	pid = request.form['pid']
	taxonomyFilter = request.form['taxonomyFilter']
	taxonomyFilterVals = request.form['taxonomyFilterVals']
	sampleFilter = request.form['sampleFilter']
	sampleFilterVals = request.form['sampleFilterVals']
	level = request.form['level']
	catvar = request.form['catvar']
	betaType = request.form['betaType']

	abundances = analysis_diversity.betaDiversity(user, pid, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, level, catvar, betaType)
	return json.dumps(abundances)

# 
# Stats endpoints
# 

@app.route('/boruta', methods=['POST'])
@flask_login.login_required
def getBoruta():
	user = current_user.id

	pid = request.form['pid']
	taxonomyFilter = request.form['taxonomyFilter']
	taxonomyFilterVals = request.form['taxonomyFilterVals']
	sampleFilter = request.form['sampleFilter']
	sampleFilterVals = request.form['sampleFilterVals']
	level = request.form['level']
	catvar = request.form['catvar']
	keepthreshold = request.form['keepthreshold']
	pval = request.form['pval']
	maxruns = request.form['maxruns']

	abundances = analysis_stats.boruta(user, pid, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, level, catvar, keepthreshold, pval, maxruns)
	return json.dumps(abundances)

@app.route('/fisher_exact', methods=['POST'])
@flask_login.login_required
def getFisherExact():
	user = current_user.id

	pid = request.form['pid']
	taxonomyFilter = request.form['taxonomyFilter']
	taxonomyFilterVals = request.form['taxonomyFilterVals']
	sampleFilter = request.form['sampleFilter']
	sampleFilterVals = request.form['sampleFilterVals']
	level = request.form['level']
	catvar = request.form['catvar']
	minthreshold = request.form['minthreshold']
	keepthreshold = request.form['keepthreshold']
	pwVar1 = request.form['pwVar1']
	pwVar2 = request.form['pwVar2']

	abundances = analysis_stats.fisherExact(user, pid, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, level, catvar, minthreshold, keepthreshold, pwVar1, pwVar2)
	return json.dumps(abundances)

@app.route('/enriched_selection', methods=['POST'])
@flask_login.login_required
def getEnrichedSelection():
	user = current_user.id

	pid = request.form['pid']
	taxonomyFilter = request.form['taxonomyFilter']
	taxonomyFilterVals = request.form['taxonomyFilterVals']
	sampleFilter = request.form['sampleFilter']
	sampleFilterVals = request.form['sampleFilterVals']
	level = request.form['level']
	catvar = request.form['catvar']
	enrichedthreshold = request.form['enrichedthreshold']
	pwVar1 = request.form['pwVar1']
	pwVar2 = request.form['pwVar2']

	abundances = analysis_stats.enrichedSelection(user, pid, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, level, catvar, pwVar1, pwVar2, enrichedthreshold)
	return json.dumps(abundances)

@app.route('/glmnet', methods=['POST'])
@flask_login.login_required
def getGlmnet():
	user = current_user.id

	pid = request.form['pid']
	taxonomyFilter = request.form['taxonomyFilter']
	taxonomyFilterVals = request.form['taxonomyFilterVals']
	sampleFilter = request.form['sampleFilter']
	sampleFilterVals = request.form['sampleFilterVals']
	level = request.form['level']
	catvar = request.form['catvar']
	keepthreshold = request.form['keepthreshold']
	alpha = request.form['alpha']
	family = request.form['family']
	lambdathreshold = request.form['lambdathreshold']
	lambdaval = request.form['lambdaval']

	abundances = analysis_stats.glmnet(user, pid, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, level, catvar, keepthreshold, alpha, family, lambdathreshold, lambdaval)
	return json.dumps(abundances)

# ----- Data processing endpoints -----

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ["csv", "taxonomy", "txt", "shared", "tsv"]

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


@app.route('/uploadReplace', methods=['POST'])
@flask_login.login_required
def uploadReplace():
	if request.method == 'POST':
		user = current_user.id
		file = request.files['upload']
		pid = request.form['project']
		fileType = request.form['fileType']
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)

			userUploadFolder = os.path.join(UPLOAD_FOLDER, current_user.id)
			uploadFolder = os.path.join(userUploadFolder, pid)

			if fileType == "otuTable":
				presubsampleFile = os.path.join(uploadFolder, analysis.OTU_TABLE_NAME_PRESUBSAMPLE)
				otuFile = os.path.join(uploadFolder, analysis.OTU_TABLE_NAME)
				if os.path.isfile(presubsampleFile):
					os.remove(presubsampleFile)
				if os.path.isfile(otuFile):
					os.remove(otuFile)

				file.save(presubsampleFile)

				subsampleType = request.form['subsampleType']
				subsampleTo = request.form['subsampleTo']
				print subsampleTo
				subsampleTo = analysis.subsampleOTUTable(user, pid, subsampleType, subsampleTo)

				analysis.changeMapSubsampleType(user, pid, subsampleType)
				analysis.changeMapSubsampleVal(user, pid, subsampleTo)

				analysis.changeMapFilename(user, pid, "otuTable", filename)

				retObj = {}
				retObj["status"] = "OK"
				retObj["subsampleType"] = subsampleType
				retObj["subsampleTo"] = subsampleTo
				retObj["fn"] = filename
				return json.dumps(retObj)

			elif fileType == "otuTaxonomyMapping":
				taxFile = os.path.join(uploadFolder, analysis.TAXONOMY_MAP_NAME)
				if os.path.isfile(taxFile):
					os.remove(taxFile)

				file.save(taxFile)
				analysis.changeMapFilename(user, pid, "otuTaxonomyMapping", filename)

				retObj = {}
				retObj["status"] = "OK"
				retObj["fn"] = filename
				return json.dumps(retObj)

			elif fileType == "otuMetadata":
				metadataFile = os.path.join(uploadFolder, analysis.METADATA_NAME)
				if os.path.isfile(metadataFile):
					os.remove(metadataFile)

				file.save(metadataFile)
				analysis.changeMapFilename(user, pid, "otuMetadata", filename)

				retObj = {}
				retObj["status"] = "OK"
				retObj["fn"] = filename
				return json.dumps(retObj)

		retObj = {}
		retObj["status"] = "Error"
		return retObj

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

@app.route('/changeSubsampling', methods=['POST'])
@flask_login.login_required
def changeSubsampling():
	user = current_user.id
	pid = request.form['pid']
	subsampleType = request.form['subsampleType']
	subsampleTo = request.form['subsampleTo']

	subsampleTo = analysis.subsampleOTUTable(user, pid, subsampleType, subsampleTo)

	analysis.changeMapSubsampleType(user, pid, subsampleType)
	analysis.changeMapSubsampleVal(user, pid, subsampleTo)

	return json.dumps(subsampleTo)

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
	print "App Startup"
	# app.run(debug=True, port=8080)
	# app.run(host='0.0.0.0', debug=True, port=8080)
	app.run()
