import os
import csv
from scipy import stats
import analysis
import numpy as np

# 
# ======== R specific setup =========
# 
# R package names
packnames = ('ggplot2', 'vegan')

# import rpy2's package module
import rpy2.robjects.packages as rpackages

if all(rpackages.isinstalled(x) for x in packnames):
    have_tutorial_packages = True
else:
    have_tutorial_packages = False

if not have_tutorial_packages:
    # import R's utility package
    utils = rpackages.importr('utils')
    # select a mirror for R packages
    utils.chooseCRANmirror(ind=1) # select the first mirror in the list
    # R vector of strings
    from rpy2.robjects.vectors import StrVector
    # file
    packnames_to_install = [x for x in packnames if not rpackages.isinstalled(x)]
    if len(packnames_to_install) > 0:
        utils.install_packages(StrVector(packnames_to_install))

# 
# ======== Main code begins =========
# 

from rpy2.robjects.packages import importr
import rpy2.robjects as robjects
import rpy2.rlike.container as rlc
r = robjects.r

from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage

rcode = """
library(vegan)

betaDiversity <- function(allOTUs, groups) {
	abc <- betadiver(allOTUs, method=NA)
	Habc = 2*abc$a / (2*abc$a + abc$b + abc$c)
	Habc = 1 - Habc

	mod <- betadisper(Habc, groups, bias.adjust=TRUE)
	distances = mod$distances
	return(distances)
}
"""

veganR = SignatureTranslatedAnonymousPackage(rcode, "veganR")

def mapIDToMetadata(otuMetadata, metaCol):
	metaVals = {}
	i = 1
	while i < len(otuMetadata):
		# Maps the ID column to metadata column
		metaVals[otuMetadata[i][0]] = otuMetadata[i][metaCol]
		i += 1
	return metaVals

def getMetadataInOTUTableOrder(otuTable, otuMetadata, metaCol):
	metadataMap = mapIDToMetadata(otuMetadata, metaCol)
	metaVals = []
	row = 1
	while row < len(otuTable):
		metaVals.append(metadataMap[otuTable[row][0]])
		row += 1
	return metaVals

def alphaDiversity():
	otuTable = analysis.csvToTable("1", "Test", "otuTable.csv")
	otuMetadata = analysis.csvToTable("1", "Test", "otuMetadata.csv")

	# TODO: Needs to be mapped properly to IDs
	metaVals = getMetadataInOTUTableOrder(otuTable, otuMetadata, 1)
	groups = robjects.FactorVector(robjects.StrVector(metaVals))

	# Forms an OTU only table (without IDs)
	allOTUs = [];
	col = 1
	while col < len(otuTable[0]):
		colVals = []
		row = 1
		while row < len(otuTable):
			colVals.append(otuTable[row][col])
			row += 1
		allOTUs.append((otuTable[0][col], robjects.FloatVector(colVals)))
		col += 1

	od = rlc.OrdDict(allOTUs)
	dataf = robjects.DataFrame(od)

	print veganR.betaDiversity(dataf, groups);

alphaDiversity()