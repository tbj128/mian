import numpy as np
import math

from mian.analysis.analysis_base import AnalysisBase

from mian.model.otu_table import OTUTable


class Composition(AnalysisBase):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        base, headers, sample_labels = table.get_table_after_filtering_and_aggregation(user_request)

        metadata = table.get_sample_metadata().get_as_table()

        return self.analyse(user_request, base, headers, sample_labels, metadata)

    def analyse(self, user_request, base, headers, sample_labels, metadata):

        # Stores the tax classification to the relative abun (averaged)
        # {
        #     "phylum" -> {
        #         "IPF": []
        #         "Control": []
        #     }
        # }
        compositionAbun = {}

        # Maps the ID to the metadata value
        metadataMap = {}
        uniqueMetadataVals = {}

        # Extracts the unique metadata values
        catCol = -1
        i = 0
        while i < len(metadata):
            if i == 0:
                j = 0
                while j < len(metadata[i]):
                    if metadata[i][j] == user_request.catvar:
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


        formattedCompositionAbun = []
        for otu,otuSumsByGroup in sumByOTU.items():
            relativeAbunObj = {}
            for k,v in uniqueMetadataVals.items():
                if totalByGroup[k] != 0:
                    relativeAbun = round(otuSumsByGroup[k] / float(totalByGroup[k]), 3)
                else:
                    relativeAbun = 0
                relativeAbunObj[k] = relativeAbun
            newObj = {"t": otu, "o": relativeAbunObj}
            formattedCompositionAbun.append(newObj)

        abundancesObj = {}
        abundancesObj["abundances"] = formattedCompositionAbun
        abundancesObj["metaVals"] = list(uniqueMetadataVals.keys())
        return abundancesObj

# print getCompositionAnalysis("1", "BatchsubOTULevel", 0, "Disease")
