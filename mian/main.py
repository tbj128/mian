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

from flask import Flask, request, render_template, redirect, url_for, Response, abort
from flask_mail import Mail, Message
import flask_login
from flask_login import current_user
from werkzeug import secure_filename
from sqlite3 import dbapi2 as sqlite3
from urllib.parse import unquote
import random
import json
import hashlib
import shutil
import base64
import zlib
import time
import uuid
import logging
#
# Imports and installs R packages as needed
#
import os
import pwd

from mian.core.data_io import DataIO
from mian.rutils import r_package_install
from mian.model.quantiles import Quantiles
from mian.model.genes import Genes

r_package_install.importr_custom("vegan", version="2.5.4")
r_package_install.importr_custom("RColorBrewer")
r_package_install.importr_custom("ranger")
r_package_install.importr_custom("Boruta")
r_package_install.importr_custom("glmnet")

from mian.core.project_manager import ProjectManager, GENERAL_ERROR, OK
from mian.analysis.alpha_diversity import AlphaDiversity
from mian.analysis.beta_diversity import BetaDiversity
from mian.analysis.boruta import Boruta
from mian.analysis.boxplots import Boxplots
from mian.analysis.composition import Composition
from mian.analysis.composition_heatmap import CompositionHeatmap
from mian.analysis.correlations import Correlations
from mian.analysis.correlation_network import CorrelationNetwork
from mian.analysis.correlations_selection import CorrelationsSelection
from mian.analysis.differential_selection import DifferentialSelection
from mian.analysis.fisher_exact import FisherExact
from mian.analysis.glmnet import GLMNet
from mian.analysis.heatmap import Heatmap
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
from mian.model.otu_table import OTUTable

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
app.config.update(
    MAIL_SERVER='email-smtp.us-east-1.amazonaws.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ['MAIL_USERNAME'] if 'MAIL_USERNAME' in os.environ else "",
    MAIL_PASSWORD=os.environ['MAIL_PASSWORD'] if 'MAIL_PASSWORD' in os.environ else ""
)
mail = Mail(app)

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
    next = url_for(request.endpoint, **request.args)
    return redirect(url_for('login', next=next))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    else:
        email = request.form['inputName']
        password = request.form['inputPassword']

        # Checks that the user doesn't already exist
        if checkUserExists(email):
            return render_template('signup.html', exists=1)

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

        return render_template('signup.html', error=1)


def redirect_dest(fallback):
    dest = request.referrer
    try:
        dest = unquote(dest.split("next=")[1])
        return redirect(dest)
    except:
        return redirect(fallback)


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
            return redirect_dest(fallback=url_for('projects'))

        return render_template('login.html', badlogin=1)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot_password.html')
    else:
        email = request.form['email']
        sendResetPasswordLink(email)
        return render_template('forgot_password_check_link.html')


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'GET':
        id = request.args.get('id', '')
        secret = request.args.get('secret', '')
        return render_template('reset_password.html', user=id, secret=secret)
    else:
        user = request.form['user']
        secret = request.form['secret']
        password = request.form['password']

        success = resetPassword(user, secret, password)

        if success:
            return render_template('login.html')
        else:
            return render_template('login.html', badlogin=2)


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'GET':
        return render_template('change_password.html')
    else:
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        success = changePassword(current_user.id, old_password, new_password)

        if success:
            return render_template('change_password.html', success=1)
        else:
            return render_template('change_password.html', error=1)


@app.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    if request.args.get('signup', '') == '1':
        return redirect(url_for('signup'))
    else:
        return redirect(url_for('login'))


@app.route('/projects')
@flask_login.login_required
def projects():
    new_signup = False
    if request.args.get('signup', '') == '1':
        new_signup = True
    status = request.args.get('status', '')
    message = request.args.get('message', '')
    project_names_to_info = get_project_ids_to_info(current_user.id)
    is_demo = current_user.name == "demo@miandata.org"
    return render_template('projects.html', demo=is_demo, newSignup=new_signup, projectNames=project_names_to_info, status=status, message=message)


@app.route('/quantile_manager')
@flask_login.login_required
def quantile_manager():
    pid = request.args.get('pid', '')
    project_names_to_info = get_project_ids_to_info(current_user.id)
    project_name = project_names_to_info[pid]["project_name"]
    quantiles = Quantiles(current_user.id, pid)
    sample_metadata = Metadata(current_user.id, pid)
    return render_template('quantile_manager.html', pid=pid, projectName=project_name, quantiles=quantiles.quantiles, metadataHeaders=sample_metadata.get_metadata_headers_with_type())


@app.route('/create', methods=['GET', 'POST'])
@flask_login.login_required
def create():
    if request.method == 'GET':
        return render_template('create.html')
    else:
        project_manager = ProjectManager(current_user.id)
        project_name = request.form['projectName']
        project_type = request.form['projectUploadType']

        if project_type == "biom":
            # Biom files are self-contained - they must be split up and subsampled to be compatible with mian
            project_biom_name = secure_filename(request.form['projectBiomName'])
            project_phylogenetic_name = secure_filename(request.form['projectPhylogeneticName'])
            project_gene_name = secure_filename(request.form['projectGeneName'])
            project_sample_id_name = secure_filename(request.form['projectSampleIDName'])
            try:
                status, message = project_manager.stage_project_from_biom(project_name=project_name,
                                                                          biom_name=project_biom_name,
                                                                          sample_metadata_filename=project_sample_id_name,
                                                                          gene_filename=project_gene_name,
                                                                          phylogenetic_filename=project_phylogenetic_name)
            except:
                return redirect(url_for('projects', status=GENERAL_ERROR, message=""))
        else:
            # Users can also choose to manually upload files
            project_otu_table_name = secure_filename(request.form['projectOTUTableName'])
            project_taxa_map_name = secure_filename(request.form['projectTaxaMapName'])
            project_sample_id_name = secure_filename(request.form['projectSampleIDName'])
            project_phylogenetic_name = secure_filename(request.form['projectPhylogeneticName'])
            project_gene_name = secure_filename(request.form['projectGeneName'])
            try:
                status, message = project_manager.stage_project_from_tsv(project_name=project_name,
                                                                         otu_filename=project_otu_table_name,
                                                                         taxonomy_filename=project_taxa_map_name,
                                                                         sample_metadata_filename=project_sample_id_name,
                                                                         gene_filename=project_gene_name,
                                                                         phylogenetic_filename=project_phylogenetic_name)
            except:
                return redirect(url_for('projects', status=GENERAL_ERROR, message=""))

        if status == OK:
            return redirect(url_for('createFilter', pid=message))
        else:
            return redirect(url_for('projects', status=status, message=message))


@app.route('/create_filter', methods=['GET', 'POST'])
@flask_login.login_required
def createFilter():
    if request.method == 'GET':
        pid = request.args.get('pid', '')
        return render_template('create-filter.html', pid=pid)
    else:
        project_manager = ProjectManager(current_user.id)
        pid = request.form['project']
        project_subsample_type = request.form['projectSubsampleType']
        project_subsample_to = request.form['projectSubsampleTo']
        sampleFilter = request.form['sampleFilter'] if 'sampleFilter' in request.form else ""
        sampleFilterRole = request.form['sampleFilterRole'] if 'sampleFilterRole' in request.form else ""
        sampleFilterVals = json.loads(request.form['sampleFilterVals']) if 'sampleFilterVals' in request.form else []

        try:
            status, message = project_manager.create_project(pid=pid,
                                                             sampleFilter=sampleFilter,
                                                             sampleFilterRole=sampleFilterRole,
                                                             sampleFilterVals=sampleFilterVals,
                                                             subsample_type=project_subsample_type,
                                                             subsample_to=project_subsample_to)
        except:
            return redirect(url_for('projects', status=GENERAL_ERROR, message=""))

        return redirect(url_for('projects', status=status, message=message))


@app.route('/get_filtering_info', methods=['POST'])
@flask_login.login_required
def getFilterInfo():
    project_manager = ProjectManager(current_user.id)
    pid = request.form['pid']
    sampleFilter = request.form['sampleFilter'] if 'sampleFilter' in request.form else ""
    sampleFilterRole = request.form['sampleFilterRole'] if 'sampleFilterRole' in request.form else ""
    sampleFilterVals = json.loads(request.form['sampleFilterVals']) if 'sampleFilterVals' in request.form else []

    info = project_manager.get_filtering_info(pid, sampleFilter, sampleFilterRole, sampleFilterVals)
    return json.dumps(info)


@app.route('/project_not_found')
def project_not_found():
    return render_template('project_not_found.html')


@app.route('/project_empty')
def project_empty():
    return render_template('project_empty.html')


@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('projects'))
    else:
        return render_template('index.html')


@app.errorhandler(404)
def not_found(e):
    return render_template('not_found.html')


# ----- Analysis Pages -----

#
# Visualization Pages
#


def render_normal(html_file, request, show_low_expression_filtering=False):
    projectNames = get_project_ids_to_info(current_user.id)
    currProject = request.args.get('pid', '')

    if len(projectNames) == 0:
        return redirect(url_for('project_empty'))

    not_found = True
    for projectName in projectNames:
        if projectNames[projectName]['pid'] == currProject or currProject == '':
            not_found = False
    if not_found:
        # The requested project was not found
        return redirect(url_for('project_not_found'))

    if show_low_expression_filtering:
        return render_template(html_file, uid=current_user.id, projectNames=projectNames, currProject=currProject, lowExpressionFilteringEnabled=True, share=False)
    else:
        return render_template(html_file, uid=current_user.id, projectNames=projectNames,
                               currProject=currProject, share=False)


def render_sharing(html_file, request, show_low_expression_filtering=False):
    uid = request.args.get('uid', '')
    pid = request.args.get('pid', '')
    if uid == "" or pid == "":
        redirect(url_for('home'))

    projectNames = get_project_ids_to_info(uid)
    if pid not in projectNames or projectNames[pid]["shared"] == "no":
        return redirect(url_for('home'))

    subProjectNames = {pid: projectNames[pid]}
    if show_low_expression_filtering:
        return render_template(html_file, uid=uid, projectNames=subProjectNames, currProject=pid, lowExpressionFilteringEnabled=True, share=True)
    else:
        return render_template(html_file, uid=uid, projectNames=subProjectNames, currProject=pid, share=True)


@app.route('/alpha_diversity')
@flask_login.login_required
def alpha_diversity():
    return render_normal('alpha_diversity.html', request)


@app.route('/share/alpha_diversity')
def alpha_diversity_share():
    return render_sharing('alpha_diversity.html', request)


@app.route('/beta_diversity')
@flask_login.login_required
def beta_diversity():
    return render_normal('beta_diversity.html', request)


@app.route('/share/beta_diversity')
def beta_diversity_share():
    return render_sharing('beta_diversity.html', request)


@app.route('/boxplots')
@flask_login.login_required
def boxplots():
    return render_normal('boxplots.html', request)


@app.route('/share/boxplots')
def boxplots_share():
    return render_sharing('boxplots.html', request)


@app.route('/composition_bar')
@flask_login.login_required
def compositionBar():
    return render_normal('composition_bar.html', request)


@app.route('/share/composition_bar')
def compositionBar_share():
    return render_sharing('composition_bar.html', request)


@app.route('/composition_donut')
@flask_login.login_required
def compositionDonut():
    return render_normal('composition_donut.html', request)


@app.route('/share/composition_donut')
def compositionDonut_share():
    return render_sharing('composition_donut.html', request)


@app.route('/composition_heatmap')
@flask_login.login_required
def compositionHeatmap():
    return render_normal('composition_heatmap.html', request)


@app.route('/share/composition_heatmap')
def compositionHeatmap_share():
    return render_sharing('composition_heatmap.html', request)


@app.route('/correlations')
@flask_login.login_required
def correlations():
    return render_normal('correlations.html', request)


@app.route('/share/correlations')
def correlations_share():
    return render_sharing('correlations.html', request)


@app.route('/correlation_network')
@flask_login.login_required
def correlation_network():
    return render_normal('correlation_network.html', request, show_low_expression_filtering=True)


@app.route('/share/correlation_network')
def correlation_network_share():
    return render_sharing('correlation_network.html', request, show_low_expression_filtering=True)


@app.route('/correlations_selection')
@flask_login.login_required
def correlations_selection():
    return render_normal('correlations_selection.html', request, show_low_expression_filtering=True)


@app.route('/share/correlations_selection')
def correlations_selection_share():
    return render_sharing('correlations_selection.html', request, show_low_expression_filtering=True)


@app.route('/differential_selection')
@flask_login.login_required
def differential_selection():
    return render_normal('differential_selection.html', request, show_low_expression_filtering=True)


@app.route('/share/differential_selection')
def differential_selection_share():
    return render_sharing('differential_selection.html', request, show_low_expression_filtering=True)


@app.route('/fisher_exact')
@flask_login.login_required
def fisher_exact():
    return render_normal('fisher_exact.html', request, show_low_expression_filtering=True)


@app.route('/share/fisher_exact')
def fisher_exact_share():
    return render_sharing('fisher_exact.html', request, show_low_expression_filtering=True)


@app.route('/glmnet')
@flask_login.login_required
def glmnet():
    return render_normal('glmnet.html', request, show_low_expression_filtering=True)


@app.route('/share/glmnet')
def glmnet_share():
    return render_sharing('glmnet.html', request, show_low_expression_filtering=True)


@app.route('/heatmap')
@flask_login.login_required
def heatmap():
    return render_normal('heatmap.html', request, show_low_expression_filtering=True)


@app.route('/share/heatmap')
def heatmap_share():
    return render_sharing('heatmap.html', request, show_low_expression_filtering=True)


@app.route('/nmds')
@flask_login.login_required
def nmds():
    return render_normal('nmds.html', request)


@app.route('/share/nmds')
def nmds_share():
    return render_sharing('nmds.html', request)


@app.route('/pca')
@flask_login.login_required
def pca():
    return render_normal('pca.html', request)


@app.route('/share/pca')
def pca_share():
    return render_sharing('pca.html', request)


@app.route('/random_forest')
@flask_login.login_required
def random_forest():
    return render_normal('random_forest.html', request, show_low_expression_filtering=True)


@app.route('/share/random_forest')
def random_forest_share():
    return render_sharing('random_forest.html', request, show_low_expression_filtering=True)


@app.route('/rarefaction')
@flask_login.login_required
def rarefaction():
    return render_normal('rarefaction.html', request)


@app.route('/share/rarefaction')
def rarefaction_share():
    return render_sharing('rarefaction.html', request)


@app.route('/table')
@flask_login.login_required
def table():
    return render_normal('table_view.html', request)


@app.route('/share/table')
def table_share():
    return render_sharing('table_view.html', request)


@app.route('/tree')
@flask_login.login_required
def tree():
    return render_normal('tree_view.html', request)


@app.route('/share/tree')
def tree_share():
    return render_sharing('tree_view.html', request)


# ----- REST endpoints -----

#
# Sharing endpoints
#

@app.route('/get_sharing_status')
@flask_login.login_required
def getSharingStatus():
    user = current_user.id
    pid = request.args.get('pid', '')
    if pid == '':
        return json.dumps({})

    map_file = Map(user, pid)
    if map_file.shared == "yes":
        return json.dumps({"share": "yes"})
    else:
        return json.dumps({"share": "no"})


@app.route('/toggle_sharing')
@flask_login.login_required
def toggleSharing():
    user = current_user.id
    pid = request.args.get('pid', '')
    share = request.args.get('share', '')
    if pid == '':
        return json.dumps({})

    map_file = Map(user, pid)
    if share == "yes":
        map_file.shared = "yes"
    else:
        map_file.shared = "no"
    map_file.save()
    return json.dumps({})

#
# Sidebar endpoints
#


@app.route('/taxonomies')
@flask_login.login_required
def getTaxonomiesSecure():
    user = current_user.id
    pid = request.args.get('pid', '')
    if pid == '':
        return json.dumps({})
    return getTaxonomies(user, pid)


@app.route('/share/taxonomies')
def getTaxonomiesShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        pid = request.args.get('pid', '')
        return getTaxonomies(uid, pid)
    else:
        abortNotShared()


def getTaxonomies(user, pid):
    logger.info("Getting taxonomies")

    taxonomy = Taxonomy(user, pid)
    abundances = taxonomy.get_taxonomy_map()
    logger.info("Returning taxonomies")
    return json.dumps(abundances)

# ---


@app.route('/metadata_headers_with_type')
@flask_login.login_required
def getMetadataHeadersWithTypeSecure():
    user = current_user.id
    pid = request.args.get('pid', '')
    if pid == '':
        return json.dumps({})
    return getMetadataHeadersWithType(user, pid)


@app.route('/share/metadata_headers_with_type')
def getMetadataHeadersWithTypeShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        pid = request.args.get('pid', '')
        return getMetadataHeadersWithType(uid, pid)
    else:
        abortNotShared()


def getMetadataHeadersWithType(user, pid):
    metadata = Metadata(user, pid)
    abundances = metadata.get_metadata_headers_with_type()
    return json.dumps(abundances)

# ---


@app.route('/genes')
@flask_login.login_required
def getGenesSecure():
    user = current_user.id
    pid = request.args.get('pid', '')
    type = request.args.get('type', '')
    if pid == '':
        return json.dumps({})
    return getGenes(user, pid, type)


@app.route('/share/genes')
def getGenesShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        pid = request.args.get('pid', '')
        type = request.args.get('type', '')
        return getGenes(uid, pid, type)
    else:
        abortNotShared()


def getGenes(user, pid, type):
    metadata = Genes(user, pid)
    abundances = metadata.get_gene_headers(type)
    return json.dumps(abundances)

# ---


@app.route('/otu_table_headers_at_level')
@flask_login.login_required
def getOTUTableHeadersAtLevelSecure():
    user = current_user.id
    pid = request.args.get('pid', '')
    level = request.args.get('level', '')
    if pid == '' or level == '':
        return json.dumps({})
    return getOTUTableHeadersAtLevel(user, pid, level)


@app.route('/share/otu_table_headers_at_level')
def getOTUTableHeadersAtLevelShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        pid = request.args.get('pid', '')
        level = request.args.get('level', '')
        return getOTUTableHeadersAtLevel(uid, pid, level)
    else:
        abortNotShared()


def getOTUTableHeadersAtLevel(user, pid, level):
    headers = OTUTable.get_otu_table_headers_at_taxonomic_level(user, pid, level)
    return json.dumps(headers)

# ---


@app.route('/metadata_vals')
@flask_login.login_required
def getMetadataValsSecure():
    user = current_user.id
    pid = request.args.get('pid', '')
    catvar = request.args.get('catvar', '')
    if pid == '' or catvar == '':
        return json.dumps({})
    return getMetadataVals(user, pid, catvar)


@app.route('/share/metadata_vals')
def getMetadataValsShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        pid = request.args.get('pid', '')
        catvar = request.args.get('catvar', '')
        return getMetadataVals(uid, pid, catvar)
    else:
        abortNotShared()


def getMetadataVals(user, pid, catvar):
    metadata = Metadata(user, pid)
    uniqueCatVals = metadata.get_metadata_unique_vals(catvar)
    return json.dumps(uniqueCatVals)

# ---



# Visualization endpoints


@app.route('/alpha_diversity', methods=['POST'])
@flask_login.login_required
def getAlphaDiversitySecure():
    user_request = __get_user_request(request)
    return getAlphaDiversity(user_request, request)


@app.route('/share/alpha_diversity', methods=['POST'])
def getAlphaDiversityShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getAlphaDiversity(user_request, request)
    else:
        abortNotShared()


def getAlphaDiversity(user_request, req):
    user_request.set_custom_attr("expvar", req.form['expvar'])
    user_request.set_custom_attr("colorvar", req.form['colorvar'])
    user_request.set_custom_attr("sizevar", req.form['sizevar'])
    user_request.set_custom_attr("plotType", req.form['plotType'])
    user_request.set_custom_attr("alphaType", req.form['alphaType'])
    user_request.set_custom_attr("alphaContext", req.form['alphaContext'])
    user_request.set_custom_attr("statisticalTest", req.form['statisticalTest'])

    plugin = AlphaDiversity()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# --


@app.route('/beta_diversity', methods=['POST'])
@flask_login.login_required
def getBetaDiversitySecure():
    user_request = __get_user_request(request)
    return getBetaDiversity(user_request, request)


@app.route('/share/beta_diversity', methods=['POST'])
def getBetaDiversityShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getBetaDiversity(user_request, request)
    else:
        abortNotShared()


def getBetaDiversity(user_request, req):
    user_request.set_custom_attr("colorvar", req.form['colorvar'])
    user_request.set_custom_attr("betaType", req.form['betaType'])
    user_request.set_custom_attr("strata", req.form['strata'])
    user_request.set_custom_attr("api", "beta")

    plugin = BetaDiversity()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# --


@app.route('/beta_diversity_permanova', methods=['POST'])
@flask_login.login_required
def getBetaDiversityPERMANOVASecure():
    user_request = __get_user_request(request)
    return getBetaDiversityPERMANOVA(user_request, request)


@app.route('/share/beta_diversity_permanova', methods=['POST'])
def getBetaDiversityPERMANOVAShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getBetaDiversityPERMANOVA(user_request, request)
    else:
        abortNotShared()


def getBetaDiversityPERMANOVA(user_request, req):
    user_request.set_custom_attr("colorvar", req.form['colorvar'])
    user_request.set_custom_attr("betaType", req.form['betaType'])
    user_request.set_custom_attr("strata", req.form['strata'])
    user_request.set_custom_attr("api", "permanova")

    plugin = BetaDiversity()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# --


@app.route('/boruta', methods=['POST'])
@flask_login.login_required
def getBorutaSecure():
    user_request = __get_user_request(request)
    return getBoruta(user_request, request)


@app.route('/share/boruta', methods=['POST'])
def getBorutaShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getBoruta(user_request, request)
    else:
        abortNotShared()


def getBoruta(user_request, req):
    user_request.set_custom_attr("pval", req.form['pval'])
    user_request.set_custom_attr("maxruns", req.form['maxruns'])

    plugin = Boruta()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# --


@app.route('/boxplots', methods=['POST'])
@flask_login.login_required
def getBoxplotsSecure():
    user_request = __get_user_request(request)
    return getBoxplots(user_request, request)


@app.route('/share/boxplots', methods=['POST'])
def getBoxplotsShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getBoxplots(user_request, request)
    else:
        abortNotShared()


def getBoxplots(user_request, req):
    user_request.set_custom_attr("yvals", req.form['yvals'])
    user_request.set_custom_attr("colorvar", req.form['colorvar'])
    user_request.set_custom_attr("yvalsSpecificTaxonomy", req.form['yvalsSpecificTaxonomy'])
    user_request.set_custom_attr("statisticalTest", req.form['statisticalTest'])

    plugin = Boxplots()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# --


@app.route('/composition', methods=['POST'])
@flask_login.login_required
def getCompositionSecure():
    user_request = __get_user_request(request)
    return getComposition(user_request, request)


@app.route('/share/composition', methods=['POST'])
def getCompositionShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getComposition(user_request, request)
    else:
        abortNotShared()


def getComposition(user_request, req):
    plugin = Composition()
    user_request.set_custom_attr("plotType", req.form['plotType'])
    user_request.set_custom_attr("xaxis", req.form['xaxis'])
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# --


@app.route('/composition_heatmap', methods=['POST'])
@flask_login.login_required
def getCompositionHeatmapSecure():
    user_request = __get_user_request(request)
    return getCompositionHeatmap(user_request, request)


@app.route('/share/composition_heatmap', methods=['POST'])
def getCompositionHeatmapShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getCompositionHeatmap(user_request, request)
    else:
        abortNotShared()


def getCompositionHeatmap(user_request, req):
    plugin = CompositionHeatmap()
    user_request.set_custom_attr("rows", req.form['rows'])
    user_request.set_custom_attr("cols", req.form['cols'])
    user_request.set_custom_attr("clustersamples", req.form['clustersamples'])
    user_request.set_custom_attr("clustertaxonomic", req.form['clustertaxonomic'])
    user_request.set_custom_attr("showlabels", req.form['showlabels'])
    user_request.set_custom_attr("colorscheme", req.form['colorscheme'])
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# ---


@app.route('/correlations', methods=['POST'])
@flask_login.login_required
def getCorrelationsSecure():
    user_request = __get_user_request(request)
    return getCorrelations(user_request, request)


@app.route('/share/correlations', methods=['POST'])
def getCorrelationsShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getCorrelations(user_request, request)
    else:
        abortNotShared()


def getCorrelations(user_request, req):
    user_request.set_custom_attr("corrvar1", req.form['corrvar1'])
    user_request.set_custom_attr("corrvar2", req.form['corrvar2'])
    user_request.set_custom_attr("colorvar", req.form['colorvar'])
    user_request.set_custom_attr("sizevar", req.form['sizevar'])
    user_request.set_custom_attr("samplestoshow", req.form['samplestoshow'])
    user_request.set_custom_attr("corrvar1SpecificTaxonomies", req.form['corrvar1SpecificTaxonomies'])
    user_request.set_custom_attr("corrvar2SpecificTaxonomies", req.form['corrvar2SpecificTaxonomies'])
    user_request.set_custom_attr("sizevarSpecificTaxonomies", req.form['sizevarSpecificTaxonomies'])

    plugin = Correlations()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# ---


@app.route('/correlation_network', methods=['POST'])
@flask_login.login_required
def getCorrelationNetworkSecure():
    user_request = __get_user_request(request)
    return getCorrelationNetwork(user_request, request)


@app.route('/share/correlation_network', methods=['POST'])
def getCorrelationNetworkShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getCorrelationNetwork(user_request, request)
    else:
        abortNotShared()


def getCorrelationNetwork(user_request, req):
    user_request.set_custom_attr("type", req.form['type'])
    user_request.set_custom_attr("cutoff", req.form['cutoff'])

    plugin = CorrelationNetwork()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# ---


@app.route('/correlations_selection', methods=['POST'])
@flask_login.login_required
def getCorrelationsSelectionSecure():
    user_request = __get_user_request(request)
    return getCorrelationsSelection(user_request, request)


@app.route('/share/correlations_selection', methods=['POST'])
def getCorrelationsSelectionShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getCorrelationsSelection(user_request, request)
    else:
        abortNotShared()


def getCorrelationsSelection(user_request, req):
    user_request.set_custom_attr("select", req.form['select'])
    user_request.set_custom_attr("against", req.form['against'])
    user_request.set_custom_attr("expvar", req.form['expvar'])
    user_request.set_custom_attr("pvalthreshold", req.form['pvalthreshold'])

    plugin = CorrelationsSelection()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# ---


@app.route('/differential_selection', methods=['POST'])
@flask_login.login_required
def getDifferentialSelectionSecure():
    user_request = __get_user_request(request)
    return getDifferentialSelection(user_request, request)


@app.route('/share/differential_selection', methods=['POST'])
def getDifferentialSelectionShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getDifferentialSelection(user_request, request)
    else:
        abortNotShared()


def getDifferentialSelection(user_request, req):
    user_request.set_custom_attr("type", req.form['type'])
    user_request.set_custom_attr("pvalthreshold", req.form['pvalthreshold'])
    user_request.set_custom_attr("pwVar1", req.form['pwVar1'])
    user_request.set_custom_attr("pwVar2", req.form['pwVar2'])

    plugin = DifferentialSelection()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# ---


@app.route('/fisher_exact', methods=['POST'])
@flask_login.login_required
def getFisherExactSecure():
    user_request = __get_user_request(request)
    return getFisherExact(user_request, request)


@app.route('/share/fisher_exact', methods=['POST'])
def getFisherExactShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getFisherExact(user_request, request)
    else:
        abortNotShared()


def getFisherExact(user_request, req):
    user_request.set_custom_attr("minthreshold", req.form['minthreshold'])
    user_request.set_custom_attr("pwVar1", req.form['pwVar1'])
    user_request.set_custom_attr("pwVar2", req.form['pwVar2'])

    plugin = FisherExact()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# ---


@app.route('/glmnet', methods=['POST'])
@flask_login.login_required
def getGlmnetSecure():
    user_request = __get_user_request(request)
    return getGlmnet(user_request, request)


@app.route('/share/glmnet', methods=['POST'])
def getGlmnetShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getGlmnet(user_request, request)
    else:
        abortNotShared()


def getGlmnet(user_request, req):
    user_request.set_custom_attr("expvar", req.form['expvar'])
    user_request.set_custom_attr("alpha", req.form['alpha'])
    user_request.set_custom_attr("model", req.form['model'])
    user_request.set_custom_attr("lambdathreshold", req.form['lambdathreshold'])

    plugin = GLMNet()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# ---


@app.route('/heatmap', methods=['POST'])
@flask_login.login_required
def getHeatmapSecure():
    user_request = __get_user_request(request)
    return getHeatmap(user_request, request)


@app.route('/share/heatmap', methods=['POST'])
def getHeatmapShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getHeatmap(user_request, request)
    else:
        abortNotShared()


def getHeatmap(user_request, req):
    user_request.set_custom_attr("corrvar1", req.form['corrvar1'])
    user_request.set_custom_attr("corrvar2", req.form['corrvar2'])
    user_request.set_custom_attr("cluster", req.form['cluster'])
    user_request.set_custom_attr("minSamplesPresent", req.form['minSamplesPresent'])
    user_request.set_custom_attr("corrvar1Alpha", json.loads(req.form['corrvar1Alpha']))
    user_request.set_custom_attr("corrvar2Alpha", json.loads(req.form['corrvar2Alpha']))

    plugin = Heatmap()
    abundances = plugin.run(user_request)
    return base64.b64encode(zlib.compress(json.dumps(abundances).encode("utf-8")))


# ---


@app.route('/random_forest', methods=['POST'])
@flask_login.login_required
def getRandomForestSecure():
    user_request = __get_user_request(request)
    return getRandomForest(user_request, request)


@app.route('/share/random_forest', methods=['POST'])
def getRandomForestShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getRandomForest(user_request, request)
    else:
        abortNotShared()


def getRandomForest(user_request, req):
    user_request.set_custom_attr("numTrees", req.form['numTrees'])
    user_request.set_custom_attr("maxDepth", req.form['maxDepth'])

    plugin = RandomForest()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# ---


@app.route('/rarefaction', methods=['POST'])
@flask_login.login_required
def getRarefactionSecure():
    user_request = __get_user_request(request)
    return getRarefaction(user_request, request)


@app.route('/share/rarefaction', methods=['POST'])
def getRarefactionShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getRarefaction(user_request, request)
    else:
        abortNotShared()


def getRarefaction(user_request, req):
    plugin = RarefactionCurves()
    user_request.set_custom_attr("colorvar", req.form['colorvar'])
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# ---


@app.route('/nmds', methods=['POST'])
@flask_login.login_required
def getNMDSSecure():
    user_request = __get_user_request(request)
    return getNMDS(user_request, request)


@app.route('/share/nmds', methods=['POST'])
def getNMDSShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getNMDS(user_request, request)
    else:
        abortNotShared()


def getNMDS(user_request, req):
    user_request.set_custom_attr("type", req.form['type'])

    plugin = NMDS()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# ---


@app.route('/pca', methods=['POST'])
@flask_login.login_required
def getPCASecure():
    user_request = __get_user_request(request)
    return getPCA(user_request, request)


@app.route('/share/pca', methods=['POST'])
def getPCAShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getPCA(user_request, request)
    else:
        abortNotShared()


def getPCA(user_request, req):
    user_request.set_custom_attr("type", req.form['type'])
    user_request.set_custom_attr("pca1", req.form['pca1'])
    user_request.set_custom_attr("pca2", req.form['pca2'])
    user_request.set_custom_attr("pca3", req.form['pca3'])

    plugin = PCA()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# ---


@app.route('/table', methods=['POST'])
@flask_login.login_required
def getTableSecure():
    user_request = __get_user_request(request)
    return getTable(user_request)


@app.route('/share/table', methods=['POST'])
def getTableShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getTable(user_request)
    else:
        abortNotShared()

def getTable(user_request):
    plugin = TableView()
    abundances = plugin.run(user_request)
    return json.dumps(abundances)


# ---


@app.route('/tree', methods=['POST'])
@flask_login.login_required
def getTreeSecure():
    user_request = __get_user_request(request)
    return getTree(user_request, request)


@app.route('/share/tree', methods=['POST'])
def getTreeShare():
    if checkSharedValidity(request):
        uid = request.args.get('uid', '')
        user_request = __get_user_request(request, user=uid)
        return getTree(user_request, request)
    else:
        abortNotShared()

def getTree(user_request, req):
    user_request.set_custom_attr("taxonomy_display_level", req.form['taxonomy_display_level'])
    user_request.set_custom_attr("display_values", req.form['display_values'])
    user_request.set_custom_attr("exclude_unclassified", req.form['exclude_unclassified'])
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


@app.route('/quantile_metadata_info', methods=['GET'])
@flask_login.login_required
def get_quantile_metadata_info():
    user = current_user.id
    pid = request.args.get("pid")
    metadata_name = request.args.get("metadata_name")
    quantile_type = request.args.get("quantile_type") # gene or numeric
    if quantile_type == "gene":
        genes = Genes(user, pid)
        return_obj = {
            "context": genes.get_gene_info(metadata_name)
        }
    else:
        metadata = Metadata(user, pid)
        return_obj = {
            "context": metadata.get_numeric_metadata_info(metadata_name)
        }

    quantiles = Quantiles(user, pid)
    if quantiles.exists(metadata_name):
        return_obj["existing_quantile"] = quantiles.get_existing(metadata_name)
    return json.dumps(return_obj)


@app.route('/list_quantiles', methods=['POST'])
@flask_login.login_required
def list_quantiles():
    user = current_user.id
    pid = request.form['pid']
    sample_metadata = request.form['sample_metadata'] if 'sample_metadata' in request.form else ""

    quantiles = Quantiles(user, pid)
    if sample_metadata != "":
        return json.dumps(quantiles.quantiles)
    else:
        if sample_metadata in quantiles.quantiles:
            return json.dumps(quantiles.quantiles[sample_metadata])
        else:
            return json.dumps({})


@app.route('/save_quantile', methods=['POST'])
@flask_login.login_required
def save_quantile():
    user = current_user.id
    pid = request.form['pid']
    quantile_staging = json.loads(request.form['quantileStaging'])

    quantiles = Quantiles(user, pid)
    quantiles.update_quantile(quantile_staging["metadata_name"], quantile_staging["min"], quantile_staging["max"], quantile_staging["quantiles"], quantile_staging["type"], quantile_staging["quantile_type"])
    quantiles.save()
    return json.dumps({})


@app.route('/remove_quantile', methods=['POST'])
@flask_login.login_required
def remove_quantile():
    user = current_user.id
    pid = request.form['pid']
    sample_metadata = request.form['sample_metadata']

    quantiles = Quantiles(user, pid)
    quantiles.remove_quantile(sample_metadata)
    quantiles.save()
    return json.dumps({})


# ----- Data processing endpoints -----

def __get_user_request(request, user=None):
    if user is None:
        user = current_user.id

    pid = request.form['pid']
    taxonomyFilterCount = request.form['taxonomyFilterCount'] if 'taxonomyFilterCount' in request.form else ""
    taxonomyFilterPrevalnce = request.form['taxonomyFilterPrevalence'] if 'taxonomyFilterPrevalence' in request.form else ""
    taxonomyFilter = request.form['taxonomyFilter'] if 'taxonomyFilter' in request.form else ""
    taxonomyFilterRole = request.form['taxonomyFilterRole'] if 'taxonomyFilterRole' in request.form else ""
    taxonomyFilterVals = json.loads(request.form['taxonomyFilterVals']) if 'taxonomyFilterVals' in request.form else []
    sampleFilter = request.form['sampleFilter'] if 'sampleFilter' in request.form else ""
    sampleFilterRole = request.form['sampleFilterRole'] if 'sampleFilterRole' in request.form else ""
    sampleFilterVals = json.loads(request.form['sampleFilterVals']) if 'sampleFilterVals' in request.form else []
    catvar = request.form['catvar'] if 'catvar' in request.form else ""
    level = request.form['level'] if 'level' in request.form else -2
    user_request = UserRequest(user, pid, taxonomyFilterCount, taxonomyFilterPrevalnce, taxonomyFilter,
                               taxonomyFilterRole, taxonomyFilterVals, sampleFilter, sampleFilterRole,
                               sampleFilterVals, level, catvar)
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

@app.route('/loadExampleProject', methods=['POST'])
@flask_login.login_required
def loadExampleProject():
    if request.method == 'POST':
        project_dir = os.path.dirname(__file__)
        project_dir = os.path.join(project_dir, "data")
        user_dir = os.path.join(project_dir, current_user.id)
        user_dir = os.path.join(user_dir, "example")

        # Create the user dir if necessary
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)

        # Copy all files from the example directory to the user dir
        example_dir = os.path.join(project_dir, "example")

        for item in os.listdir(example_dir):
            s = os.path.join(example_dir, item)
            d = os.path.join(user_dir, item)
            shutil.copy2(s, d)

        return redirect(url_for('projects', status=OK, message="Example COPD Project Loaded"))

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

@app.route("/download")
@flask_login.login_required
def downloadFile():
    user = current_user.id
    currProject = request.args.get('pid', '')
    type = request.args.get('type', '')
    project_manager = ProjectManager(user)

    def generate_tsv():
        for row in project_manager.get_file_for_download(currProject, type):
            yield '\t'.join(row) + '\n'
    def generate_text():
        return project_manager.get_file_for_download(currProject, type)

    if type == "biom" or type == "phylogenetic":
        return Response(generate_text(),
                           mimetype="text/plain",
                           headers={"Content-Disposition":
                                        "attachment;filename=" + type + ".txt"})
    else:
        return Response(generate_tsv(),
                           mimetype="text/tab-separated-values",
                           headers={"Content-Disposition":
                                        "attachment;filename=" + type + ".txt"})


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


def checkUserExists(email):
    """
    Checks if the user exists
    """
    db = sqlite3.connect(DB_PATH)
    c = db.cursor()
    t = (email,)
    c.execute('SELECT id, user_email FROM accounts WHERE user_email=?', t)
    row = c.fetchone()
    if row is None:
        return False
    db.close()
    return True


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


def sendResetPasswordLink(email):
    """
    Resets the user password if they possess the correct secret
    """
    db = sqlite3.connect(DB_PATH)
    c = db.cursor()
    t = (email,)
    c.execute('SELECT id FROM accounts WHERE user_email=?', t)
    row = c.fetchone()
    db.close()

    if row is None:
        # This account doesn't actually exist
        return False
    else:
        id = row[0]
        secret = str(uuid.uuid4())
        expiry = int(time.time()) + 60 * 24

        db = sqlite3.connect(DB_PATH)
        c = db.cursor()
        c.execute('DELETE FROM reset WHERE id = ?', (id,))
        db.commit()
        c.execute('INSERT INTO reset (id, secret, expiry) VALUES (?,?,?)', (id, secret, expiry))
        db.commit()
        db.close()

        logger.info("Generated a reset link: https://miandata.org/reset_password?id=" + str(id) + "&secret=" + secret)

        if not app.debug:
            msg = Message("Reset Password on Mian",
                          sender="no-reply@miandata.org",
                          recipients=[email])
            msg.body = "Reset your password here: https://miandata.org/reset_password?id=" + str(id) + "&secret=" + secret
            mail.send(msg)

        return True


def resetPassword(user, secret, new_password):
    """
    Resets the user password if they possess the correct secret
    """
    db = sqlite3.connect(DB_PATH)
    c = db.cursor()
    t = (user,)
    c.execute('SELECT secret, expiry FROM reset WHERE id=?', t)
    row = c.fetchone()
    db.close()

    if row is None:
        # Cannot reset because no reset request was sent
        return False
    else:
        actual_secret = row[0]
        actual_expiry = row[1]

        curr_time = int(time.time())
        if curr_time > actual_expiry:
            return False

        if secret != actual_secret:
            return False

        db = sqlite3.connect(DB_PATH)
        c = db.cursor()
        salt = createSalt()

        calculatedPassword = hashlib.md5(str(salt + new_password).encode('utf-8')).hexdigest()
        c.execute('UPDATE accounts SET password_hash = ?, salt = ? WHERE id = ?',
                  (calculatedPassword, salt, user))
        db.commit()
        db.close()

        return True


def changePassword(id, original_password, new_password):
    """
    Changes the user password
    """
    db = sqlite3.connect(DB_PATH)
    c = db.cursor()
    t = (id,)
    c.execute('SELECT password_hash, salt FROM accounts WHERE id=?', t)
    row = c.fetchone()
    db.close()

    if row is None:
        logger.info("No user exists when attempting to change password for id " + str(id))
        return False
    else:
        knownPassword = row[0]
        salt = row[1]
        calculatedPassword = hashlib.md5(str(salt + original_password).encode('utf-8')).hexdigest()
        if calculatedPassword != knownPassword:
            logger.info("User id " + str(id) + " password change had the wrong old password")
            return False

    db = sqlite3.connect(DB_PATH)
    c = db.cursor()
    salt = createSalt()

    calculatedPassword = hashlib.md5(str(salt + new_password).encode('utf-8')).hexdigest()
    c.execute('UPDATE accounts SET password_hash = ?, salt = ? WHERE id = ?',
              (calculatedPassword, salt, id))
    db.commit()
    db.close()

    return True


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
                quantiles = Quantiles(user_id, pid)
                num_gene_quantiles = 0
                num_metadata_quantiles = 0
                for quantile_name, q in quantiles.quantiles.items():
                    if q["quantile_type"] == "gene":
                        num_gene_quantiles += 1
                    else:
                        num_metadata_quantiles += 1
                project_map = Map(user_id, pid)
                if project_map.orig_biom_name != "":
                    project_type = "biom"
                    project_info = {
                        "project_name": project_map.project_name,
                        "pid": pid,
                        "project_type": project_type,
                        "orig_biom_name": project_map.orig_biom_name,
                        "orig_sample_metadata_name": project_map.orig_sample_metadata_name,
                        "orig_gene_name": project_map.orig_gene_name,
                        "orig_phylogenetic_name": project_map.orig_phylogenetic_name,
                        "subsampled_value": project_map.subsampled_value,
                        "subsampled_type": project_map.subsampled_type,
                        "subsampled_removed_samples": project_map.subsampled_removed_samples,
                        "matrix_type": project_map.matrix_type,
                        "num_samples": project_map.num_samples,
                        "num_otus": project_map.num_otus,
                        "shared": project_map.shared,
                        "num_gene_quantiles": num_gene_quantiles,
                        "num_metadata_quantiles": num_metadata_quantiles
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
                        "orig_gene_name": project_map.orig_gene_name,
                        "orig_phylogenetic_name": project_map.orig_phylogenetic_name,
                        "subsampled_value": project_map.subsampled_value,
                        "subsampled_type": project_map.subsampled_type,
                        "subsampled_removed_samples": project_map.subsampled_removed_samples,
                        "matrix_type": project_map.matrix_type,
                        "num_samples": project_map.num_samples,
                        "num_otus": project_map.num_otus,
                        "shared": project_map.shared,
                        "num_gene_quantiles": num_gene_quantiles,
                        "num_metadata_quantiles": num_metadata_quantiles
                    }
                logger.info("Read project info " + str(project_info))
                if project_map.project_name != "" and project_map.subsampled_type != "":
                    # Note: Projects that are half uploaded will not have a subsampled type
                    project_name_to_info[project_map.pid] = project_info
    return project_name_to_info


def checkSharedValidity(req):
    uid = req.args.get('uid', '')
    pid = req.args.get('pid', '')
    if uid == "" or pid == "":
        return False

    project_names_to_info = get_project_ids_to_info(uid)
    if pid not in project_names_to_info:
        return False

    return project_names_to_info[pid]["shared"] == "yes"

def abortNotShared():
    abort(403)
    abort(Response('This project is not publicly accessible'))

