import os
import csv
from scipy import stats
import analysis
import numpy as np

# 
# ======== R specific setup =========
# 

from rpy2.robjects.packages import importr
import rpy2.robjects as robjects
import rpy2.rlike.container as rlc
from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage

r = robjects.r

# 
# ======== Main code begins =========
# 

rcode = """
pca <- function(allOTUs) {
	# Removes any columns that only contain 0s
	allOTUs <- allOTUs[, colSums(allOTUs) > 0]
	pca <- prcomp(allOTUs, center = TRUE, scale. = TRUE)
	return(pca$x)
}

pca_variance <- function(allOTUs) {
	# Removes any columns that only contain 0s
	allOTUs <- allOTUs[, colSums(allOTUs) > 0]
	pca <- prcomp(allOTUs, center = TRUE, scale. = TRUE)
	proportions = 100*(pca[["sdev"]]^2)/sum(pca[["sdev"]]^2)
	return(proportions[1:min(length(proportions), 10)])
}
"""

rViz = SignatureTranslatedAnonymousPackage(rcode, "rViz")

def pca(userID, projectID, level, itemsOfInterest, catvar, pca1, pca2):
	otuTable = analysis.csvToTable(userID, projectID, "otuTable.csv")
	otuMetadata = analysis.csvToTable(userID, projectID, "otuMetadata.csv")
	metaVals = analysis.getMetadataInOTUTableOrder(otuTable, otuMetadata, analysis.getCatCol(otuMetadata, catvar))
	
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
	pcaVals = rViz.pca(dataf)
	pcaVariances = rViz.pca_variance(dataf)

	pca1Min = 100
	pca2Min = 100
	pca1Max = 0
	pca2Max = 0

	pcaRow = []
	i = 1 # RObjects use 1 based indexing
	while i <= pcaVals.nrow:
		meta = metaVals[i - 1]
		pcaObj = {}
		pcaObj["m"] = meta
		pcaObj["pca1"] = float(pcaVals.rx(i, int(pca1))[0])
		pcaObj["pca2"] = float(pcaVals.rx(i, int(pca2))[0])
		if pcaObj["pca1"] > pca1Max:
			pca1Max = pcaObj["pca1"]
		if pcaObj["pca1"] < pca1Min:
			pca1Min = pcaObj["pca1"]

		if pcaObj["pca2"] > pca2Max:
			pca2Max = pcaObj["pca2"]
		if pcaObj["pca2"] < pca2Min:
			pca2Min = pcaObj["pca2"]

		pcaRow.append(pcaObj)
		i += 1

	pcaVarRow = []
	for p in pcaVariances:
		pcaVarRow.append(float(p))

	# TODO: Check
	abundancesObj = {}
	abundancesObj["pca"] = pcaRow
	abundancesObj["pcaVar"] = pcaVarRow
	abundancesObj["pca1Max"] = pca1Max
	abundancesObj["pca1Min"] = pca1Min
	abundancesObj["pca2Max"] = pca2Max
	abundancesObj["pca2Min"] = pca2Min
	return abundancesObj

# pca("1", "Test", 0, ["Bacteria"], "Disease", 1, 3)
