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
        otu_table = table.get_table_after_filtering_and_aggregation(user_request.taxonomy_filter,
                                                                    user_request.taxonomy_filter_role,
                                                                    user_request.taxonomy_filter_vals,
                                                                    user_request.sample_filter,
                                                                    user_request.sample_filter_role,
                                                                    user_request.sample_filter_vals,
                                                                    user_request.level)

        metadata = table.get_sample_metadata()

        return self.analyse(user_request, otu_table, metadata)

    def analyse(self, user_request, base, metadata):
        otuMetadata = metadata.get_as_table()

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
            corrcol1 = metadata.get_metadata_column_number(corrvar1)

        corrcol2 = -1
        if corrvar2 != "mian-abundance" and corrvar2 != "mian-max":
            corrcol2 = metadata.get_metadata_column_number(corrvar2)

        colorcol = -1
        if colorvar != "mian-abundance" and colorvar != "mian-max":
            colorcol = metadata.get_metadata_column_number(colorvar)

        sizecol = -1
        if sizevar != "mian-abundance" and sizevar != "mian-max":
            sizecol = metadata.get_metadata_column_number(sizecol)

        corrArr = []
        corrValArr1 = []
        corrValArr2 = []

        i = 1
        while i < len(base):
            maxAbundance = 0
            totalAbundance = 0

            j = OTUTable.OTU_START_COL
            while j < len(base[i]):
                totalAbundance += float(base[i][j])
                j += 1

            j = OTUTable.OTU_START_COL
            while j < len(base[i]):
                if float(base[i][j]) > maxAbundance:
                    maxAbundance = float(base[i][j])
                j += 1

            if (samplestoshow == "nonzero" and totalAbundance > 0) or (
                    samplestoshow == "zero" and totalAbundance == 0) or samplestoshow == "both":
                corrObj = {}
                sampleID = base[i][OTUTable.SAMPLE_ID_COL]
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

                    colorVal = otuMetadata[metadataRow][colorcol]
                    if colorvar == "mian-abundance":
                        colorVal = totalAbundance
                    elif colorvar == "mian-max":
                        colorVal = maxAbundance
                    elif colorvar == "None":
                        colorVal = 1
                    corrObj["color"] = colorVal

                    sizeVal = otuMetadata[metadataRow][sizecol]
                    if sizevar == "mian-abundance":
                        sizeVal = totalAbundance
                    elif sizevar == "mian-max":
                        sizeVal = maxAbundance
                    elif sizevar == "None":
                        sizeVal = 1
                    corrObj["size"] = sizeVal

                    corrArr.append(corrObj)

            i += 1

        coef, pval = stats.pearsonr(corrValArr1, corrValArr2)
        if math.isnan(coef):
            coef = 0
        if math.isnan(pval):
            pval = 1

        abundances_obj = {"corrArr": corrArr, "coef": coef, "pval": pval}
        return abundances_obj
