from sqlite3 import dbapi2 as sqlite3
from rpy2.rinterface import RRuntimeError
from rpy2.robjects.packages import importr
utils = importr('utils')


#
# Initialization including database creation of the project
#

def init_db():
    connection = sqlite3.connect("mian.db")
    cur = connection.cursor()
    with open('schema.sql', mode='r') as f:
        cur.executescript(f.read())
    connection.commit()

def importr_custom(package_name):
    try:
        r_package = importr(package_name)
    except RRuntimeError:
        utils.install_packages(package_name, "http://cran.stat.sfu.ca/")
        r_package = importr(package_name)
    return r_package

init_db()
print('Initialized the database.')

importr_custom("vegan")
importr_custom("RColorBrewer")
importr_custom("ranger")
importr_custom("Boruta")
importr_custom("glmnet")

print('Installed/Loaded R Packages')
