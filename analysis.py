# ===========================================
# 
# mian Analysis Core Library
# @author: tbj128
# 
# ===========================================

# 
# Imports
# 

import os
import csv
from scipy import stats
import math
import random
import string
import numpy as np
import shutil
from subprocess import Popen, PIPE

# 
# Global Attributes
# 
OTU_TABLE_NAME_PRESUBSAMPLE = "otuTable.presubsample.shared"
OTU_TABLE_NAME_MOTHUR_SUBSAMPLE = "otuTable.presubsample.subsample.shared"
OTU_TABLE_NAME = "otuTable.shared"
TAXONOMY_MAP_NAME = "otuTaxonomyMapping.taxonomy"
METADATA_NAME = "otuMetadata.tsv"

OTU_GROUP_ID_COL = 1
OTU_START_COL = 3


# 
# OTU table I/O
# 

# Converts a CSV formatted OTU table to an array based format 
def csvToTable(userID, projectID, csvName, sep="\t"):
	dir = os.path.dirname(__file__)
	dir = os.path.join(dir, "data")
	dir = os.path.join(dir, userID)
	dir = os.path.join(dir, projectID)

	otuMap = []
	csvName = os.path.join(dir, csvName)
	with open(csvName, 'rb') as csvfile:
		# dialect = csv.Sniffer().sniff(csvfile.read(1024))
		# csvfile.seek(0)
		baseCSV = csv.reader(csvfile, delimiter=sep, quotechar='|')
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
	outputCSV = csv.writer(open(csvName, 'wb'), delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
	for row in base:
		outputCSV.writerow(row)

# Adds an attribute right before the last dot of the postfix
def addFileNameAttr(csvName, postfix, attr):
	csvName = csvName.lower().replace("." + postfix, "")
	csvName = csvName + "." + attr + "." + postfix
	return csvName

# ================================
# OTU Table Processing Helpers

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

	i = 0
	while i < len(base):
		if i == 0:
			# Header row
			# Ignores the first column (sample ID)
			newRow = []
			j = 0
			while j < OTU_START_COL:
				newRow.append(base[i][j])
				relevantCols[j] = 1
				j += 1

			j = OTU_START_COL
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

	i = 0
	while i < len(base):
		if i == 0:
			# Header row
			# Ignores the first column (sample ID)

			newRow = []
			j = 0
			while j < OTU_START_COL:
				newRow.append(base[i][j])
				relevantCols[j] = 1
				j += 1

			j = OTU_START_COL
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
	j = OTU_START_COL
	while j < len(base[0]):
		otuToColNum[base[0][j]] = j
		if otuToTaxaSpecific[base[0][j]] not in uniqueSpecificTax:
			uniqueSpecificTax.append(otuToTaxaSpecific[base[0][j]])
		j += 1

	newBase = []
	i = 0
	while i < len(base):
		newRow = []
		j = 0
		while j < OTU_START_COL:
			newRow.append(base[i][j])
			j += 1
			
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

def subsampleOTUTable(userID, projectID, projectSubsampleType, projectSubsampleTo):
	base = csvToTable(userID, projectID, OTU_TABLE_NAME_PRESUBSAMPLE)
	subsampleTo = 0

	if projectSubsampleType == "auto":
		# Picks the sample with the lowest sequences as the subsample to value
		lowestSequences = 0
		i = 1
		while i < len(base):
			total = 0
			j = OTU_START_COL
			while j < len(base[i]):
				total += float(base[i][j])
				j += 1
			if total > lowestSequences:
				lowestSequences = total
			i += 1
		subsampleTo = lowestSequences
	elif projectSubsampleType == "manual":
		if projectSubsampleTo.isdigit():
			subsampleTo = int(projectSubsampleTo)

	dir = os.path.dirname(__file__)
	dir = os.path.join(dir, "data")
	dir = os.path.join(dir, userID)
	dir = os.path.join(dir, projectID)
	sharedName = os.path.join(dir, OTU_TABLE_NAME_PRESUBSAMPLE)
	generatedSharedName = ""
	permSharedName = os.path.join(dir, OTU_TABLE_NAME)

	for f in os.listdir(dir):
	    if ".subsample.shared" in f and "presubsample" in f: 
	    	generatedSharedName = f
	    	break

	generatedSharedName = os.path.join(dir, generatedSharedName)
	
	if projectSubsampleType == "auto" or projectSubsampleType == "manual":
		print str(subsampleTo)
		c = Popen(['mothur'], shell=True, stdin=PIPE)
		c.communicate(input="sub.sample(shared=" + sharedName + ", size=" + str(subsampleTo) + ")\nquit()")

		if generatedSharedName != "":
			if os.path.isfile(permSharedName):
				os.remove(permSharedName)

			shutil.copy(generatedSharedName, permSharedName)
	else:
		if os.path.isfile(permSharedName):
			os.remove(permSharedName)
		shutil.copy(sharedName, permSharedName)
	
	return subsampleTo

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
	taxonomyMapping = csvToTable(userID, projectID, TAXONOMY_MAP_NAME)
	# TODO: Consider column naming and detect Silva/GreenGenes
	taxonomyMap = {}
	i = 0
	for row in taxonomyMapping:
		if i > 0:
			if 2 >= len(row):
				print row
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
	j = OTU_START_COL
	while j < len(otuTable):
		if otuTable[0][j] in relevantOTUs:
			cols[j] = 1
		j += 1
	return cols

# ================================

def getMetadataHeaders(userID, projectID):
	metadata = csvToTable(userID, projectID, METADATA_NAME)
	headers = [];
	i = 1
	while i < len(metadata[0]):
		headers.append(metadata[0][i])
		i += 1
	return headers

def getMetadataHeadersWithMetadata(userID, projectID):
	metadata = csvToTable(userID, projectID, METADATA_NAME)
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
	otuMetadata = csvToTable(userID, projectID, METADATA_NAME)
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
		if otuTable[row][OTU_GROUP_ID_COL] in metadataMap:
			metaVals.append(metadataMap[otuTable[row][OTU_GROUP_ID_COL]])
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

	base = csvToTable(userID, projectID, OTU_TABLE_NAME)
	metadata = csvToTable(userID, projectID, METADATA_NAME)
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
			j = OTU_START_COL
			while j < len(base[i]):
				if base[i][j] in otus:
					relevantCols.append(j)
				j += 1
		else:
			row = {}
			row["s"] = str(base[i][OTU_GROUP_ID_COL])

			totalAbundance = 0

			j = OTU_START_COL
			while j < len(base[i]):
				if j in relevantCols:
					totalAbundance += float(base[i][j])
				j += 1

			row["a"] = totalAbundance
			if base[i][OTU_GROUP_ID_COL] in metadataMap:
				abundances[metadataMap[base[i][OTU_GROUP_ID_COL]]].append(row)
				statsAbundances[metadataMap[base[i][OTU_GROUP_ID_COL]]].append(totalAbundance)
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

	base = csvToTable(userID, projectID, OTU_TABLE_NAME)
	metadata = csvToTable(userID, projectID, METADATA_NAME)
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
		j = OTU_START_COL
		while j < len(base[i]):
			if j == OTU_GROUP_ID_COL or base[0][j] in otus:
				newRow.append(base[i][j])
			j += 1
		i += 1
		newBase.append(newRow)
	base = newBase

	# Merge the OTUs at the same taxa level
	otuToColNum = {}
	uniqueSpecificTax = []

	# base now only has sample ID as the first column
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

def getCompositionAnalysis(userID, projectID, level, catvar):
	base = csvToTable(userID, projectID, OTU_TABLE_NAME)
	metadata = csvToTable(userID, projectID, METADATA_NAME)
	taxonomyMap = getTaxonomyMapping(userID, projectID)

	# Merges the OTUs based on their taxonomic classification at the specified level
	base = getOTUTableAtLevelIntegrated(base, taxonomyMap, "All", level)

	# Stores the tax classification to the relative abun (averaged)
	# {
	# 	"phylum" -> {
	# 		"IPF": []
	# 		"Control": []
	# 	}
	# }
	compositionAbun = {}

	# Maps the ID to the metadata value
	metadataMap = {}
	uniqueMetadataVals = {}

	# TODO: Refactor
	catCol = -1
	i = 0
	while i < len(metadata):
		if i == 0:
			j = 0
			while j < len(metadata[i]):
				if metadata[i][j] == catvar:
					catCol = j
				j += 1
		else:
			if catCol == -1:
				metadataMap[metadata[i][0]] = "All"
				uniqueMetadataVals["All"] = 1
			else:
				metadataMap[metadata[i][0]] = metadata[i][catCol]
				uniqueMetadataVals[metadata[i][catCol]] = 1
		i += 1

	# Maps id to total
	totalAbun = {}
	i = 1
	while i < len(base):
		sampleID = base[i][OTU_GROUP_ID_COL]
		total = 0
		j = OTU_START_COL
		while j < len(base[i]):
			total += float(base[i][j])
			j += 1
		totalAbun[sampleID] = total
		i += 1

	# Iterates through each tax classification and calculates the relative abundance for each category
	colToTax = {}
	j = OTU_START_COL
	while j < len(base[0]):
		tax = base[0][j]
		compositionAbun[tax] = {}
		for m, v in uniqueMetadataVals.iteritems():
			compositionAbun[tax][m] = []

		i = 1
		while i < len(base):
			sampleID = base[i][OTU_GROUP_ID_COL]
			if sampleID in metadataMap:
				m = metadataMap[sampleID]
				compositionAbun[tax][m].append(float(base[i][j]) / float(totalAbun[sampleID]))
			i += 1

		for m, v in uniqueMetadataVals.iteritems():
			compositionAbun[tax][m] = round(np.mean(compositionAbun[tax][m]), 3)

		j += 1

	formattedCompositionAbun = []
	for t, obj in compositionAbun.iteritems():
		newObj = {}
		newObj["t"] = t
		newObj["o"] = obj
		formattedCompositionAbun.append(newObj)

	abundancesObj = {}
	abundancesObj["abundances"] = formattedCompositionAbun
	abundancesObj["metaVals"] = uniqueMetadataVals.keys()
	return abundancesObj

def getTreeGrouping(userID, projectID, level, itemsOfInterest, catvar, taxonomyDisplayLevel, displayValues, excludeUnclassified):
	if itemsOfInterest is None or itemsOfInterest == "":
		return {}

	base = csvToTable(userID, projectID, OTU_TABLE_NAME)
	metadata = csvToTable(userID, projectID, METADATA_NAME)
	taxonomyMap = getTaxonomyMapping(userID, projectID)
	idToMetadata = mapIDToMetadata(metadata, getCatCol(metadata, catvar))
	uniqueMetadataVals = getUniqueMetadataCatVals(metadata, getCatCol(metadata, catvar))

	otuToColNum = {}
	j = OTU_START_COL
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
				sampleID = base[i][OTU_GROUP_ID_COL]
				if sampleID in idToMetadata:
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


def getRarefaction(userID, projectID):
	rarefactionBase = csvToTable(userID, projectID, "otuTable.groups.rarefaction")
	retVal = {}
	subsampleVals = []
	maxVal = 0
	maxSubsampleVal = 0
	maxSubsample = 10000
	j = 1
	while j < len(rarefactionBase[0]):
		if rarefactionBase[0][j].find("lci") != -1 or rarefactionBase[0][j].find("hci") != -1:
			j += 1
			continue

		newArr = []
		numNA = 0
		i = 1
		while i < len(rarefactionBase):
			if float(rarefactionBase[i][0]) > maxSubsample:
				break

			if j == 1:
				subsampleVals.append(float(rarefactionBase[i][0]))
				if float(rarefactionBase[i][0]) > maxSubsampleVal:
					maxSubsampleVal = float(rarefactionBase[i][0])

			if (rarefactionBase[i][j] == "NA"):
				newArr.append(-1)
				numNA += 1
			else:
				newArr.append(float(rarefactionBase[i][j]))
				if float(rarefactionBase[i][j]) > maxVal:
					maxVal = float(rarefactionBase[i][j])
			i += 1

		retVal[rarefactionBase[0][j]] = newArr

		j += 1

	abundancesObj = {}
	abundancesObj["result"] = retVal
	abundancesObj["subsampleVals"] = subsampleVals
	abundancesObj["max"] = maxVal
	abundancesObj["maxSubsampleVal"] = maxSubsampleVal
	return abundancesObj

# ==================================

# getAbundanceForOTUsByGrouping("1", "Test", 0, ["Bacteria"], "Disease", 1, 3)
# getTreeGrouping("1", "Test", 0, ["Bacteria"], "Disease", -1, "avgabun", "yes")
# print getCompositionAnalysis("1", "BatchsubOTULevel", 0, "Disease")
# print getRarefaction("1", "BatchsubSequenceLevel")