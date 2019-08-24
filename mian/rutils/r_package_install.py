from rpy2.rinterface import RRuntimeError
from rpy2.robjects.packages import importr
from rpy2.robjects.vectors import StrVector
utils = importr('utils')


def importr_custom(package_name, version=None):
    try:
        importr(package_name)
        print(package_name + ' is already installed')
    except RRuntimeError:
        utils.chooseCRANmirror(ind=1)
        if version is not None:
            versions_vec = StrVector((version,))
            package_name_vec = StrVector((package_name,))
            utils.install_packages(package_name_vec, versions=versions_vec)
        else:
            utils.install_packages(package_name)
        importr(package_name)
        print(package_name + ' has been installed')
