import os
import csv
from scipy import stats
import analysis
import numpy as np
import time

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
library(vegan)

alphaDiversity <- function(allOTUs, alphaType, alphaContext) {
	alphaDiv = diversity(allOTUs, index = alphaType)
	if (alphaContext == "evenness") {
		S <- specnumber(allOTUs)
		J <- alphaDiv/log(S)
		return(J)
	} else if (alphaContext == "speciesnumber") {
		S <- specnumber(allOTUs)
		return(S)
	} else {
		return(alphaDiv)
	}
}

betaDiversity <- function(allOTUs, groups, method) {
	abc <- betadiver(allOTUs, method=method)
	Habc = abc
	if (method == "sor") {
		Habc = 1 - abc
	}

	mod <- betadisper(Habc, groups)
	distances = mod$distances
	return(distances)
}

betaDiversityPERMANOVA <- function(allOTUs, groups) {
	return(adonis(allOTUs~groups))
}

betaDiversityDisper <- function(allOTUs, groups, method) {
	abc <- betadiver(allOTUs, method=method)
	Habc = abc
	if (method == "sor") {
		Habc = 1 - abc
	}

	# TODO: Use bias adjust?
	mod <- betadisper(Habc, groups)
	return(anova(mod))
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

def getOTUTableAtLevel(base, taxonomyMap, itemsOfInterest, level):
	otus = {}
	for otu, classification in taxonomyMap.iteritems():
		if int(level) >= 0 and int(level) < len(classification):
			if classification[int(level)] in itemsOfInterest:
				otus[otu] = 1
		else:
			if otu in itemsOfInterest:
				otus[otu] = 1

	newOTUTable = []
	relevantCols = {}
	relevantCols[0] = 1

	i = 0
	while i < len(base):
		if i == 0:
			# Header row
			# Ignores the first column (sample ID)
			newRow = [base[i][0]]
			j = 1
			while j < len(base[i]):
				if base[i][j] in otus:
					newRow.append(base[i][j])
					relevantCols[j] = 1
				j += 1
			newOTUTable.append(newRow)
		else:
			newRow = []
			j = 0
			while j < len(base[i]):
				if j in relevantCols:
					newRow.append(base[i][j])
				j += 1
			newOTUTable.append(newRow)
		i += 1
	return newOTUTable

def getCatCol(otuMetadata, catvar):
	catCol = 1
	j = 0
	while j < len(otuMetadata[0]):
		if otuMetadata[0][j] == catvar:
			catCol = j
		j += 1
	return catCol


def alphaDiversity(userID, projectID, level, itemsOfInterest, catvar, alphaType, alphaContext):
	if itemsOfInterest is None or itemsOfInterest == "":
		return []
		
	otuTable = analysis.csvToTable(userID, projectID, "otuTable.csv")
	otuMetadata = analysis.csvToTable(userID, projectID, "otuMetadata.csv")
	taxonomyMap = analysis.getTaxonomyMapping(userID, projectID)

	metaVals = getMetadataInOTUTableOrder(otuTable, otuMetadata, getCatCol(otuMetadata, catvar))

	otuTable = getOTUTableAtLevel(otuTable, taxonomyMap, itemsOfInterest, level)


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

	vals = veganR.alphaDiversity(dataf, alphaType, alphaContext);

	# Calculate the statistical p-value
	abundances = {}
	statsAbundances = {}
	i = 0
	while i < len(vals):
		obj = {}
		obj["s"] = str(otuTable[i][0])
		obj["a"] = vals[i]

		meta = metaVals[i]
		if meta in statsAbundances:
			statsAbundances[meta].append(vals[i])
			abundances[meta].append(obj)
		else:
			statsAbundances[meta] = [vals[i]]
			abundances[meta] = [obj]

		i += 1
	statistics = analysis.getTtest(statsAbundances)

	abundancesObj = {}
	abundancesObj["abundances"] = abundances
	abundancesObj["stats"] = statistics
	return abundancesObj


def betaDiversity(userID, projectID, level, itemsOfInterest, catvar, betaType):
	if itemsOfInterest is None or itemsOfInterest == "":
		return []

	otuTable = analysis.csvToTable(userID, projectID, "otuTable.csv")
	otuMetadata = analysis.csvToTable(userID, projectID, "otuMetadata.csv")
	taxonomyMap = analysis.getTaxonomyMapping(userID, projectID)

	metaVals = getMetadataInOTUTableOrder(otuTable, otuMetadata, getCatCol(otuMetadata, catvar))
	groups = robjects.FactorVector(robjects.StrVector(metaVals))

	otuTable = getOTUTableAtLevel(otuTable, taxonomyMap, itemsOfInterest, level)

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

	# See: http://stackoverflow.com/questions/35410860/permanova-multivariate-spread-among-groups-is-not-similar-to-variance-homogeneit
	vals = veganR.betaDiversity(dataf, groups, betaType)

	# Calculate the statistical p-value
	abundances = {}
	statsAbundances = {}
	i = 0
	while i < len(vals):
		obj = {}
		obj["s"] = str(otuTable[i][0])
		obj["a"] = vals[i]

		if metaVals[i] in statsAbundances:
			statsAbundances[metaVals[i]].append(vals[i])
			abundances[metaVals[i]].append(obj)
		else:
			statsAbundances[metaVals[i]] = [vals[i]]
			abundances[metaVals[i]] = [obj]

		i += 1
		
	statistics = analysis.getTtest(statsAbundances)

	abundancesObj = {}
	abundancesObj["abundances"] = abundances
	abundancesObj["stats"] = statistics

	permanova = veganR.betaDiversityPERMANOVA(dataf, groups)
	dispersions = veganR.betaDiversityDisper(dataf, groups, betaType)
	abundancesObj["permanova"] = str(permanova)
	abundancesObj["dispersions"] = str(dispersions)

	return abundancesObj