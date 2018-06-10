import numpy as np

from mian.analysis.analysis_base import AnalysisBase

from mian.model.otu_table import OTUTable


class Composition(AnalysisBase):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table = table.get_table_after_filtering_and_aggregation(user_request.taxonomy_filter,
                                                                    user_request.taxonomy_filter_role,
                                                                    user_request.taxonomy_filter_vals,
                                                                    user_request.sample_filter,
                                                                    user_request.sample_filter_role,
                                                                    user_request.sample_filter_vals,
                                                                    user_request.level)

        metadata = table.get_sample_metadata().get_as_table()

        return self.analyse(user_request, otu_table, metadata)

    def analyse(self, user_request, base, metadata):

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
        i = 1
        while i < len(base):
            sampleID = base[i][OTUTable.SAMPLE_ID_COL]
            total = 0
            j = OTUTable.OTU_START_COL
            while j < len(base[i]):
                total += float(base[i][j])
                j += 1
            totalAbun[sampleID] = total
            i += 1

        # Iterates through each tax classification and calculates the relative abundance for each category
        colToTax = {}
        j = OTUTable.OTU_START_COL
        while j < len(base[0]):
            tax = base[0][j]
            compositionAbun[tax] = {}
            for m, v in uniqueMetadataVals.items():
                compositionAbun[tax][m] = []

            i = 1
            while i < len(base):
                sampleID = base[i][OTUTable.SAMPLE_ID_COL]
                if sampleID in metadataMap:
                    m = metadataMap[sampleID]
                    compositionAbun[tax][m].append(float(base[i][j]) / float(totalAbun[sampleID]))
                i += 1

            for m, v in uniqueMetadataVals.items():
                compositionAbun[tax][m] = round(np.mean(compositionAbun[tax][m]), 3)

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
