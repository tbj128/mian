import os
import csv
from scipy import stats

# 
# OTU table I/O
# 

# Converts a CSV formatted OTU table to an array based format 
def csvToTable(userID, csvName):
	dir = os.path.dirname(__file__) + "/data/" + userID
	csvName = os.path.join(dir, csvName)
	baseCSV = csv.reader(open(csvName), delimiter=',', quotechar='|')
	otuMap = []
	for o in baseCSV:
		if len(o) > 1:
			otuMap.append(o)
	return otuMap

# Exports a OTU table to CSV format
def tableToCSV(base, csvName):
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

def getTaxonomyMapping(userID):
	taxonomyMapping = csvToTable(userID, "otuTaxonomyMapping.csv")
	# TODO: Consider column naming and detect Silva/GreenGenes
	taxonomyMap = {}
	i = 0
	for row in taxonomyMapping:
		if i > 0:
			taxonomyMap[row[0]] = decomposeSilvaTaxonomy(row[2])
		i += 1
	return taxonomyMap

# ================================

def getMetadataHeaders(userID):
	metadata = csvToTable(userID, "otuMetadata.csv")
	headers = [];
	i = 1
	while i < len(metadata[0]):
		headers.append(metadata[0][i])
		i += 1
	return headers

# ================================

def getAbundanceForOTUs(userID, level, itemsOfInterest, catvar):
	if itemsOfInterest is None:
		return []

	base = csvToTable(userID, "otuTable.csv")
	metadata = csvToTable(userID, "otuMetadata.csv")
	taxonomyMap = getTaxonomyMapping(userID)

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
	statistics = []
	abundanceKeys = abundances.keys()
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

			if allZeros == False:
				t, pvalue = stats.ttest_ind(statsAbundances[abundanceKeys[i]], statsAbundances[abundanceKeys[j]], 0, False)
				stat["pval"] = pvalue
				statistics.append(stat)
			else:
				stat["pval"] = 1
				statistics.append(stat)

			j += 1
		i += 1

	abundancesObj = {}
	abundancesObj["abundances"] = abundances
	abundancesObj["stats"] = statistics
	return abundancesObj