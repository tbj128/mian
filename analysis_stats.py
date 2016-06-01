# ===========================================
# 
# mian Analysis Data Mining/ML Library
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
fisher_exact <- function(base, groups, minthreshold, keepthreshold) {

	cat1 = levels(groups)[1]
	cat2 = levels(groups)[2]

	base = base[,colSums(base!=0)>keepthreshold, drop=FALSE]

	if (ncol(base) <= 0) {
		return(matrix(,0,7))
	}

	cat1OTUs = base[groups == cat1,, drop=FALSE];
	cat2OTUs = base[groups == cat2,, drop=FALSE];

	results = matrix(,ncol(cat1OTUs),7)
	results = data.frame(results)
	colnames(results) = c("P-Value", "Q-Value", "Cat1 Present", "Cat1 Total", "Cat2 Present", "Cat2 Total")
	rownames(results) = colnames(cat1OTUs)

	for (i in 1:ncol(cat1OTUs)) {
		fisherMatrix = matrix(,2,2);
		fisherMatrix[1, 1] = sum(cat2OTUs[,i] > minthreshold);
		fisherMatrix[1, 2] = sum(cat2OTUs[,i] <= minthreshold);
		fisherMatrix[2, 1] = sum(cat1OTUs[,i] > minthreshold);
		fisherMatrix[2, 2] = sum(cat1OTUs[,i] <= minthreshold);
		totalSumCat1 = fisherMatrix[2, 1] + fisherMatrix[2, 2]
		totalSumCat2 = fisherMatrix[1, 1] + fisherMatrix[1, 2]
		
		ftest = fisher.test(fisherMatrix);

		results[i,1] = colnames(cat1OTUs)[i]
		results[i,2] = ftest$p.value
		results[i,3] = 1
		results[i,4] = fisherMatrix[2, 1]
		results[i,5] = totalSumCat1
		results[i,6] = fisherMatrix[1, 1]
		results[i,7] = totalSumCat2
	}

	results[,3] = p.adjust(results[,2], method = "fdr");

	# Sorts the table according to the (p-val) column
	results = results[order(results[,2]),]

	return(results)
}
"""

rStats = SignatureTranslatedAnonymousPackage(rcode, "rStats")


def fisherExact(userID, projectID, level, itemsOfInterest, catvar, minthreshold, keepthreshold, catVar1, catVar2):
	if itemsOfInterest is None or itemsOfInterest == "":
		return []

	otuTable = analysis.csvToTable(userID, projectID, analysis.OTU_TABLE_NAME)
	otuMetadata = analysis.csvToTable(userID, projectID, analysis.METADATA_NAME)
	taxonomyMap = analysis.getTaxonomyMapping(userID, projectID)

	metaVals = analysis.getMetadataInOTUTableOrder(otuTable, otuMetadata, analysis.getCatCol(otuMetadata, catvar))
	groups = robjects.FactorVector(robjects.StrVector(metaVals))

	otuTable = analysis.getOTUTableAtLevelIntegrated(otuTable, taxonomyMap, itemsOfInterest, level)

	# Forms an OTU only table (without IDs)
	allOTUs = [];
	col = analysis.OTU_START_COL
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

	fisherResults = rStats.fisher_exact(dataf, groups, int(minthreshold), int(keepthreshold))
	
	results = []
	i = 1
	while i <= fisherResults.nrow:
		newRow = []
		j = 1
		while j <= fisherResults.ncol:
			if j > 1:
				newRow.append(float(fisherResults.rx(i,j)[0]))
			else:
				newRow.append(str(fisherResults.rx(i,j)[0]))
			j += 1
		i += 1
		results.append(newRow)

	cat1 = catVar1
	cat2 = catVar2
	abundancesObj = {}
	abundancesObj["results"] = results
	abundancesObj["cat1"] = cat1
	abundancesObj["cat2"] = cat2

	return abundancesObj


def enrichedSelection(userID, projectID, level, itemsOfInterest, catvar, catVar1, catVar2, percentAbundanceThreshold):
	if itemsOfInterest is None or itemsOfInterest == "":
		return []

	otuTable = analysis.csvToTable(userID, projectID, analysis.OTU_TABLE_NAME)
	otuMetadata = analysis.csvToTable(userID, projectID, analysis.METADATA_NAME)
	taxonomyMap = analysis.getTaxonomyMapping(userID, projectID)

	metaVals = analysis.getMetadataInOTUTableOrder(otuTable, otuMetadata, analysis.getCatCol(otuMetadata, catvar))

	otuTable = analysis.getOTUTableAtLevelIntegrated(otuTable, taxonomyMap, itemsOfInterest, level)

	otuTablePercentAbundance = convertToPercentAbundance(otuTable, float(percentAbundanceThreshold))
	otuTableCat1, otuTableCat2 = separateIntoGroups(otuTablePercentAbundance, otuMetadata, catvar, catVar1, catVar2)

	otuTableCat1 = keepOnlyOTUs(otuTableCat1)
	otuTableCat2 = keepOnlyOTUs(otuTableCat2)

	diff1 = diffBase(otuTableCat1, otuTableCat2)
	diff2 = diffBase(otuTableCat2, otuTableCat1)

	diff1Arr = []
	for d in diff1:
		dObj = {}
		if int(level) == -1:
			dObj["t"] = d
			dObj["c"] = ', '.join(taxonomyMap[d])
		else:
			dObj["t"] = d
			dObj["c"] = ""
		diff1Arr.append(dObj)

	diff2Arr = []
	for d in diff2:
		dObj = {}
		if int(level) == -1:
			dObj["t"] = d
			dObj["c"] = ', '.join(taxonomyMap[d])
		else:
			dObj["t"] = d
			dObj["c"] = ""
		diff2Arr.append(dObj)

	abundancesObj = {}
	abundancesObj["diff1"] = diff1Arr
	abundancesObj["diff2"] = diff2Arr

	return abundancesObj


# Helpers

def convertToPercentAbundance(base, perThreshold):
	baseNew = []
	OTU_START = analysis.OTU_START_COL

	i = 0
	for row in base:
		if i == 0:
			baseNew.append(row)
		else:
			newRow = []
			colNum = OTU_START
			rowSum = 0
			# Find top OTUs per row
			while colNum < len(row):
				# Is this an OTU of interest?
				rowSum = rowSum + float(row[colNum])
				colNum = colNum + 1

			colNum = 0
			while colNum < len(row):
				if colNum >= OTU_START and rowSum > 0:
					# Is this an OTU of interest?
					per = float(row[colNum]) / float(rowSum)
					if per > perThreshold:
						newRow.append(float(per))
					else:
						newRow.append(float(0))
				else:
					newRow.append(row[colNum])
				colNum = colNum + 1

			baseNew.append(newRow)

		i = i + 1
	return baseNew


def diffBase(a, b):
	colNumToOTU = {}
	aOTUs = set()
	bOTUs = set()
	i = 0
	for row in a:
		if i == 0:
			colNum = 0
			while colNum < len(row):
				colNumToOTU[colNum] = row[colNum]
				colNum = colNum + 1
		else:
			colNum = 0
			while colNum < len(row):
				if row[colNum] > 0:
					if colNumToOTU[colNum] not in aOTUs:
						aOTUs.add(colNumToOTU[colNum])
				colNum = colNum + 1
		i = i + 1

	i = 0
	for row in b:
		if i == 0:
			colNum = 0
			while colNum < len(row):
				colNumToOTU[colNum] = row[colNum]
				colNum = colNum + 1
		else:
			colNum = 0
			while colNum < len(row):
				if row[colNum] > 0:
					if colNumToOTU[colNum] not in bOTUs:
						bOTUs.add(colNumToOTU[colNum])
				colNum = colNum + 1
		i = i + 1

	return diff(aOTUs,bOTUs)

def diff(a, b):
    return [aa for aa in a if aa not in b]

def separateIntoGroups(base, baseMetadata, catvar, catCol1, catCol2):
	catvarCol = analysis.getCatCol(baseMetadata, catvar)
	catCol1Samples = {}
	catCol2Samples = {}

	i = 1
	while i < len(baseMetadata):
		if baseMetadata[i][catvarCol] == catCol1:
			catCol1Samples[baseMetadata[i][analysis.OTU_GROUP_ID_COL]] = 1
		if baseMetadata[i][catvarCol] == catCol2:
			catCol2Samples[baseMetadata[i][analysis.OTU_GROUP_ID_COL]] = 1
		i += 1

	baseCat1 = []
	baseCat2 = []
	i = 0
	for o in base:
		if i == 0:
			baseCat1.append(o)
			baseCat2.append(o)
		else:
			if o[analysis.OTU_GROUP_ID_COL] in catCol1Samples:
				baseCat1.append(o)
			elif o[analysis.OTU_GROUP_ID_COL] in catCol2Samples:
				baseCat2.append(o)
		i = i + 1
	return baseCat1, baseCat2

def keepOnlyOTUs(base):
	newBase = []
	for o in base:
		newRow = []
		j = analysis.OTU_START_COL
		while j < len(o):
			newRow.append(o[j])
			j += 1
		newBase.append(newRow)
	return newBase

# fisherExact("1", "BatchsubOTULevel", 1, ["Firmicutes","Fusobacteria"], "Disease", 0, 5)
# enrichedSelection("1", "BatchsubOTULevel", 7, "All", "Disease", "IPF", "Control", 0.25)