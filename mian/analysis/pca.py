# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#
#
# ======== R specific setup =========
#
import rpy2.robjects as robjects
import rpy2.rlike.container as rlc
from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage

from mian.analysis.analysis_base import AnalysisBase

from mian.model.otu_table import OTUTable


class PCA(AnalysisBase):
    r = robjects.r

    #
    # ======== Main code begins =========
    #

    rcode = """
    library("RColorBrewer")

    pca <- function(allOTUs) {
        # Removes any columns that only contain 0s
        allOTUs <- allOTUs[, colSums(allOTUs) > 0]
        pca <- prcomp(allOTUs, center = TRUE, scale. = TRUE)
        return(pca$x)
    }

    pca_variance <- function(allOTUs) {
        # Removes any columns that only contain 0s
        allOTUs <- allOTUs[, colSums(allOTUs) > 0]
        pca <- prcomp(allOTUs, center = TRUE, scale. = TRUE)
        proportions = 100*(pca[["sdev"]]^2)/sum(pca[["sdev"]]^2)
        return(proportions[1:min(length(proportions), 10)])
    }

    get_colors <- function(groups) {
        cols <- brewer.pal(length(unique(groups)),"Set1")
        names(cols) = levels(groups)
        colors = c()
        for (g in groups) {
            colors = c(colors, cols[g])
        }
        return(colors)
    }
    """

    rViz = SignatureTranslatedAnonymousPackage(rcode, "rViz")

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table = table.get_table_after_filtering_and_aggregation(user_request.taxonomy_filter,
                                                                    user_request.taxonomy_filter_role,
                                                                    user_request.taxonomy_filter_vals,
                                                                    user_request.sample_filter,
                                                                    user_request.sample_filter_role,
                                                                    user_request.sample_filter_vals,
                                                                    user_request.level)

        metadata_vals = table.get_sample_metadata().get_metadata_column_table_order(otu_table, user_request.catvar)
        sample_ids_to_metadata_map = table.get_sample_metadata().get_sample_id_to_metadata_map(user_request.catvar)
        return self.analyse(user_request, otu_table, metadata_vals, sample_ids_to_metadata_map)

    def analyse(self, user_request, otuTable, metaVals, metaIDs):
        # Forms an OTU only table (without IDs)
        allOTUs = [];
        col = OTUTable.OTU_START_COL
        while col < len(otuTable[0]):
            colVals = []
            row = 1
            while row < len(otuTable):
                sampleID = otuTable[row][OTUTable.SAMPLE_ID_COL]
                if sampleID in metaIDs:
                    colVals.append(otuTable[row][col])
                row += 1
            allOTUs.append((otuTable[0][col], robjects.FloatVector(colVals)))
            col += 1

        od = rlc.OrdDict(allOTUs)
        dataf = robjects.DataFrame(od)
        pcaVals = self.rViz.pca(dataf)
        pcaVariances = self.rViz.pca_variance(dataf)

        pca1Min = 100
        pca2Min = 100
        pca1Max = 0
        pca2Max = 0

        pca1 = user_request.get_custom_attr("pca1")
        pca2 = user_request.get_custom_attr("pca2")

        pcaRow = []
        i = 1  # RObjects use 1 based indexing
        while i <= pcaVals.nrow:
            meta = metaVals[i - 1]
            pcaObj = {}
            pcaObj["m"] = meta
            pcaObj["pca1"] = round(float(pcaVals.rx(i, int(pca1))[0]), 8)
            pcaObj["pca2"] = round(float(pcaVals.rx(i, int(pca2))[0]), 8)
            if pcaObj["pca1"] > pca1Max:
                pca1Max = pcaObj["pca1"]
            if pcaObj["pca1"] < pca1Min:
                pca1Min = pcaObj["pca1"]

            if pcaObj["pca2"] > pca2Max:
                pca2Max = pcaObj["pca2"]
            if pcaObj["pca2"] < pca2Min:
                pca2Min = pcaObj["pca2"]

            pcaRow.append(pcaObj)
            i += 1

        pcaVarRow = []
        for p in pcaVariances:
            pcaVarRow.append(float(p))

        # TODO: Check
        abundancesObj = {}
        abundancesObj["pca"] = pcaRow
        abundancesObj["pcaVar"] = pcaVarRow
        abundancesObj["pca1Max"] = pca1Max
        abundancesObj["pca1Min"] = pca1Min
        abundancesObj["pca2Max"] = pca2Max
        abundancesObj["pca2Min"] = pca2Min
        return abundancesObj
