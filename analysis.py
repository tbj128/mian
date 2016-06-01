import os
import csv
from scipy import stats
import math
import random
import string
import numpy as np

# 
# OTU table I/O
# 

# Converts a CSV formatted OTU table to an array based format 
def csvToTable(userID, projectID, csvName):
	dir = os.path.dirname(__file__)
	dir = os.path.join(dir, "data")
	dir = os.path.join(dir, userID)
	dir = os.path.join(dir, projectID)

	csvName = os.path.join(dir, csvName)
	baseCSV = csv.reader(open(csvName), delimiter=',', quotechar='|')
	otuMap = []
	for o in baseCSV:
		if len(o) > 1:
			otuMap.append(o)
	return otuMap

# Exports a OTU table to CSV format
def tableToCSV(base, userID, projectID, csvName):
	dir = os.path.dirname(__file__)
	dir = os.path.join(dir, "data")
	dir = os.path.join(dir, userID)
	dir = os.path.join(dir, projectID)
	
	dir = os.path.dirname(__file__) + "/data/"
	csvName = os.path.join(dir, csvName)
	outputCSV = csv.writer(open(csvName, 'wb'), delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
	for row in base:
		outputCSV.writerow(row)

def addFileNameAttr(csvName, attr):
	csvName = csvName.lower().replace(".csv", "")
	csvName = csvName + "." + attr + ".csv"
	return csvName

# ================================
# OTU Table Processing Helpers

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

# This function returns the headers at the specified level
def getOTUTableAtLevelIntegrated(base, taxonomyMap, itemsOfInterest, level):
	otus = {}
	taxaSpecificToOTU = {}
	otuToTaxaSpecific = {}
	for otu, classification in taxonomyMap.iteritems():
		if int(level) >= 0 and int(level) < len(classification):
			if itemsOfInterest == "All" or classification[int(level)] in itemsOfInterest:
				otus[otu] = 1
				otuToTaxaSpecific[otu] = classification[int(level)]

				if classification[int(level)] not in taxaSpecificToOTU:
					taxaSpecificToOTU[classification[int(level)]] = [otu]
				else:
					taxaSpecificToOTU[classification[int(level)]].append(otu)
		else:
			# OTU level
			if itemsOfInterest == "All" or otu in itemsOfInterest:
				otus[otu] = 1
				otuToTaxaSpecific[otu] = otu

				if otu not in taxaSpecificToOTU:
					taxaSpecificToOTU[otu] = [otu]
				else:
					taxaSpecificToOTU[otu].append(otu)


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
	base = newOTUTable

	# Merge the OTUs at the same taxa level
	otuToColNum = {}
	uniqueSpecificTax = []
	j = 1
	while j < len(base[0]):
		otuToColNum[base[0][j]] = j
		if otuToTaxaSpecific[base[0][j]] not in uniqueSpecificTax:
			uniqueSpecificTax.append(otuToTaxaSpecific[base[0][j]])
		j += 1

	newBase = []
	i = 0
	while i < len(base):
		newRow = [base[i][0]]
		for specificTaxa in uniqueSpecificTax:
			if i > 0:
				relevantOTUs = taxaSpecificToOTU[specificTaxa]
				tot = 0
				for relevantOTU in relevantOTUs:
					if relevantOTU in otuToColNum:
						tot += float(base[i][otuToColNum[relevantOTU]])
				newRow.append(tot)
			else:
				newRow.append(specificTaxa)
		i += 1
		newBase.append(newRow)
	base = newBase

	return base

# ================================
# Statistics Helpers

def getTtest(statsAbundances):
	# Calculate the statistical p-value
	statistics = []
	abundanceKeys = statsAbundances.keys()

	i = 0
	while i < len(abundanceKeys):
		j = i + 1
		while j < len(abundanceKeys):
			stat = {}
			stat["c1"] = abundanceKeys[i]
			stat["c2"] = abundanceKeys[j]

			# Check if both are completely zero (otherwise will break ttest)
			allZeros = True
			for x in statsAbundances[abundanceKeys[i]]:
				if x != 0:
					allZeros = False
					break
			for x in statsAbundances[abundanceKeys[j]]:
				if x != 0:
					allZeros = False
					break

			if allZeros == False and len(statsAbundances[abundanceKeys[i]]) > 0 and len(statsAbundances[abundanceKeys[j]]) > 0:
				t, pvalue = stats.ttest_ind(statsAbundances[abundanceKeys[i]], statsAbundances[abundanceKeys[j]], 0, False)
				if not math.isnan(pvalue):
					stat["pval"] = pvalue
					statistics.append(stat)
			else:
				stat["pval"] = 1
				statistics.append(stat)

			j += 1
		i += 1
	return statistics

# ================================

def decomposeSilvaTaxonomy(tax):
	# IPF OTU Map
	# Bacteria(100);"Bacteroidetes"(100);Flavobacteria(100);"Flavobacteriales"(100);Flavobacteriaceae(100);Chryseobacterium(100);
	decomposed = []
	taxArr = tax.split(";")
	for t in taxArr:
		a = ""
		if "unclassified" in t:
			a = "unclassified"
		else:
			sID = t.split("(")
			a = sID[0].replace("\"", "")
		decomposed.append(a)
	return decomposed

def getTaxonomyMapping(userID, projectID):
	taxonomyMapping = csvToTable(userID, projectID, "otuTaxonomyMapping.csv")
	# TODO: Consider column naming and detect Silva/GreenGenes
	taxonomyMap = {}
	i = 0
	for row in taxonomyMapping:
		if i > 0:
			taxonomyMap[row[0]] = decomposeSilvaTaxonomy(row[2])
		i += 1
	return taxonomyMap

# ================================

def getRelevantOTUs(taxonomyMap, level, itemsOfInterest):
	otus = {}
	for otu, classification in taxonomyMap.iteritems():
		if int(level) >= 0 and int(level) < len(classification):
			if classification[int(level)] in itemsOfInterest:
				otus[otu] = 1
		else:
			if otu in itemsOfInterest:
				otus[otu] = 1
	return otus

def getRelevantCols(otuTable, relevantOTUs):
	cols = {}
	j = 1
	while j < len(otuTable):
		if otuTable[0][j] in relevantOTUs:
			cols[j] = 1
		j += 1
	return cols

# ================================

def getMetadataHeaders(userID, projectID):
	metadata = csvToTable(userID, projectID, "otuMetadata.csv")
	headers = [];
	i = 1
	while i < len(metadata[0]):
		headers.append(metadata[0][i])
		i += 1
	return headers

def getMetadataHeadersWithMetadata(userID, projectID):
	metadata = csvToTable(userID, projectID, "otuMetadata.csv")
	headers = [];
	i = 1
	while i < len(metadata[0]):
		headers.append(metadata[0][i])
		i += 1
	return headers, metadata

def getNumericMetadata(otuMetadata):
	headers = []
	j = 1
	while j < len(otuMetadata[0]):
		isNumeric = True
		i = 1
		while i < len(otuMetadata[i]):
			if any(c.isalpha() for c in otuMetadata[i][j]):
				isNumeric = False
				break
			i += 1
		if isNumeric:
			headers.append(otuMetadata[0][j])
		j += 1
	return headers

def getMetadataUniqueVals(userID, projectID, catvar):
	uniqueVals = []
	otuMetadata = csvToTable(userID, projectID, "otuMetadata.csv")
	catvarCol = getCatCol(otuMetadata, catvar)
	i = 1
	while i < len(otuMetadata):
		if otuMetadata[i][catvarCol] not in uniqueVals:
			uniqueVals.append(otuMetadata[i][catvarCol])
		i += 1
	return uniqueVals

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

def getCatCol(otuMetadata, catvar):
	catCol = 1
	j = 0
	while j < len(otuMetadata[0]):
		if otuMetadata[0][j] == catvar:
			catCol = j
		j += 1
	return catCol

def getUniqueMetadataCatVals(otuMetadata, metaCol):
	uniqueVals = []
	i = 1
	while i < len(otuMetadata):
		# Maps the ID column to metadata column
		if otuMetadata[i][metaCol] not in uniqueVals:
			uniqueVals.append(otuMetadata[i][metaCol])
		i += 1
	return uniqueVals


# ================================

def getAbundanceForOTUs(userID, projectID, level, itemsOfInterest, catvar):
	if itemsOfInterest is None:
		return {}

	base = csvToTable(userID, projectID, "otuTable.csv")
	metadata = csvToTable(userID, projectID, "otuMetadata.csv")
	taxonomyMap = getTaxonomyMapping(userID, projectID)

	statsAbundances = {}
	abundances = {}
	metadataMap = {}
	catCol = 1
	i = 0
	while i < len(metadata):
		if i == 0:
			j = 0
			while j < len(metadata[i]):
				if metadata[i][j] == catvar:
					catCol = j
				j += 1
		else:
			metadataMap[metadata[i][0]] = metadata[i][catCol]
			if metadata[i][catCol] not in abundances:
				abundances[metadata[i][catCol]] = []
				statsAbundances[metadata[i][catCol]] = []
		i += 1

	otus = {}
	for otu, classification in taxonomyMap.iteritems():
		if int(level) >= 0 and int(level) < len(classification):
			if classification[int(level)] in itemsOfInterest:
				otus[otu] = 1
		else:
			if otu in itemsOfInterest:
				otus[otu] = 1

	relevantCols = []
	i = 0
	while i < len(base):
		if i == 0:
			# Header row
			# Ignores the first column (sample ID)
			j = 1
			while j < len(base[i]):
				if base[i][j] in otus:
					relevantCols.append(j)
				j += 1
		else:
			row = {}
			row["s"] = str(base[i][0])

			totalAbundance = 0

			j = 1
			while j < len(base[i]):
				if j in relevantCols:
					totalAbundance += float(base[i][j])
				j += 1

			row["a"] = totalAbundance
			abundances[metadataMap[base[i][0]]].append(row)
			statsAbundances[metadataMap[base[i][0]]].append(totalAbundance)
		i += 1

	# Calculate the statistical p-value
	statistics = getTtest(statsAbundances)

	abundancesObj = {}
	abundancesObj["abundances"] = abundances
	abundancesObj["stats"] = statistics
	return abundancesObj

def getAbundanceForOTUsByGrouping(userID, projectID, level, itemsOfInterest, catvar, taxonomyGroupingGeneral, taxonomyGroupingSpecific):
	if itemsOfInterest is None or itemsOfInterest == "" or int(taxonomyGroupingGeneral) >= int(taxonomyGroupingSpecific):
		return {}

	base = csvToTable(userID, projectID, "otuTable.csv")
	metadata = csvToTable(userID, projectID, "otuMetadata.csv")
	taxonomyMap = getTaxonomyMapping(userID, projectID)

	# Get map of specific tax grouping to general tax grouping
	otus = {}
	otuToTaxaSpecific = {}
	taxaSpecificToOTU = {}
	taxGroupingMap = {}
	uniqueGeneralTax = []
	for otu, classification in taxonomyMap.iteritems():
		if int(taxonomyGroupingSpecific) >= 0 and int(taxonomyGroupingSpecific) < len(classification) and int(taxonomyGroupingGeneral) < int(taxonomyGroupingSpecific) and int(taxonomyGroupingGeneral) < len(classification):
			specificTaxa = classification[int(taxonomyGroupingSpecific)]
			generalTaxa = classification[int(taxonomyGroupingGeneral)]

			if specificTaxa not in itemsOfInterest:
				taxGroupingMap[specificTaxa] = generalTaxa

			if generalTaxa not in uniqueGeneralTax:
				uniqueGeneralTax.append(generalTaxa)

			if specificTaxa not in taxaSpecificToOTU:
				taxaSpecificToOTU[specificTaxa] = [otu]
			else:
				taxaSpecificToOTU[specificTaxa].append(otu)

			otuToTaxaSpecific[otu] = specificTaxa
	
		if int(level) >= 0 and int(level) < len(classification):
			if classification[int(level)] in itemsOfInterest:
				otus[otu] = 1
		else:
			if otu in itemsOfInterest:
				otus[otu] = 1

	# Grouped by catvar, then by the (eg.) averaged phylum, then by (eg.) averaged family
	idToMetadata = mapIDToMetadata(metadata, getCatCol(metadata, catvar))
	uniqueMetadataVals = getUniqueMetadataCatVals(metadata, getCatCol(metadata, catvar))
	
	# Find the OTUs that are relevant and subset the base table
	newBase = []
	i = 0
	while i < len(base):
		newRow = []
		j = 0
		while j < len(base[i]):
			if j == 0 or base[0][j] in otus:
				newRow.append(base[i][j])
			j += 1
		i += 1
		newBase.append(newRow)
	base = newBase

	# Merge the OTUs at the same taxa level
	otuToColNum = {}
	uniqueSpecificTax = []
	j = 1
	while j < len(base[0]):
		otuToColNum[base[0][j]] = j
		if otuToTaxaSpecific[base[0][j]] not in uniqueSpecificTax:
			uniqueSpecificTax.append(otuToTaxaSpecific[base[0][j]])
		j += 1

	newBase = []
	i = 0
	while i < len(base):
		newRow = [base[i][0]]
		for specificTaxa in uniqueSpecificTax:
			if i > 0:
				relevantOTUs = taxaSpecificToOTU[specificTaxa]
				tot = 0
				for relevantOTU in relevantOTUs:
					if relevantOTU in otuToColNum:
						tot += float(base[i][otuToColNum[relevantOTU]])
				newRow.append(tot)
			else:
				newRow.append(specificTaxa)
		i += 1
		newBase.append(newRow)
	base = newBase


	groupingPreAverage = {}

	j = 1
	while j < len(base[0]):
		taxaSpecific = base[0][j]
		taxaGeneral = taxGroupingMap[taxaSpecific]
		
		i = 1
		while i < len(base):
			id = base[i][0]
			metadata = idToMetadata[id]

			if taxaGeneral not in groupingPreAverage:
				groupingPreAverage[taxaGeneral] = {}

			if taxaSpecific not in groupingPreAverage[taxaGeneral]:
				groupingPreAverage[taxaGeneral][taxaSpecific] = {}

			if metadata not in groupingPreAverage[taxaGeneral][taxaSpecific]:
				groupingPreAverage[taxaGeneral][taxaSpecific][metadata] = {}
				groupingPreAverage[taxaGeneral][taxaSpecific][metadata]["tc"] = 1
				if float(base[i][j]) > 0: 
					groupingPreAverage[taxaGeneral][taxaSpecific][metadata]["c"] = 1
				else:
					groupingPreAverage[taxaGeneral][taxaSpecific][metadata]["c"] = 0
			else:
				groupingPreAverage[taxaGeneral][taxaSpecific][metadata]["tc"] += 1
				if float(base[i][j]) > 0: 
					groupingPreAverage[taxaGeneral][taxaSpecific][metadata]["c"] += 1
			i += 1
		j += 1

	groupingPostProcess = {}
	groupingPostProcess["name"] = ""
	groupingPostProcess["children"] = []
	for taxaGeneral,taxaSpecificObj in groupingPreAverage.iteritems():
		generalObj = {}
		generalObj["name"] = taxaGeneral
		generalObj["children"] = []
		taxaGeneralTotal = 0

		for taxaSpecific,metadataObj in taxaSpecificObj.iteritems():
			taxaSpecificTotal = 0
			for metadata,countObj in metadataObj.iteritems():
				taxaGeneralTotal += countObj["c"]
				taxaSpecificTotal += countObj["c"]

			if taxaSpecificTotal > 0:
				specificObj = metadataObj
				specificObj["name"] = taxaSpecific
				generalObj["children"].append(specificObj)

		if taxaGeneralTotal > 0:
			groupingPostProcess["children"].append(generalObj)

	abundancesObj = {}
	abundancesObj["metaUnique"] = uniqueMetadataVals
	abundancesObj["root"] = groupingPostProcess
	return abundancesObj


def getTreeGrouping(userID, projectID, level, itemsOfInterest, catvar, taxonomyDisplayLevel, displayValues, excludeUnclassified):
	if itemsOfInterest is None or itemsOfInterest == "":
		return {}

	base = csvToTable(userID, projectID, "otuTable.csv")
	metadata = csvToTable(userID, projectID, "otuMetadata.csv")
	taxonomyMap = getTaxonomyMapping(userID, projectID)
	idToMetadata = mapIDToMetadata(metadata, getCatCol(metadata, catvar))
	uniqueMetadataVals = getUniqueMetadataCatVals(metadata, getCatCol(metadata, catvar))

	otuToColNum = {}
	j = 1
	while j < len(base[0]):
		otuToColNum[base[0][j]] = j
		j += 1

	lenOfClassification = 0
	for otu, classification in taxonomyMap.iteritems():
		lenOfClassification = len(classification)
		break

	taxonomyDisplayLevel = int(taxonomyDisplayLevel)
	if taxonomyDisplayLevel >= lenOfClassification:
		taxonomyDisplayLevel = lenOfClassification
	elif taxonomyDisplayLevel < 0:
		taxonomyDisplayLevel = lenOfClassification

	treeObj = {}
	numLeaves = 0

	for otu, classification in taxonomyMap.iteritems():
		if otu in otuToColNum:
			otuObj = {}

			col = otuToColNum[otu]

			i = 1
			while i < len(base):
				sampleID = base[i][0]
				metaVal = idToMetadata[sampleID]
				otuVal = float(base[i][col])
				if displayValues == "nonzero":
					if metaVal in otuObj:
						if otuVal > 0:
							otuObj[metaVal]["c"] += 1
						otuObj[metaVal]["tc"] += 1
					else:
						otuObj[metaVal] = {}
						if otuVal > 0:
							otuObj[metaVal]["c"] = 1
						else:
							otuObj[metaVal]["c"] = 0
						otuObj[metaVal]["tc"] = 1
				else:
					if metaVal in otuObj:
						otuObj[metaVal]["v"].append(otuVal)
					else:
						otuObj[metaVal] = {}
						otuObj[metaVal]["v"] = [otuVal]

				i += 1

			classification.append(otu)

			# The user may want to exclude the unclassified OTUs (unclassified at the taxonomic display level)
			if excludeUnclassified == "yes":
				if classification[taxonomyDisplayLevel].lower() == "unclassified":
					continue

			numLeaves += treeGroupingHelper(treeObj, 0, taxonomyDisplayLevel, classification, uniqueMetadataVals, otuObj, displayValues)

	# print treeObj

	# Convert to D3 readable format
	fTreeObj = {}
	fTreeObj["name"] = "root"
	fTreeObj["children"] = []
	treeFormatterHelper(fTreeObj, treeObj, 0, taxonomyDisplayLevel, displayValues)
	# print fTreeObj
	abundancesObj = {}
	abundancesObj["metaUnique"] = uniqueMetadataVals
	abundancesObj["numLeaves"] = numLeaves
	abundancesObj["root"] = fTreeObj
	return abundancesObj

def treeGroupingHelper(treeObj, taxLevel, taxonomyDisplayLevel, classification, uniqueMetadataVals, otuObj, displayValues):
	levelClassification = classification[taxLevel]
	if levelClassification not in treeObj:
		treeObj[levelClassification] = {}

	numLeaves = 0

	if taxonomyDisplayLevel == taxLevel:
		# Associate the values
		for meta in uniqueMetadataVals:
			if meta in otuObj:
				if "nonzero" == displayValues:
					if meta in treeObj[levelClassification]:
						treeObj[levelClassification][meta]["c"] += otuObj[meta]["c"]
						treeObj[levelClassification][meta]["tc"] += otuObj[meta]["tc"]
					else:
						treeObj[levelClassification][meta] = {}
						treeObj[levelClassification][meta]["c"] = otuObj[meta]["c"]
						treeObj[levelClassification][meta]["tc"] = otuObj[meta]["tc"]
						numLeaves = 1
				else:
					if meta in treeObj[levelClassification]:
						treeObj[levelClassification][meta]["v"].extend(otuObj[meta]["v"])
					else:
						treeObj[levelClassification][meta] = {}
						treeObj[levelClassification][meta]["v"] = otuObj[meta]["v"]
						numLeaves = 1
	else:
		return treeGroupingHelper(treeObj[levelClassification], taxLevel + 1, taxonomyDisplayLevel, classification, uniqueMetadataVals, otuObj, displayValues)

	return numLeaves

def treeFormatterHelper(fTreeArr, treeObj, level, taxonomyDisplayLevel, displayValues):
	for taxa,child in treeObj.iteritems():
		newChildObj = {}
		newChildObj["name"] = taxa
		if level == taxonomyDisplayLevel:
			if "nonzero" == displayValues:
				newChildObj["val"] = child
			else:
				# Collapse the array into specific values
				if displayValues == "avgabun":
					metas = child.keys()
					for meta in metas:
						metaVals = child[meta]
						avg = np.mean(metaVals["v"])
						child[meta] = round(avg, 2)
						child["tc"] = len(metaVals["v"])
				elif displayValues == "medianabun":
					metas = child.keys()
					for meta in metas:
						metaVals = child[meta]
						child[meta] = np.median(metaVals["v"])
						child["tc"] = len(metaVals["v"])
				elif displayValues == "maxabun":
					metas = child.keys()
					for meta in metas:
						metaVals = child[meta]
						child[meta] = np.amax(metaVals["v"])
						child["tc"] = len(metaVals["v"])
				else:
					print "Unknown display value"
					child[meta] = 0

				newChildObj["val"] = child

		else:
			newChildObj["children"] = []
			treeFormatterHelper(newChildObj, child, level + 1, taxonomyDisplayLevel, displayValues)
		fTreeArr["children"].append(newChildObj)


# ==================================

# getAbundanceForOTUsByGrouping("1", "Test", 0, ["Bacteria"], "Disease", 1, 3)
# getTreeGrouping("1", "Test", 0, ["Bacteria"], "Disease", -1, "avgabun", "yes")