# ===========================================
# 
# mian Analysis Alpha/Beta Diversity Library
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
	if (method == "bray") {
		Habc = vegdist(allOTUs, method=method)

		mod <- betadisper(Habc, groups)
		distances = mod$distances
		return(distances)
	} else {
		abc <- betadiver(allOTUs, method=method)
		Habc = abc
		if (method == "sor") {
			Habc = 1 - abc
		}

		mod <- betadisper(Habc, groups)
		distances = mod$distances
		return(distances)
	}

	mod <- betadisper(Habc, groups)
	distances = mod$distances
	return(distances)
}

betaDiversityPERMANOVA <- function(allOTUs, groups, strata) {
	return(adonis(allOTUs~groups, strata=strata))
}

betaDiversityPERMANOVA2 <- function(allOTUs, groups) {
	return(adonis(allOTUs~groups))
}

betaDiversityDisper <- function(allOTUs, groups, method) {
	if (method == "bray") {
		Habc = vegdist(allOTUs, method=method)
		
		# TODO: Use bias adjust?
		mod <- betadisper(Habc, groups)
		return(anova(mod))
	} else {
		abc <- betadiver(allOTUs, method=method)
		Habc = abc
		if (method == "sor") {
			Habc = 1 - abc
		}

		# TODO: Use bias adjust?
		mod <- betadisper(Habc, groups)
		return(anova(mod))
	}
}

"""

veganR = SignatureTranslatedAnonymousPackage(rcode, "veganR")

def alphaDiversity(userID, projectID, level, itemsOfInterest, catvar, alphaType, alphaContext):
	if itemsOfInterest is None or itemsOfInterest == "":
		return []
		
	otuTable = analysis.csvToTable(userID, projectID, analysis.OTU_TABLE_NAME)
	otuMetadata = analysis.csvToTable(userID, projectID, analysis.METADATA_NAME)
	taxonomyMap = analysis.getTaxonomyMapping(userID, projectID)

	metaVals = analysis.getMetadataInOTUTableOrder(otuTable, otuMetadata, analysis.getCatCol(otuMetadata, catvar))
	metaIDs = analysis.mapIDToMetadata(otuMetadata, 1)

	otuTable = analysis.getOTUTableAtLevel(otuTable, taxonomyMap, itemsOfInterest, level)


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

	vals = veganR.alphaDiversity(dataf, alphaType, alphaContext);

	# Calculate the statistical p-value
	abundances = {}
	statsAbundances = {}
	i = 0
	while i < len(vals):
		obj = {}
		obj["s"] = str(otuTable[i][analysis.OTU_GROUP_ID_COL])
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

	otuTable = analysis.csvToTable(userID, projectID, analysis.OTU_TABLE_NAME)
	otuMetadata = analysis.csvToTable(userID, projectID, analysis.METADATA_NAME)
	taxonomyMap = analysis.getTaxonomyMapping(userID, projectID)

	metaVals = analysis.getMetadataInOTUTableOrder(otuTable, otuMetadata, analysis.getCatCol(otuMetadata, catvar))
	metaIDs = analysis.mapIDToMetadata(otuMetadata, 1)
	groups = robjects.FactorVector(robjects.StrVector(metaVals))

	# =====================================================================
	# TODO: FIX
	# 
	metaVals2 = analysis.getMetadataInOTUTableOrder(otuTable, otuMetadata, analysis.getCatCol(otuMetadata, "Individual"))
	
	strata = robjects.FactorVector(robjects.StrVector(metaVals2))
	# 
	# TODO: FIX
	# =====================================================================


	otuTable = analysis.getOTUTableAtLevel(otuTable, taxonomyMap, itemsOfInterest, level)

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

	# See: http://stackoverflow.com/questions/35410860/permanova-multivariate-spread-among-groups-is-not-similar-to-variance-homogeneit
	vals = veganR.betaDiversity(dataf, groups, betaType)
	
	# Calculate the statistical p-value
	abundances = {}
	statsAbundances = {}
	i = 0
	while i < len(vals):
		obj = {}
		obj["s"] = str(otuTable[i][analysis.OTU_GROUP_ID_COL])
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

	# permanova = veganR.betaDiversityPERMANOVA(dataf, groups, strata)
	permanova = veganR.betaDiversityPERMANOVA2(dataf, groups)
	# print strata
	# print permanova
	# print permanova2
	dispersions = veganR.betaDiversityDisper(dataf, groups, betaType)
	abundancesObj["permanova"] = str(permanova)
	abundancesObj["dispersions"] = str(dispersions)

	return abundancesObj