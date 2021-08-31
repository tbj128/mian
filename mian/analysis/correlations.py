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

from mian.analysis.alpha_diversity import AlphaDiversity
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
        phylogenetic_tree = table.get_phylogenetic_tree()

        return self.analyse(user_request, base, headers, sample_labels, metadata, phylogenetic_tree)

    def analyse(self, user_request, base, headers, sample_labels, metadata, phylogenetic_tree):
        level = int(user_request.level)
        corrvar1 = user_request.get_custom_attr("corrvar1")
        corrvar2 = user_request.get_custom_attr("corrvar2")
        colorvar = user_request.get_custom_attr("colorvar")
        corrMethod = user_request.get_custom_attr("corrMethod")
        sizevar = user_request.get_custom_attr("sizevar")
        samplestoshow = user_request.get_custom_attr("samplestoshow")
        taxonomiesOfInterest1 = json.loads(user_request.get_custom_attr("corrvar1SpecificTaxonomies"))
        taxonomiesOfInterest2 = json.loads(user_request.get_custom_attr("corrvar2SpecificTaxonomies"))
        taxonomiesOfInterest3 = json.loads(user_request.get_custom_attr("sizevarSpecificTaxonomies")) # Currently limited to only alpha diversity

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

        # # Retrieves the gene values (if applicable)
        gene_vals_1 = []
        gene_vals_2 = []
        genes = None
        if corrvar1 == "mian-gene" or corrvar2 == "mian-gene":
            genes = Genes(user_request.user_id, user_request.pid)
            if corrvar1 == "mian-gene":
                gene_vals_1 = genes.get_multi_gene_values(taxonomiesOfInterest1, sample_labels=sample_labels)
            if corrvar2 == "mian-gene":
                gene_vals_2 = genes.get_multi_gene_values(taxonomiesOfInterest2, sample_labels=sample_labels)


        # Get out any metadata that might be required later on
        metadata_request_arr = ["", "", "", ""]
        if not (corrvar1 == "None" or corrvar1 == "mian-taxonomy-abundance" or corrvar1 == "mian-abundance" or corrvar1 == "mian-max" or corrvar1 == "mian-gene"):
            metadata_request_arr[0] = corrvar1

        if not (corrvar2 == "None" or corrvar2 == "mian-taxonomy-abundance" or corrvar2 == "mian-abundance" or corrvar2 == "mian-max" or corrvar2 == "mian-gene"):
            metadata_request_arr[1] = corrvar2

        if not (colorvar == "None" or colorvar == "mian-taxonomy-abundance" or colorvar == "mian-abundance" or colorvar == "mian-max" or colorvar == "mian-gene"):
            metadata_request_arr[2] = colorvar

        if not (sizevar == "None" or sizevar == "mian-taxonomy-abundance" or sizevar == "mian-abundance" or sizevar == "mian-max" or sizevar == "mian-gene"):
            metadata_request_arr[3] = sizevar
        otuMetadata, _, _ = metadata.get_as_table_in_table_order(sample_labels, metadata_request_arr, genes=genes)


        alpha_params = []
        alpha_vals = []
        if corrvar1 == "mian-alpha":
            alpha_params.append(taxonomiesOfInterest1[0])
            alpha_params.append(taxonomiesOfInterest1[1])
        if corrvar2 == "mian-alpha":
            alpha_params.append(taxonomiesOfInterest2[0])
            alpha_params.append(taxonomiesOfInterest2[1])
        if sizevar == "mian-alpha":
            alpha_params.append(taxonomiesOfInterest3[0])
            alpha_params.append(taxonomiesOfInterest3[1])

        if corrvar1 == "mian-alpha" or corrvar2 == "mian-alpha" or sizevar == "mian-alpha":
            alpha = AlphaDiversity()
            if int(user_request.level) == -1:
                # OTU tables are returned as a CSR matrix
                base = base.toarray()
            alpha_vals = alpha.calculate_alpha_diversity(base, sample_labels, headers, phylogenetic_tree, alpha_params[1], alpha_params[0])

        corrArr = []
        corrValArr1 = []
        corrValArr2 = []

        i = 0
        while i < base.shape[0]:
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
                elif corrvar1 == "mian-alpha":
                    corrVal1 = alpha_vals[i]
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
                elif corrvar2 == "mian-alpha":
                    corrVal2 = alpha_vals[i]
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
                elif sizevar == "mian-alpha":
                    sizeVal = alpha_vals[i]
                elif sizevar == "None":
                    sizeVal = 1
                else:
                    sizeVal = otuMetadata[i][3]
                corrObj["size"] = sizeVal

                corrArr.append(corrObj)

            i += 1

        if corrMethod == "pearson":
            coef, pval = stats.pearsonr(corrValArr1, corrValArr2)
        elif corrMethod == "spearman":
            coef, pval = stats.spearmanr(corrValArr1, corrValArr2)
        else:
            raise NotImplementedError("Corr method is not implemented")

        if math.isnan(coef):
            coef = 0
        if math.isnan(pval):
            pval = 1

        abundances_obj = {"corrArr": corrArr, "coef": coef, "pval": pval}
        return abundances_obj
