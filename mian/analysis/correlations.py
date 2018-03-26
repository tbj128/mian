# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#

from scipy import stats, math
from mian.analysis.analysis_base import AnalysisBase

from mian.model.otu_table import OTUTable
from mian.model.metadata import Metadata


class Correlations(AnalysisBase):
    """
    Correlations correlate between two sample metadata values
    """

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        table = table.get_table_after_filtering(user_request.sample_filter,
                                                user_request.sample_filter_vals,
                                                user_request.taxonomy_filter_vals,
                                                user_request.taxonomy_filter)
        metadata_values = table.get_sample_metadata().get_single_metadata_column(table, user_request.catvar)
        sample_ids_to_metadata_map = table.get_sample_metadata().get_sample_id_to_metadata_map(user_request.catvar)

        return self.analyse(user_request, table, metadata_values, sample_ids_to_metadata_map)

    def analyse(self, user_request, otuTable, otuMetadata, taxonomyMap):
        relevantOTUs = DataProcessor.get_relevant_otus(taxonomyMap, user_request.taxonomy_filter,
                                                       user_request.taxonomy_filter_vals)
        relevantCols = DataProcessor.get_relevant_cols(otuTable, relevantOTUs)

        corrvar1 = user_request.get_custom_attr("corrvar1")
        corrvar2 = user_request.get_custom_attr("corrvar2")
        colorvar = user_request.get_custom_attr("colorvar")
        sizevar = user_request.get_custom_attr("sizevar")
        samplestoshow = user_request.get_custom_attr("samplestoshow")

        sampleIDToMetadataRow = {}
        i = 1
        while i < len(otuMetadata):
            sampleID = otuMetadata[i][0]
            sampleIDToMetadataRow[sampleID] = i
            i += 1

        corrcol1 = -1
        if corrvar1 != "mian-abundance" and corrvar1 != "mian-max":
            corrcol1 = Metadata.get_cat_col(otuMetadata, corrvar1)

        corrcol2 = -1
        if corrvar2 != "mian-abundance" and corrvar2 != "mian-max":
            corrcol2 = Metadata.get_cat_col(otuMetadata, corrvar2)

        colorcol = -1
        if colorvar != "":
            colorcol = Metadata.get_cat_col(otuMetadata, colorvar)

        sizecol = -1
        if sizevar != "":
            sizecol = Metadata.get_cat_col(otuMetadata, sizevar)

        corrArr = []
        corrValArr1 = []
        corrValArr2 = []

        i = 1
        while i < len(otuTable):
            maxAbundance = 0
            totalAbundance = 0

            j = OTUTable.OTU_START_COL
            if corrvar1 == "mian-abundance" or corrvar2 == "mian-abundance":
                while j < len(otuTable[i]):
                    if j in relevantCols:
                        totalAbundance += float(otuTable[i][j])
                    j += 1

            j = OTUTable.OTU_START_COL
            if corrvar1 == "mian-max" or corrvar2 == "mian-max":
                while j < len(otuTable[i]):
                    if j in relevantCols:
                        if float(otuTable[i][j]) > maxAbundance:
                            maxAbundance = float(otuTable[i][j])
                    j += 1

            if (samplestoshow == "nonzero" and totalAbundance > 0) or (
                    samplestoshow == "zero" and totalAbundance == 0) or samplestoshow == "both":
                corrObj = {}
                sampleID = otuTable[i][OTUTable.SAMPLE_ID_COL]
                if sampleID in sampleIDToMetadataRow:
                    metadataRow = sampleIDToMetadataRow[sampleID]

                    corrVal1 = 0
                    if corrvar1 == "mian-abundance":
                        corrVal1 = totalAbundance
                    elif corrvar1 == "mian-max":
                        corrVal1 = maxAbundance
                    else:
                        corrVal1 = otuMetadata[metadataRow][corrcol1]

                    corrVal2 = 0
                    if corrvar2 == "mian-abundance":
                        corrVal2 = totalAbundance
                    elif corrvar2 == "mian-max":
                        corrVal2 = maxAbundance
                    else:
                        corrVal2 = otuMetadata[metadataRow][corrcol2]

                    corrObj["s"] = sampleID
                    corrObj["c1"] = float(corrVal1)
                    corrObj["c2"] = float(corrVal2)
                    corrValArr1.append(float(corrVal1))
                    corrValArr2.append(float(corrVal2))

                    if colorcol > -1:
                        colorVal = otuMetadata[metadataRow][colorcol]
                        corrObj["color"] = colorVal
                    else:
                        corrObj["color"] = ""

                    if sizecol > -1:
                        sizeVal = otuMetadata[metadataRow][sizecol]
                        corrObj["size"] = sizeVal
                    else:
                        corrObj["size"] = 0

                    corrArr.append(corrObj)

            i += 1

        coef, pval = stats.pearsonr(corrValArr1, corrValArr2)
        if math.isnan(coef):
            coef = 0
        if math.isnan(pval):
            coef = 1

        abundancesObj = {}
        abundancesObj["corrArr"] = corrArr
        abundancesObj["coef"] = coef
        abundancesObj["pval"] = pval
        return abundancesObj
