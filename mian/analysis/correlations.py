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
import numpy as np
import json

from mian.model.genes import Genes


class Correlations(AnalysisBase):
    """
    Correlations correlate between two sample metadata values
    TODO: Implement boxplot taxonomic leveling
    """

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        base, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        metadata = table.get_sample_metadata()

        return self.analyse(user_request, base, headers, sample_labels, metadata)

    def analyse(self, user_request, base, headers, sample_labels, metadata):
        base = np.array(base, dtype=float)

        level = int(user_request.level)
        corrvar1 = user_request.get_custom_attr("corrvar1")
        corrvar2 = user_request.get_custom_attr("corrvar2")
        colorvar = user_request.get_custom_attr("colorvar")
        sizevar = user_request.get_custom_attr("sizevar")
        samplestoshow = user_request.get_custom_attr("samplestoshow")
        taxonomiesOfInterest1 = json.loads(user_request.get_custom_attr("corrvar1SpecificTaxonomies"))
        taxonomiesOfInterest2 = json.loads(user_request.get_custom_attr("corrvar2SpecificTaxonomies"))

        otuMetadata, _, _ = metadata.get_as_table_in_table_order(sample_labels, [corrvar1, corrvar2, colorvar, sizevar])

        colsOfInterest1 = []
        if corrvar1 == "mian-taxonomy-abundance":
            i = 0
            while i < len(headers):
                specificTaxonomies = headers[i].split(";")

                if len(specificTaxonomies) > level and specificTaxonomies[level].strip() in taxonomiesOfInterest1:
                    colsOfInterest1.append(i)
                i += 1
            if len(colsOfInterest1) == 0:
                return {"corrArr": [], "coef": 0, "pval": 0}

        colsOfInterest2 = []
        if corrvar2 == "mian-taxonomy-abundance":
            i = 0
            while i < len(headers):
                specificTaxonomies = headers[i].split(";")

                if len(specificTaxonomies) > level and specificTaxonomies[level].strip() in taxonomiesOfInterest2:
                    colsOfInterest2.append(i)
                i += 1
            if len(colsOfInterest2) == 0:
                return {"corrArr": [], "coef": 0, "pval": 0}

        # Retrieves the gene values (if applicable)
        gene_vals_1 = []
        gene_vals_2 = []
        if corrvar1 == "mian-gene" or corrvar2 == "mian-gene":
            genes = Genes(user_request.user_id, user_request.pid)
            if corrvar1 == "mian-gene":
                gene_vals_1 = genes.get_multi_gene_values(taxonomiesOfInterest1)
            if corrvar2 == "mian-gene":
                gene_vals_2 = genes.get_multi_gene_values(taxonomiesOfInterest2)

        corrArr = []
        corrValArr1 = []
        corrValArr2 = []

        i = 0
        while i < len(base):

            maxAbundance = np.max(base[i, :]) if corrvar1 == "mian-max" or corrvar2 == "mian-max" else 0
            totalAbundance = np.sum(base[i, :]) if corrvar1 == "mian-abundance" or corrvar2 == "mian-abundance" else 0

            if (samplestoshow == "nonzero" and totalAbundance > 0) or (
                    samplestoshow == "zero" and totalAbundance == 0) or samplestoshow == "both":
                corrObj = {}
                sampleID = sample_labels[i]

                if corrvar1 == "mian-taxonomy-abundance":
                    corrVal1 = np.sum(base[i, colsOfInterest1])
                elif corrvar1 == "mian-abundance":
                    corrVal1 = totalAbundance
                elif corrvar1 == "mian-max":
                    corrVal1 = maxAbundance
                elif corrvar1 == "mian-gene":
                    corrVal1 = gene_vals_1[i]
                else:
                    corrVal1 = otuMetadata[i][0]

                if corrvar2 == "mian-taxonomy-abundance":
                    corrVal2 = np.sum(base[i, colsOfInterest2])
                elif corrvar2 == "mian-abundance":
                    corrVal2 = totalAbundance
                elif corrvar2 == "mian-max":
                    corrVal2 = maxAbundance
                elif corrvar2 == "mian-gene":
                    corrVal2 = gene_vals_2[i]
                else:
                    corrVal2 = otuMetadata[i][1]

                corrObj["s"] = sampleID
                corrObj["c1"] = float(corrVal1)
                corrObj["c2"] = float(corrVal2)
                corrValArr1.append(float(corrVal1))
                corrValArr2.append(float(corrVal2))

                if colorvar == "mian-abundance":
                    colorVal = totalAbundance
                elif colorvar == "mian-max":
                    colorVal = maxAbundance
                elif colorvar == "None":
                    colorVal = 1
                else:
                    colorVal = otuMetadata[i][2]
                corrObj["color"] = colorVal

                if sizevar == "mian-abundance":
                    sizeVal = totalAbundance
                elif sizevar == "mian-max":
                    sizeVal = maxAbundance
                elif sizevar == "None":
                    sizeVal = 1
                else:
                    sizeVal = otuMetadata[i][3]
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
