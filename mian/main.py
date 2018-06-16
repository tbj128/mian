# ===========================================
#
# mian Main Routing Component
# @author: tbj128
#
# ===========================================

#
# Generic Imports
#
from functools import lru_cache

from flask import Flask, request, render_template, redirect, url_for
import flask_login
from flask_login import current_user
from werkzeug import secure_filename
from sqlite3 import dbapi2 as sqlite3
import os
import random
import json
import hashlib
import shutil
import logging

#
# Imports and installs R packages as needed
#
from mian.core.constants import RAW_OTU_TABLE_FILENAME, SUBSAMPLED_OTU_TABLE_FILENAME, TAXONOMY_FILENAME, \
    SAMPLE_METADATA_FILENAME
from mian.core.project_manager import ProjectManager
from mian.analysis.alpha_diversity import AlphaDiversity
from mian.analysis.beta_diversity import BetaDiversity
from mian.analysis.boruta import Boruta
from mian.analysis.boxplots import Boxplots
from mian.analysis.composition import Composition
from mian.analysis.correlations import Correlations
from mian.analysis.correlation_network import CorrelationNetwork
from mian.analysis.enriched_selection import EnrichedSelection
from mian.analysis.fisher_exact import FisherExact
from mian.analysis.glmnet import GLMNet
from mian.analysis.nmds import NMDS
from mian.analysis.pca import PCA
from mian.analysis.random_forest import RandomForest
from mian.analysis.rarefaction_curves import RarefactionCurves
from mian.analysis.table_view import TableView
from mian.analysis.tree_view import TreeView
from mian.db import db
from mian.model.user_request import UserRequest
from mian.rutils import r_package_install
from mian.model.map import Map
from mian.model.taxonomy import Taxonomy
from mian.model.metadata import Metadata

r_package_install.importr_custom("vegan")
r_package_install.importr_custom("RColorBrewer")
r_package_install.importr_custom("ranger")
r_package_install.importr_custom("Boruta")
r_package_install.importr_custom("glmnet")


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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the web app
app = Flask(__name__)

# Initialize the login manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

# Initialize the database if applicable
db.initDB(DB_PATH, SCHEMA_PATH)


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

        return render_template('login.html', badlogin=1)


@app.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect(url_for('login'))


@app.route('/projects')
@flask_login.login_required
def projects():
    new_signup = False
    if request.args.get('signup', '') == '1':
        new_signup = True
    project_names_to_info = get_project_ids_to_info(current_user.id)
    logger.info(str(project_names_to_info))
    return render_template('projects.html', newSignup=new_signup, projectNames=project_names_to_info)


@app.route('/create', methods=['GET', 'POST'])
@flask_login.login_required
def create():
    if request.method == 'GET':
        return render_template('create.html')
    else:
        project_manager = ProjectManager(current_user.id)
        project_name = secure_filename(request.form['projectName'])
        project_type = request.form['projectUploadType']
        project_subsample_type = request.form['projectSubsampleType']
        project_subsample_to = request.form['projectSubsampleTo']

        if project_type == "biom":
            # Biom files are self-contained - they must be split up and subsampled to be compatible with mian
            project_biom_name = secure_filename(request.form['projectBiomName'])
            project_manager.create_project_from_biom(project_name=project_name,
                                                     biom_name=project_biom_name,
                                                     subsample_type=project_subsample_type,
                                                     subsample_to=project_subsample_to)
        else:
            # Users can also choose to manually upload files
            project_otu_table_name = secure_filename(request.form['projectOTUTableName'])
            project_taxa_map_name = secure_filename(request.form['projectTaxaMapName'])
            project_sample_id_name = secure_filename(request.form['projectSampleIDName'])
            project_manager.create_project_from_tsv(project_name=project_name,
                                                    otu_filename=project_otu_table_name,
                                                    taxonomy_filename=project_taxa_map_name,
                                                    sample_metadata_filename=project_sample_id_name,
                                                    subsample_type=project_subsample_type,
                                                    subsample_to=project_subsample_to)

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
    projectNames = get_project_ids_to_info(current_user.id)
    currProject = request.args.get('pid', '')
    return render_template('boxplots.html', projectNames=projectNames, currProject=currProject)


@app.route('/alpha_diversity')
@flask_login.login_required
def alpha_diversity():
    projectNames = get_project_ids_to_info(current_user.id)
    currProject = request.args.get('pid', '')
    return render_template('alpha_diversity.html', projectNames=projectNames, currProject=currProject)


@app.route('/beta_diversity')
@flask_login.login_required
def beta_diversity():
    projectNames = get_project_ids_to_info(current_user.id)
    currProject = request.args.get('pid', '')
    return render_template('beta_diversity.html', projectNames=projectNames, currProject=currProject)


@app.route('/boruta')
@flask_login.login_required
def boruta():
    projectNames = get_project_ids_to_info(current_user.id)
    currProject = request.args.get('pid', projectNames[list(projectNames.keys())[0]]['pid'])
    metadata = Metadata(current_user.id, currProject)
    catVars = metadata.get_metadata_headers()

    return render_template('boruta.html', projectNames=projectNames, currProject=currProject, catVars=catVars)


@app.route('/composition')
@flask_login.login_required
def composition():
    projectNames = get_project_ids_to_info(current_user.id)
    currProject = request.args.get('pid', '')
    return render_template('composition.html', projectNames=projectNames, currProject=currProject)


@app.route('/correlations')
@flask_login.login_required
def correlations():
    # TODO: Consider using only factors in the future for catVars
    projectNames = get_project_ids_to_info(current_user.id)
    currProject = request.args.get('pid', projectNames[list(projectNames.keys())[0]]['pid'])
    metadata = Metadata(current_user.id, currProject)
    catVars = metadata.get_metadata_headers()
    numericCatVars = metadata.get_numeric_metadata_headers()
    return render_template('correlations.html', projectNames=projectNames, currProject=currProject, catVars=catVars, numericCatVars=numericCatVars)


@app.route('/correlation_network')
@flask_login.login_required
def correlation_network():
    projectNames = get_project_ids_to_info(current_user.id)
    currProject = request.args.get('pid', projectNames[list(projectNames.keys())[0]]['pid'])
    metadata = Metadata(current_user.id, currProject)
    catVars = metadata.get_metadata_headers()

    return render_template('correlation_network.html', projectNames=projectNames, currProject=currProject, catVars=catVars)


@app.route('/enriched_selection')
@flask_login.login_required
def enriched_selection():
    projectNames = get_project_ids_to_info(current_user.id)
    currProject = request.args.get('pid', projectNames[list(projectNames.keys())[0]]['pid'])
    metadata = Metadata(current_user.id, currProject)
    catVars = metadata.get_metadata_headers()
    uniqueCatVals = metadata.get_metadata_unique_vals(catVars[0])
    return render_template('enriched_selection.html', projectNames=projectNames, currProject=currProject, catVars=catVars, uniqueCatVals=uniqueCatVals)


@app.route('/fisher_exact')
@flask_login.login_required
def fisher_exact():
    projectNames = get_project_ids_to_info(current_user.id)
    currProject = request.args.get('pid', projectNames[list(projectNames.keys())[0]]['pid'])
    metadata = Metadata(current_user.id, currProject)
    catVars = metadata.get_metadata_headers()
    uniqueCatVals = metadata.get_metadata_unique_vals(catVars[0])

    return render_template('fisher_exact.html', projectNames=projectNames, currProject=currProject, catVars=catVars, uniqueCatVals=uniqueCatVals)


@app.route('/glmnet')
@flask_login.login_required
def glmnet():
    projectNames = get_project_ids_to_info(current_user.id)
    currProject = request.args.get('pid', projectNames[list(projectNames.keys())[0]]['pid'])
    metadata = Metadata(current_user.id, currProject)
    catVars = metadata.get_metadata_headers()

    return render_template('glmnet.html', projectNames=projectNames, currProject=currProject, catVars=catVars)


@app.route('/nmds')
@flask_login.login_required
def nmds():
    projectNames = get_project_ids_to_info(current_user.id)
    currProject = request.args.get('pid', '')
    return render_template('nmds.html', projectNames=projectNames, currProject=currProject)


@app.route('/pca')
@flask_login.login_required
def pca():
    projectNames = get_project_ids_to_info(current_user.id)
    currProject = request.args.get('pid', '')
    return render_template('pca.html', projectNames=projectNames, currProject=currProject)


@app.route('/random_forest')
@flask_login.login_required
def random_forest():
    projectNames = get_project_ids_to_info(current_user.id)
    currProject = request.args.get('pid', '')
    return render_template('random_forest.html', projectNames=projectNames, currProject=currProject)


@app.route('/rarefaction')
@flask_login.login_required
def rarefaction():
    projectNames = get_project_ids_to_info(current_user.id)
    currProject = request.args.get('pid', '')
    return render_template('rarefaction.html', projectNames=projectNames, currProject=currProject)


@app.route('/table')
@flask_login.login_required
def table():
    projectNames = get_project_ids_to_info(current_user.id)
    currProject = request.args.get('pid', '')
    return render_template('table_view.html', projectNames=projectNames, currProject=currProject)


@app.route('/tree')
@flask_login.login_required
def tree():
    projectNames = get_project_ids_to_info(current_user.id)
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

    abundances = Metadata.get_metadata_samples(user, pid)
    return json.dumps(abundances)


@app.route('/taxonomies')
@flask_login.login_required
def getTaxonomies():
    logger.info("Getting taxonomies")
    user = current_user.id
    pid = request.args.get('pid', '')
    if pid == '':
        return json.dumps({})

    taxonomy = Taxonomy(user, pid)
    abundances = taxonomy.get_taxonomy_map()
    logger.info("Returning taxonomies")
    return json.dumps(abundances)


@app.route('/metadata_headers')
@flask_login.login_required
def getMetadataHeaders():
    user = current_user.id
    pid = request.args.get('pid', '')
    if pid == '':
        return json.dumps({})

    metadata = Metadata(user, pid)
    abundances = metadata.get_metadata_headers()
    return json.dumps(abundances)

@app.route('/metadata_headers_with_type')
@flask_login.login_required
def getMetadataHeadersWithType():
    user = current_user.id
    pid = request.args.get('pid', '')
    if pid == '':
        return json.dumps({})

    metadata = Metadata(user, pid)
    abundances = metadata.get_metadata_headers_with_type()
    return json.dumps(abundances)

@app.route('/metadata_numeric_headers')
@flask_login.login_required
def getMetadataNumericHeaders():
    user = current_user.id
    pid = request.args.get('pid', '')
    if pid == '':
        return json.dumps({})

    metadata = Metadata(user, pid)
    abundances = metadata.get_numeric_metadata_headers()
    return json.dumps(abundances)

@app.route('/metadata_vals')
@flask_login.login_required
def getMetadataVals():
    user = current_user.id
    pid = request.args.get('pid', '')
    catvar = request.args.get('catvar', '')
    if pid == '' or catvar == '':
        return json.dumps({})

    metadata = Metadata(user, pid)
    uniqueCatVals = metadata.get_metadata_unique_vals(catvar)
    return json.dumps(uniqueCatVals)



# Visualization endpoints

@app.route('/alpha_diversity', methods=['POST'])
@flask_login.login_required
def getAlphaDiversity():
    user_request = __get_user_request(request)
    user_request.set_custom_attr("alphaType", request.form['alphaType'])
    user_request.set_custom_attr("alphaContext", request.form['alphaContext'])

    plugin = AlphaDiversity()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


@app.route('/beta_diversity', methods=['POST'])
@flask_login.login_required
def getBetaDiversity():
    user_request = __get_user_request(request)
    user_request.set_custom_attr("betaType", request.form['betaType'])

    plugin = BetaDiversity()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


@app.route('/boruta', methods=['POST'])
@flask_login.login_required
def getBoruta():
    user_request = __get_user_request(request)
    user_request.set_custom_attr("keepthreshold", request.form['keepthreshold'])
    user_request.set_custom_attr("pval", request.form['pval'])
    user_request.set_custom_attr("maxruns", request.form['maxruns'])

    plugin = Boruta()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


@app.route('/boxplots', methods=['POST'])
@flask_login.login_required
def getBoxplots():
    user_request = __get_user_request(request)
    user_request.set_custom_attr("yvals", request.form['yvals'])

    plugin = Boxplots()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


@app.route('/composition', methods=['POST'])
@flask_login.login_required
def getComposition():
    user_request = __get_user_request(request)
    plugin = Composition()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


@app.route('/correlations', methods=['POST'])
@flask_login.login_required
def getCorrelations():
    user_request = __get_user_request(request)
    user_request.set_custom_attr("corrvar1", request.form['corrvar1'])
    user_request.set_custom_attr("corrvar2", request.form['corrvar2'])
    user_request.set_custom_attr("colorvar", request.form['colorvar'])
    user_request.set_custom_attr("sizevar", request.form['sizevar'])
    user_request.set_custom_attr("samplestoshow", request.form['samplestoshow'])

    plugin = Correlations()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


@app.route('/correlation_network', methods=['POST'])
@flask_login.login_required
def getCorrelationNetwork():
    user_request = __get_user_request(request)
    user_request.set_custom_attr("maxFeatures", request.form['maxFeatures'])
    user_request.set_custom_attr("cutoff", request.form['cutoff'])

    plugin = CorrelationNetwork()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


@app.route('/enriched_selection', methods=['POST'])
@flask_login.login_required
def getEnrichedSelection():
    user_request = __get_user_request(request)
    user_request.set_custom_attr("enrichedthreshold", request.form['enrichedthreshold'])
    user_request.set_custom_attr("pwVar1", request.form['pwVar1'])
    user_request.set_custom_attr("pwVar2", request.form['pwVar2'])

    plugin = EnrichedSelection()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


@app.route('/fisher_exact', methods=['POST'])
@flask_login.login_required
def getFisherExact():
    user_request = __get_user_request(request)
    user_request.set_custom_attr("minthreshold", request.form['minthreshold'])
    user_request.set_custom_attr("keepthreshold", request.form['keepthreshold'])
    user_request.set_custom_attr("pwVar1", request.form['pwVar1'])
    user_request.set_custom_attr("pwVar2", request.form['pwVar2'])

    plugin = FisherExact()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


@app.route('/glmnet', methods=['POST'])
@flask_login.login_required
def getGlmnet():
    user_request = __get_user_request(request)
    user_request.set_custom_attr("keepthreshold", request.form['keepthreshold'])
    user_request.set_custom_attr("alpha", request.form['alpha'])
    user_request.set_custom_attr("family", request.form['family'])
    user_request.set_custom_attr("lambdathreshold", request.form['lambdathreshold'])
    user_request.set_custom_attr("lambdaval", request.form['lambdaval'])

    plugin = GLMNet()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


@app.route('/random_forest', methods=['POST'])
@flask_login.login_required
def getRandomForest():
    user_request = __get_user_request(request)
    user_request.set_custom_attr("numTrees", request.form['numTrees'])
    user_request.set_custom_attr("maxDepth", request.form['maxDepth'])

    plugin = RandomForest()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


@app.route('/rarefaction', methods=['POST'])
@flask_login.login_required
def getRarefaction():
    print("getRarefaction")
    user_request = __get_user_request(request)
    # subsamplestep = int(request.form['subsamplestep'])

    plugin = RarefactionCurves()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


@app.route('/nmds', methods=['POST'])
@flask_login.login_required
def getNMDS():
    plugin = NMDS()
    abundances = plugin.run(__get_user_request(request))
    return json.dumps(abundances)


@app.route('/pca', methods=['POST'])
@flask_login.login_required
def getPCA():
    user_request = __get_user_request(request)
    user_request.set_custom_attr("pca1", request.form['pca1'])
    user_request.set_custom_attr("pca2", request.form['pca2'])

    plugin = PCA()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)

@app.route('/table', methods=['POST'])
@flask_login.login_required
def getTable():
    user_request = __get_user_request(request)
    plugin = TableView()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)

@app.route('/tree', methods=['POST'])
@flask_login.login_required
def getTree():
    user_request = __get_user_request(request)
    user_request.set_custom_attr("taxonomy_display_level", request.form['taxonomy_display_level'])
    user_request.set_custom_attr("display_values", request.form['display_values'])
    user_request.set_custom_attr("exclude_unclassified", request.form['exclude_unclassified'])
    plugin = TreeView()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


#
# Misc endpoints
#

@app.route('/isSubsampled', methods=['POST'])
@flask_login.login_required
def getIsSubsampled():
    user = current_user.id
    pid = request.form['pid']

    return json.dumps(1)

    # isSubsampled = Subsample.get_is_subsampled(user, pid)
    # if isSubsampled:
    #     return json.dumps(1)
    # else:
    #     return json.dumps(0)



# ----- Data processing endpoints -----

def __get_user_request(request):
    user = current_user.id
    pid = request.form['pid']
    taxonomyFilter = request.form['taxonomyFilter'] if 'taxonomyFilter' in request.form else ""
    taxonomyFilterRole = request.form['taxonomyFilterRole'] if 'taxonomyFilterRole' in request.form else ""
    taxonomyFilterVals = request.form['taxonomyFilterVals'] if 'taxonomyFilterVals' in request.form else ""
    sampleFilter = request.form['sampleFilter'] if 'sampleFilter' in request.form else ""
    sampleFilterRole = request.form['sampleFilterRole'] if 'sampleFilterRole' in request.form else ""
    sampleFilterVals = request.form['sampleFilterVals'] if 'sampleFilterVals' in request.form else ""
    catvar = request.form['catvar'] if 'catvar' in request.form else ""
    level = request.form['level'] if 'level' in request.form else -2
    user_request = UserRequest(user, pid, taxonomyFilter, taxonomyFilterRole, taxonomyFilterVals,
                               sampleFilter, sampleFilterRole, sampleFilterVals, level, catvar)
    return user_request

@app.route('/upload', methods=['POST'])
@flask_login.login_required
def upload():
    if request.method == 'POST':
        file = request.files['upload']
        logger.info("Uploading file " + str(file.filename) + " for user " + str(current_user.id))
        if file:
            filename = secure_filename(file.filename)

            user_staging_dir = os.path.join(ProjectManager.STAGING_DIRECTORY, current_user.id)
            logger.info("Files will be temporarily put into a staging directory " + str(user_staging_dir))

            if not os.path.exists(user_staging_dir):
                logger.info("Making staging directory for user " + str(current_user.id))
                os.makedirs(user_staging_dir)

            file.save(os.path.join(user_staging_dir, filename))
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
        if file:
            filename = secure_filename(file.filename)
            user_staging_dir = os.path.join(ProjectManager.STAGING_DIRECTORY, current_user.id)
            if not os.path.exists(user_staging_dir):
                logger.info("Making staging directory for user " + str(current_user.id))
                os.makedirs(user_staging_dir)

            file.save(os.path.join(user_staging_dir, filename))

            project_manager = ProjectManager(user)

            if fileType == "biom":
                project_manager.update_project_from_biom(pid, filename)
            elif fileType == "otuTable":
                project_manager.update_project_from_tsv(pid, filename, None, None)
            elif fileType == "otuTaxonomyMapping":
                project_manager.update_project_from_tsv(pid, None, filename, None)
            elif fileType == "otuMetadata":
                project_manager.update_project_from_tsv(pid, None, None, filename)

            return json.dumps({
                "status": "OK"
            })

    return json.dumps({
        "status": "ERROR"
    })


@app.route('/deleteProject', methods=['POST'])
@flask_login.login_required
def deleteProject():
    if request.method == 'POST':
        project = request.form['project']
        deleteConfirm = request.form['delete']
        if deleteConfirm == "delete" and project != "":
            userUploadFolder = os.path.join(UPLOAD_FOLDER, current_user.id)
            userProjectFolder = os.path.join(userUploadFolder, project)
            logger.info("Deleting project at path %s", userProjectFolder)
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

    project_manager = ProjectManager(user)
    subsample_value = project_manager.modify_subsampling(pid, subsampleType, subsampleTo)

    return json.dumps(subsample_value)

# ------------------
# Helpers
# ------------------

#
# Auth helper methods
#


@login_manager.user_loader
def user_loader(id):
    userEmail = getUserEmail(id)
    if userEmail == "":
        return
    user = User(userEmail, id, True)
    return user


def createSalt():
    """
    Creates a random 16 character salt
    """
    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    chars=[]
    for i in range(16):
        chars.append(random.choice(ALPHABET))
    return "".join(chars)


def addUser(username, password):
    """
    Inserts a new user into the database
    """

    db = sqlite3.connect(DB_PATH)
    c = db.cursor()

    salt = createSalt()

    calculatedPassword = hashlib.md5(str(salt + password).encode('utf-8')).hexdigest()
    c.execute('INSERT INTO accounts (user_email, password_hash, salt) VALUES (?,?,?)', (username, calculatedPassword, salt))
    db.commit()
    db.close()


def getUserEmail(userID):
    """
    Retrieves the user email given the user ID
    """
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
    """
    Used during login to check if the user credentials are correct
    """
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
        calculatedPassword = hashlib.md5(str(salt + password).encode('utf-8')).hexdigest()
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


# Project Helpers

# @lru_cache(maxsize=1048576)
def get_project_ids_to_info(user_id):
    """
    Gets a mapping of all project names to IDs
    :return:
    """
    project_name_to_info = {}
    user_dir = os.path.join(ProjectManager.DATA_DIRECTORY, user_id)
    for subdir, dirs, files in os.walk(user_dir):
        for dir in dirs:
            logger.info("Found project directory " + str(dir) + " for user " + str(user_id))
            if dir != ProjectManager.STAGING_DIRECTORY:
                pid = dir
                project_map = Map(user_id, pid)
                project_info = {}
                if project_map.orig_biom_name != "":
                    project_type = "biom"
                    project_info = {
                        "project_name": project_map.project_name,
                        "pid": pid,
                        "project_type": project_type,
                        "orig_biom_name": project_map.orig_biom_name,
                        "subsampled_value": project_map.subsampled_value,
                        "subsampled_type": project_map.subsampled_type
                    }
                else:
                    project_type = "table"
                    project_info = {
                        "project_name": project_map.project_name,
                        "pid": pid,
                        "project_type": project_type,
                        "orig_otu_table_name": project_map.orig_otu_table_name,
                        "orig_sample_metadata_name": project_map.orig_sample_metadata_name,
                        "orig_taxonomy_name": project_map.orig_taxonomy_name,
                        "subsampled_value": project_map.subsampled_value,
                        "subsampled_type": project_map.subsampled_type
                    }
                logger.info("Read project info " + str(project_info))
                project_name_to_info[project_map.project_name] = project_info
    return project_name_to_info
