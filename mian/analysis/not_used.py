
def getDistanceAnalysis(userID, projectID, taxonomyFilter, taxonomyFilterVals, sampleFilter, sampleFilterVals, level):
    base = csvToTable(userID, projectID, OTU_TABLE_NAME)
    metadata = csvToTable(userID, projectID, METADATA_NAME)
    taxonomyMap = getTaxonomyMapping(userID, projectID)

    base = filterOTUTableByMetadata(base, metadata, sampleFilter, sampleFilterVals)

    # Merges the OTUs based on their taxonomic classification at the specified level
    base = getOTUTableAtLevel(base, taxonomyMap, taxonomyFilterVals, taxonomyFilter)
    base = getOTUTableAtLevelIntegrated(base, taxonomyMap, "All", level)

    base = filterOTUByMinPositives(base, 6)

    # Proprocesses each column into a numpy array
    colToNumpy = {}
    i = OTU_START_COL
    while i < len(base[0]):
        descriptor = []
        row = 1
        while row < len(base):
            descriptor.append(float(base[row][i]))
            row += 1

        # Optional: Normalize?
        descriptor = np.array(descriptor)
        descriptor = descriptor / math.sqrt(np.sum(np.power(descriptor,2)))
        colToNumpy[base[0][i]] = descriptor
        i += 1


    similarityMatrix = [[0 for i in range(len(base[0]) - OTU_START_COL)] for j in range(len(base[0]) - OTU_START_COL)]
    mostSimilarI = ""
    mostSimilarJ = ""
    mostSimilarIDescriptor = []
    mostSimilarJDescriptor = []
    mostSimilarAngle = 10

    i = OTU_START_COL
    while i < len(base[0]):
        j = i + 1
        while j < len(base[0]):
            # Calculate the cosine similarity (note that the descriptors are already normalized)
            cosineSimilarity = np.dot(colToNumpy[base[0][i]], colToNumpy[base[0][j]])
            # Calculate angle corresponding to the cosine similarity
            angle = math.acos(cosineSimilarity)
            similarityMatrix[i - OTU_START_COL][j - OTU_START_COL] = angle
            similarityMatrix[j - OTU_START_COL][i - OTU_START_COL] = angle

            if angle <= mostSimilarAngle:
                mostSimilarAngle = angle
                mostSimilarI = base[0][i]
                mostSimilarJ = base[0][j]
                mostSimilarIDescriptor = colToNumpy[base[0][i]]
                mostSimilarJDescriptor = colToNumpy[base[0][j]]
            j += 1
        i += 1
    print(mostSimilarI)
    print(mostSimilarIDescriptor)
    print(mostSimilarJ)
    print(mostSimilarJDescriptor)
    print(np.dot(mostSimilarIDescriptor, mostSimilarJDescriptor))
    print(mostSimilarAngle)
    abundancesObj = {}
    abundancesObj["similarityMatrix"] = similarityMatrix
    return abundancesObj

#getDistanceAnalysis("1", "BatchsubOTULevel", 0, "mian-select-all", "none", "mian-select-all", 4)
