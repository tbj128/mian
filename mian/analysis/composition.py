import numpy as np
import math

from mian.analysis.analysis_base import AnalysisBase

from mian.model.otu_table import OTUTable


class Composition(AnalysisBase):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        base, headers, sample_labels = table.get_table_after_filtering(user_request)

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

        # TODO: Refactor
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

        # Maps id to total
        totalAbun = {}
        i = 0
        while i < len(base):
            sampleID = sample_labels[i]
            total = 0
            j = 0
            while j < len(base[i]):
                total += float(base[i][j])
                j += 1
            totalAbun[sampleID] = total
            i += 1

        # Iterates through each tax classification and calculates the relative abundance for each category
        colToTax = {}
        j = 0
        while j < len(base[0]):
            tax = headers[j]
            compositionAbun[tax] = {}
            for m, v in uniqueMetadataVals.items():
                compositionAbun[tax][m] = []

            i = 0
            while i < len(base):
                sampleID = sample_labels[i]
                if sampleID in metadataMap:
                    m = metadataMap[sampleID]
                    compositionAbun[tax][m].append(float(base[i][j]) / float(totalAbun[sampleID]))
                i += 1

            for m, v in uniqueMetadataVals.items():
                comp_abun = round(np.mean(compositionAbun[tax][m]), 3)
                if not math.isnan(comp_abun):
                    compositionAbun[tax][m] = comp_abun

            j += 1

        formattedCompositionAbun = []
        for t, obj in compositionAbun.items():
            newObj = {}
            newObj["t"] = t
            newObj["o"] = obj
            formattedCompositionAbun.append(newObj)

        abundancesObj = {}
        abundancesObj["abundances"] = formattedCompositionAbun
        abundancesObj["metaVals"] = list(uniqueMetadataVals.keys())
        return abundancesObj

# print getCompositionAnalysis("1", "BatchsubOTULevel", 0, "Disease")
