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
library(Boruta)
library(glmnet)

boruta <- function(base, groups, keepthreshold, pval, maxruns) {
	# Remove any OTUs with presence < keepthreshold (for efficiency)
	x = base[,colSums(base!=0)>=keepthreshold]
	y.1 = as.factor(groups)
	b <- Boruta(x, y.1, doTrace=0, holdHistory=FALSE, pValue=pval, maxRuns=maxruns)
	return (b$finalDecision)
}

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

run_glmnet <- function(base, groups, keepthreshold, alphaVal, familyType, lambda_threshold_type, lambda_val) {
	# Remove any OTUs with presence < keepthreshold (for efficiency)
	x = base[,colSums(base!=0)>=keepthreshold]
	y.1 = as.factor(groups)

	# x = x[,2:ncol(x)];
	x <- as.matrix(data.frame(x))
	y <- as.factor(groups)
	yN = as.numeric(y)
	# y <- base[,SAV]
	cv <- cv.glmnet(x,y,alpha=alphaVal,family=familyType)

	# plot(cv,cex=2)
	if (lambda_threshold_type == "Custom") {
		scAll = coef(cv,s=exp(lambda_val))
	} else if (lambda_threshold_type == "lambda1se") {
		scAll = coef(cv,s=cv$lambda.1se)
	} else {
		scAll = coef(cv,s=cv$lambda.min)
	}


	uniqueGroups = unique(groups)
	if (familyType == "binomial") {
		results = matrix(,(length(scAll) - 1)*length(uniqueGroups), 3)
	} else {
		results = matrix(,(length(scAll[[uniqueGroups[1]]]) - 1)*length(uniqueGroups), 3)
	}
	index = 1
	for (g in 1:length(uniqueGroups)) {
		if (familyType == "binomial") {
			sc = scAll
		} else {
			sc = scAll[[uniqueGroups[g]]]
		}
		
		# Start at 2 to discount the intercept entry
		for (s in 2:length(sc)) {
			results[index, 1] = as.character(uniqueGroups[g])
			results[index, 2] = rownames(sc)[s]
			results[index, 3] = sc[s]
			index = index + 1
		}
	}
	return(results)
}

"""

rStats = SignatureTranslatedAnonymousPackage(rcode, "rStats")


def boruta(userID, projectID, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, level, catvar, keepthreshold, pval, maxruns):
	otuTable = analysis.csvToTable(userID, projectID, analysis.OTU_TABLE_NAME)
	otuMetadata = analysis.csvToTable(userID, projectID, analysis.METADATA_NAME)
	taxonomyMap = analysis.getTaxonomyMapping(userID, projectID)

	otuTable = analysis.filterOTUTableByMetadata(otuTable, otuMetadata, sampleFilter, sampleFilterVals)
	otuTable = analysis.getOTUTableAtLevel(otuTable, taxonomyMap, taxonomyFilterVals, taxonomyFilter)
	otuTable = analysis.getOTUTableAtLevelIntegrated(otuTable, taxonomyMap, "All", level)

	metaVals = analysis.getMetadataInOTUTableOrder(otuTable, otuMetadata, analysis.getCatCol(otuMetadata, catvar))
	metaIDs = analysis.mapIDToMetadata(otuMetadata, 1)
	groups = robjects.FactorVector(robjects.StrVector(metaVals))

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

	borutaResults = rStats.boruta(dataf, groups, int(keepthreshold), float(pval), int(maxruns))
	
	assignments = {}

	i = 0
	for lab in borutaResults.iter_labels():
		if lab in assignments:
			assignments[lab].append(allOTUs[i][0])
		else:
			assignments[lab] = [allOTUs[i][0]]
		i += 1

	abundancesObj = {}
	abundancesObj["results"] = assignments

	return abundancesObj


def fisherExact(userID, projectID, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, level, catvar, minthreshold, keepthreshold, catVar1, catVar2):
	otuTable = analysis.csvToTable(userID, projectID, analysis.OTU_TABLE_NAME)
	otuMetadata = analysis.csvToTable(userID, projectID, analysis.METADATA_NAME)
	taxonomyMap = analysis.getTaxonomyMapping(userID, projectID)

	otuTable = analysis.filterOTUTableByMetadata(otuTable, otuMetadata, sampleFilter, sampleFilterVals)
	otuTable = analysis.getOTUTableAtLevel(otuTable, taxonomyMap, taxonomyFilterVals, taxonomyFilter)
	otuTable = analysis.getOTUTableAtLevelIntegrated(otuTable, taxonomyMap, "All", level)

	metaVals = analysis.getMetadataInOTUTableOrder(otuTable, otuMetadata, analysis.getCatCol(otuMetadata, catvar))
	metaIDs = analysis.mapIDToMetadata(otuMetadata, 1)
	groups = robjects.FactorVector(robjects.StrVector(metaVals))


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


def enrichedSelection(userID, projectID, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, level, catvar, catVar1, catVar2, percentAbundanceThreshold):
	otuTable = analysis.csvToTable(userID, projectID, analysis.OTU_TABLE_NAME)
	otuMetadata = analysis.csvToTable(userID, projectID, analysis.METADATA_NAME)
	taxonomyMap = analysis.getTaxonomyMapping(userID, projectID)

	metaVals = analysis.getMetadataInOTUTableOrder(otuTable, otuMetadata, analysis.getCatCol(otuMetadata, catvar))
	metaIDs = analysis.mapIDToMetadata(otuMetadata, 1)

	otuTable = analysis.filterOTUTableByMetadata(otuTable, otuMetadata, sampleFilter, sampleFilterVals)
	otuTable = analysis.getOTUTableAtLevel(otuTable, taxonomyMap, taxonomyFilterVals, taxonomyFilter)
	otuTable = analysis.getOTUTableAtLevelIntegrated(otuTable, taxonomyMap, "All", level)

	otuTablePercentAbundance = convertToPercentAbundance(otuTable, float(percentAbundanceThreshold))
	otuTableCat1, otuTableCat2 = separateIntoGroups(otuTablePercentAbundance, otuMetadata, catvar, catVar1, catVar2)
	
	otuTableCat1 = keepOnlyOTUs(otuTableCat1, metaIDs)
	otuTableCat2 = keepOnlyOTUs(otuTableCat2, metaIDs)
	
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


def glmnet(userID, projectID, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, level, catvar, keepthreshold, alphaVal, family, lambda_threshold_type, lambda_val):
	otuTable = analysis.csvToTable(userID, projectID, analysis.OTU_TABLE_NAME)
	otuMetadata = analysis.csvToTable(userID, projectID, analysis.METADATA_NAME)
	taxonomyMap = analysis.getTaxonomyMapping(userID, projectID)

	otuTable = analysis.filterOTUTableByMetadata(otuTable, otuMetadata, sampleFilter, sampleFilterVals)
	otuTable = analysis.getOTUTableAtLevel(otuTable, taxonomyMap, taxonomyFilterVals, taxonomyFilter)
	otuTable = analysis.getOTUTableAtLevelIntegrated(otuTable, taxonomyMap, "All", level)

	metaVals = analysis.getMetadataInOTUTableOrder(otuTable, otuMetadata, analysis.getCatCol(otuMetadata, catvar))
	metaIDs = analysis.mapIDToMetadata(otuMetadata, 1)
	groups = robjects.FactorVector(robjects.StrVector(metaVals))

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
	glmnetResult = rStats.run_glmnet(dataf, groups, int(keepthreshold), float(alphaVal), family, lambda_threshold_type, float(lambda_val))
	
	accumResults = {}
	i = 1
	while i <= glmnetResult.nrow:
		newRow = []
		newRow.append(glmnetResult.rx(i,2)[0])
		newRow.append(float(glmnetResult.rx(i,3)[0]))

		g = glmnetResult.rx(i,1)[0]
		if g in accumResults:
			accumResults[g].append(newRow)
		else:
			accumResults[g] = [newRow]

		i += 1

	abundancesObj = {}
	print accumResults
	abundancesObj["results"] = accumResults

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
			catCol1Samples[baseMetadata[i][0]] = 1
		if baseMetadata[i][catvarCol] == catCol2:
			catCol2Samples[baseMetadata[i][0]] = 1
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

def keepOnlyOTUs(base, metaIDs):
	newBase = []
	i = 0
	for o in base:
		sampleID = base[i][analysis.OTU_GROUP_ID_COL]
		if i == 0 or sampleID in metaIDs:
			newRow = []
			j = analysis.OTU_START_COL
			while j < len(o):
				newRow.append(o[j])
				j += 1
			newBase.append(newRow)
		i += 1
	return newBase

# fisherExact("1", "BatchsubOTULevel", 1, ["Firmicutes","Fusobacteria"], "Disease", 0, 5)
# enrichedSelection("1", "BatchsubOTULevel", 7, "All", "Disease", "IPF", "Control", 0.25)
# boruta("1", "BatchsubSequenceLevel", 1, "Disease", 5, 0.01, 100)
# glmnet("1", "BatchsubSequenceLevel", 1, "Disease", 5, 0.5, "multinomial", "Custom", -2)
# glmnet("1", "BatchsubSequenceLevel", 1, "Disease", 5, 0.5, "binomial", "Custom", -2)
# glmnet("1", "BatchsubSequenceLevel", 1, "Disease", 5, 0.5, "binomial", "lambda1se", -2)