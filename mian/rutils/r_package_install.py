from rpy2.rinterface_lib.embedded import RRuntimeError
from rpy2.robjects.packages import importr
import rpy2.robjects as robj
utils = importr('utils')


def importr_custom(package_name, version=None, is_bioconductor=False):
    try:
        importr(package_name)
        print(package_name + ' is already installed')
    except RRuntimeError:
        utils.chooseCRANmirror(ind=1)
        if is_bioconductor:
            robj.r('install.packages("BiocManager", repos="http://cran.r-project.org")')
            robj.r('BiocManager::install("' + package_name + '", dependencies=TRUE)')
        elif version is not None:
            archive_url = "https://cran.r-project.org/src/contrib/Archive/" + package_name + "/" + package_name + "_" + version + ".tar.gz"
            print("Trying to install from " + archive_url)
            utils.install_packages(archive_url, repos=robj.NULL, method="libcurl")
        else:
            utils.install_packages(package_name)
        importr(package_name)
        print(package_name + ' has been installed')
