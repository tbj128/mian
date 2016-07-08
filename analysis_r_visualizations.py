# ===========================================
# 
# mian Analysis R-based Visualizations
# @author: tbj128
# 
# ===========================================

# 
# Imports
# 

import os
import csv
from scipy import stats
import analysis
import numpy as np
import math

# 
# ======== R specific setup =========
# 

from rpy2.robjects.packages import importr
import rpy2.robjects as robjects
import rpy2.rlike.container as rlc
from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage

# utils = importr('utils')
# utils.install_packages('RColorBrewer')

rprint = robjects.globalenv.get("print")
grdevices = importr('grDevices')
base = importr('base')
lattice = importr('lattice')
vegan = importr('vegan')

r = robjects.r

# 
# ======== Main code begins =========
# 

rcode = """
library("RColorBrewer")

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

get_colors <- function(groups) {
	cols <- brewer.pal(length(unique(groups)),"Set1")
	names(cols) = levels(groups)
	colors = c()
	for (g in groups) {
		colors = c(colors, cols[g])
	}
	return(colors) 
}

plot_NMDS <- function(example_NMDS, groups, colors) {
	cols <- brewer.pal(length(unique(groups)),"Set1")
	names(cols) = levels(groups)
	# ordiplot(example_NMDS,type="points",display="species")
	ordiplot(example_NMDS,type="n")
 	legend("topright",legend=unique(groups), cex=.8, col=cols, pch=15, lty=0)
	for(i in unique(groups)) {
		# orditorp(example_NMDS,display="species",pch=".",col="red",air=0.01)
		orditorp(example_NMDS$point[grep(i,groups),],display="sites",col=colors[grep(i,groups)],air=0.01)
	  	ordihull(example_NMDS$point[grep(i,groups),],draw="polygon", groups=groups[groups==i],col=colors[grep(i,groups)],label=F) 
	}
}

"""

rViz = SignatureTranslatedAnonymousPackage(rcode, "rViz")

def correlations(userID, projectID, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, corrvar1, corrvar2, colorvar, sizevar, samplestoshow):
	otuTable = analysis.csvToTable(userID, projectID, analysis.OTU_TABLE_NAME)
	otuMetadata = analysis.csvToTable(userID, projectID, analysis.METADATA_NAME)
	taxonomyMap = analysis.getTaxonomyMapping(userID, projectID)

	otuTable = analysis.filterOTUTableByMetadata(otuTable, otuMetadata, sampleFilter, sampleFilterVals)
	otuTable = analysis.getOTUTableAtLevel(otuTable, taxonomyMap, taxonomyFilterVals, taxonomyFilter)

	relevantOTUs = analysis.getRelevantOTUs(taxonomyMap, taxonomyFilter, taxonomyFilterVals)
	relevantCols = analysis.getRelevantCols(otuTable, relevantOTUs)

	sampleIDToMetadataRow = {}
	i = 1
	while i < len(otuMetadata):
		sampleID = otuMetadata[i][0]
		sampleIDToMetadataRow[sampleID] = i
		i += 1

	corrcol1 = -1
	if corrvar1 != "Abundances":
		corrcol1 = analysis.getCatCol(otuMetadata, corrvar1)

	corrcol2 = -1
	if corrvar2 != "Abundances":
		corrcol2 = analysis.getCatCol(otuMetadata, corrvar2)

	colorcol = -1
	if colorvar != "":
		colorcol = analysis.getCatCol(otuMetadata, colorvar)

	sizecol = -1
	if sizevar != "":
		sizecol = analysis.getCatCol(otuMetadata, sizevar)

	corrArr = []
	corrValArr1 = []
	corrValArr2 = []

	i = 1
	while i < len(otuTable):
		totalAbundance = 0
		j = analysis.OTU_START_COL
		while j < len(otuTable[i]):
			if j in relevantCols:
				totalAbundance += float(otuTable[i][j])
			j += 1

		if (samplestoshow == "nonzero" and totalAbundance > 0) or (samplestoshow == "zero" and totalAbundance == 0) or samplestoshow == "both":
			corrObj = {}
			sampleID = otuTable[i][analysis.OTU_GROUP_ID_COL]
			if sampleID in sampleIDToMetadataRow:
				metadataRow = sampleIDToMetadataRow[sampleID]

				corrVal1 = 0
				if corrvar1 == "Abundances":
					corrVal1 = totalAbundance
				else:
					corrVal1 = otuMetadata[metadataRow][corrcol1]

				corrVal2 = 0
				if corrvar2 == "Abundances":
					corrVal2 = totalAbundance
				else:
					corrVal2 = otuMetadata[metadataRow][corrcol2]

				corrObj["s"] = sampleID
				corrObj["c1"] = float(corrVal1)
				corrObj["c2"] = float(corrVal2)
				corrValArr1.append(float(corrVal1))
				corrValArr2.append(float(corrVal2))

				if colorcol > -1:
					colorVal = otuMetadata[metadataRow][colorcol]
					corrObj["color"] = colorVal
				else:
					corrObj["color"] = ""

				if sizecol > -1:
					sizeVal = otuMetadata[metadataRow][sizecol]
					corrObj["size"] = sizeVal
				else:
					corrObj["size"] = 0

				corrArr.append(corrObj)

		i += 1

	coef, pval = stats.pearsonr(corrValArr1, corrValArr2)
	if math.isnan(coef): 
		coef = 0
	if math.isnan(pval): 
		coef = 1

	abundancesObj = {}
	abundancesObj["corrArr"] = corrArr
	abundancesObj["coef"] = coef
	abundancesObj["pval"] = pval
	return abundancesObj

def pca(userID, projectID, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, level, catvar, pca1, pca2):
	otuTable = analysis.csvToTable(userID, projectID, analysis.OTU_TABLE_NAME)
	otuMetadata = analysis.csvToTable(userID, projectID, analysis.METADATA_NAME)
	taxonomyMap = analysis.getTaxonomyMapping(userID, projectID)

	otuTable = analysis.filterOTUTableByMetadata(otuTable, otuMetadata, sampleFilter, sampleFilterVals)
	otuTable = analysis.getOTUTableAtLevel(otuTable, taxonomyMap, taxonomyFilterVals, taxonomyFilter)
	otuTable = analysis.getOTUTableAtLevelIntegrated(otuTable, taxonomyMap, "All", level)

	metaVals = analysis.getMetadataInOTUTableOrder(otuTable, otuMetadata, analysis.getCatCol(otuMetadata, catvar))
	metaIDs = analysis.mapIDToMetadata(otuMetadata, 1)

	# Forms an OTU only table (without IDs)
	allOTUs = [];
	col = analysis.OTU_START_COL
	while col < len(otuTable[0]):
		colVals = []
		row = 1
		while row < len(otuTable):
			sampleID = otuTable[row][analysis.OTU_GROUP_ID_COL]
			if sampleID in metaIDs:
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


def nmds(userID, projectID, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, level, catvar):
	otuTable = analysis.csvToTable(userID, projectID, analysis.OTU_TABLE_NAME)
	otuMetadata = analysis.csvToTable(userID, projectID, analysis.METADATA_NAME)
	taxonomyMap = analysis.getTaxonomyMapping(userID, projectID)
	
	otuTable = analysis.filterOTUTableByMetadata(otuTable, otuMetadata, sampleFilter, sampleFilterVals)
	otuTable = analysis.getOTUTableAtLevel(otuTable, taxonomyMap, taxonomyFilterVals, taxonomyFilter)
	otuTable = analysis.getOTUTableAtLevelIntegrated(otuTable, taxonomyMap, "All", level)

	metaVals = analysis.getMetadataInOTUTableOrder(otuTable, otuMetadata, analysis.getCatCol(otuMetadata, catvar))
	groups = robjects.FactorVector(robjects.StrVector(metaVals))
	metaIDs = analysis.mapIDToMetadata(otuMetadata, 1)

	# Forms an OTU only table (without IDs)
	allOTUs = [];
	col = analysis.OTU_START_COL
	while col < len(otuTable[0]):
		colVals = []
		row = 1
		while row < len(otuTable):
			sampleID = otuTable[row][analysis.OTU_GROUP_ID_COL]
			if sampleID in metaIDs:
				colVals.append(otuTable[row][col])
			row += 1
		allOTUs.append((otuTable[0][col], robjects.FloatVector(colVals)))
		col += 1

	od = rlc.OrdDict(allOTUs)
	dataf = robjects.DataFrame(od)
	example_NMDS = vegan.metaMDS(dataf, k=2) # The number of reduced dimensions

	# print example_NMDS$points
	# print example_NMDS$species

	colors = rViz.get_colors(groups)

	dir = os.path.dirname(__file__)
	dir = os.path.join(dir, "static")
	dir = os.path.join(dir, "tmp")
	dir = os.path.join(dir, userID)
	dir = os.path.join(dir, projectID)

	if not os.path.exists(dir):
	    os.makedirs(dir)

	fn = os.path.join(dir, "nmds.png")

	grdevices.png(file=fn, width=640, height=640)
	rViz.plot_NMDS(example_NMDS, groups, colors)
	grdevices.dev_off()

	abundancesObj = {}
	abundancesObj["fn"] = "static/tmp/" + str(userID) + "/" + str(projectID) + "/nmds.png"
	return abundancesObj


# pca("1", "Test", 0, ["Bacteria"], "Disease", 1, 3)
# nmds("1", "Test", 0, ["Bacteria"], "Disease", 1, 3)