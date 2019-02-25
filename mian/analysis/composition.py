import numpy as np
import math
import logging

from mian.analysis.analysis_base import AnalysisBase

from mian.model.otu_table import OTUTable


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Composition(AnalysisBase):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        base, headers, sample_labels = table.get_table_after_filtering_and_aggregation(user_request)

        metadata = table.get_sample_metadata().get_as_table()

        return self.analyse(user_request, base, headers, sample_labels, metadata)

    def analyse(self, user_request, base, headers, sample_labels, metadata):
        plotType = user_request.get_custom_attr("plotType")
        xaxis = user_request.get_custom_attr("xaxis")
        if plotType == "heatmap":
            return self.analyse_heatmap(user_request, base, headers, sample_labels, metadata, xaxis)

        if xaxis == "Taxonomic":
            return self.analyse_taxonomic_groups(user_request, base, headers, sample_labels, metadata)
        else:
            return self.analyse_metadata(user_request, base, headers, sample_labels, metadata)

    def analyse_heatmap(self, user_request, base, headers, sample_labels, metadata, xaxis):
        """
        Return the composition to be parsed as a heatmap
        """

        row_headers = []
        if user_request.catvar == "none":
            row_headers = []
        elif user_request.catvar == "SampleID":
            row_headers = sample_labels
        else:
            metadata_sample_to_value = {}
            j = 0
            while j < len(metadata[0]):
                if metadata[0][j] == user_request.catvar:
                    # Found the column that contains the catvar so add all the values from this column
                    i = 1
                    while i < len(metadata):
                        sample = metadata[i][0]
                        metadata_sample_to_value[sample] = metadata[i][j]
                        i += 1
                    break
                j += 1

            i = 0
            for sample_label in sample_labels:
                row_headers.append(metadata_sample_to_value[sample_label])
                i += 1

        min = 10000000
        max = 0
        for row in base:
            for col in row:
                if col > max:
                    max = col
                if col < min:
                    min = col

        if xaxis == "Taxonomic":
            abundances_obj = {
                "row_headers": row_headers,
                "col_headers": headers,
                "data": base,
                "max": max,
                "min": min
            }
            return abundances_obj
        else:
            # Transpose the table
            new_base = []
            j = 0
            while j < len(base[0]):
                new_row = []
                i = 0
                while i < len(base):
                    new_row.append(base[i][j])
                    i += 1
                new_base.append(new_row)
                j += 1

            abundances_obj = {
                "row_headers": headers,
                "col_headers": row_headers,
                "data": new_base,
                "max": max,
                "min": min
            }
            return abundances_obj


    def analyse_metadata(self, user_request, base, headers, sample_labels, metadata):
        """
        Return the composition such that the selected metadata or sample ID are on the X-axis
        """

        # Populate the xAxisVals, which contains all the unique metadata variables that will
        # be displayed on the x-axis
        xAxisVals = {}
        if user_request.catvar == "none":
            # Add all of the sample IDs to the column "All"
            xAxisVals["All"] = sample_labels
        elif user_request.catvar == "SampleID":
            for s in sample_labels:
                xAxisVals[s] = [s]
        else:
            j = 0
            while j < len(metadata[0]):
                if metadata[0][j] == user_request.catvar:
                    # Found the column that contains the catvar so add all the values from this column
                    i = 1
                    while i < len(metadata):
                        if metadata[i][j] not in xAxisVals:
                            xAxisVals[metadata[i][j]] = []
                        xAxisVals[metadata[i][j]].append(metadata[i][0])
                        i += 1
                    break
                j += 1

        # Make a sample ID to OTU table row
        sampleIDToRowIndex = {}
        i = 0
        while i < len(sample_labels):
            sampleIDToRowIndex[sample_labels[i]] = i
            i += 1

        headerToId = {}
        i = 0
        for header in headers:
            headerToId[header] = i
            i += 1

        headerToTotalVal = {}
        output = []

        for key, samples in xAxisVals.items():
            # Display the average abundance of each taxonomic group across all samples in this metadata grouping
            headerToVal = {}
            j = 0
            for header in headers:
                headerIndex = headerToId[header]

                valsSum = 0
                valsTot = 0
                for sample in samples:
                    if sample not in sampleIDToRowIndex:
                        logger.warning("Sample is missing from the OTU table: " + str(sample))
                        continue
                    rowIndex = sampleIDToRowIndex[sample]
                    valsSum += base[rowIndex][j]
                    valsTot += 1

                avgVal = 0
                if valsTot > 0:
                    avgVal = round(valsSum / float(valsTot), 3)
                    headerToVal[headerIndex] = avgVal

                if header not in headerToTotalVal:
                    headerToTotalVal[headerIndex] = 0
                headerToTotalVal[headerIndex] += avgVal

                j += 1

            output.append({
                "t": key,
                "o": headerToVal
            })

        abundancesObj = {}
        abundancesObj["abundances"] = output
        abundancesObj["uniqueVals"] = sorted(headerToTotalVal.items(), key=lambda kv: kv[1], reverse=True)
        abundancesObj["idMap"] = reverse_map(headerToId)
        return abundancesObj


    def analyse_taxonomic_groups(self, user_request, base, headers, sample_labels, metadata):
        """
        Return the composition such that the taxonomic groups are on the X-axis
        """
        # Maps the ID to the metadata value
        metadataMap = {}
        uniqueMetadataVals = {}
        metadataToId = {}

        # Extracts the unique metadata values
        catCol = -1
        i = 0
        while i < len(metadata):
            if i == 0:
                if user_request.catvar == "SampleID":
                    catCol = 0
                else:
                    j = 0
                    while j < len(metadata[i]):
                        if metadata[i][j] == user_request.catvar:
                            catCol = j
                        j += 1
            else:
                # Process the core metadata file contents after locating the right cat col
                if catCol == -1:
                    metadataMap[metadata[i][0]] = "All"
                    uniqueMetadataVals["All"] = True
                    metadataToId["All"] = 0
                else:
                    metadataMap[metadata[i][0]] = metadata[i][catCol]
                    uniqueMetadataVals[metadata[i][catCol]] = True
                    if metadata[i][catCol] not in metadataToId:
                        metadataToId[metadata[i][catCol]] = len(metadataToId.keys())

            i += 1

        # Get a map of OTUs to their sum by group
        sumByOTU = {}

        j = 0
        while j < len(base[0]):
            i = 0
            otuSumsByGroup = {}
            for k,v in uniqueMetadataVals.items():
                otuSumsByGroup[k] = 0

            while i < len(base):
                sampleID = sample_labels[i]
                otuSumsByGroup[metadataMap[sampleID]] += float(base[i][j])
                i += 1
            otu = headers[j]
            sumByOTU[otu] = otuSumsByGroup
            j += 1

        totalByGroup = {}
        for k,v in uniqueMetadataVals.items():
            totalByGroup[k] = 0
            for otu,otuSumsByGroup in sumByOTU.items():
                # Adds up all the OTUs (by group)
                totalByGroup[k] += otuSumsByGroup[k]

        metadataToTotalVal = {}
        formattedCompositionAbun = []
        for otu,otuSumsByGroup in sumByOTU.items():
            relativeAbunObj = {}
            for k,v in uniqueMetadataVals.items():
                id = metadataToId[k] # Use ID to reduce space during transmission
                if totalByGroup[k] != 0:
                    relativeAbun = round(otuSumsByGroup[k] / float(totalByGroup[k]), 3)
                else:
                    relativeAbun = 0
                relativeAbunObj[id] = relativeAbun

                # Calculate the total val for each metadata (just so we can return the top metadata in each category)
                if k not in metadataToTotalVal:
                    metadataToTotalVal[id] = 0
                metadataToTotalVal[id] += relativeAbun

            newObj = {"t": otu, "o": relativeAbunObj}
            formattedCompositionAbun.append(newObj)

        abundancesObj = {}
        abundancesObj["abundances"] = formattedCompositionAbun
        abundancesObj["uniqueVals"] = sorted(metadataToTotalVal.items(), key=lambda kv: kv[1], reverse=True)
        abundancesObj["idMap"] = reverse_map(metadataToId)
        return abundancesObj

def reverse_map(map):
    new_map = {}
    for k,v in map.items():
        new_map[v] = k
    return new_map

