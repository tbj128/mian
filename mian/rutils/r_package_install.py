from rpy2.rinterface import RRuntimeError
from rpy2.robjects.packages import importr
utils = importr('utils')


def importr_custom(package_name, version=None):
    try:
        r_package = importr(package_name)
        print(package_name + ' is already installed')
    except RRuntimeError:
        utils.chooseCRANmirror(ind=1)
        if version is not None:
            utils.install_packages(package_name, version=version)
        else:
            utils.install_packages(package_name)
        print(package_name + ' has been installed')
