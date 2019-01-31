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
import logging
import rpy2.robjects.numpy2ri
rpy2.robjects.numpy2ri.activate()

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

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
        proportions = 100*(pca[["sdev"]]^2)/sum(pca[["sdev"]]^2)
        return(list(pca$x, proportions[1:min(length(proportions), 10)]))
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
        base, headers, sample_labels = table.get_table_after_filtering_and_aggregation(user_request)

        metadata_vals = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.catvar)
        return self.analyse(user_request, base, headers, sample_labels, metadata_vals)

    def analyse(self, user_request, base, headers, sample_labels, metaVals):
        logger.info("Starting PCA analysis")

        allOTUs = []
        col = 0
        while col < len(base[0]):
            baseCol = []
            row = 0
            while row < len(base):
                baseCol.append(base[row][col])
                row += 1
            allOTUs.append((headers[col], robjects.FloatVector(baseCol)))
            col += 1

        logger.info("After creating the R float vector table")

        od = rlc.OrdDict(allOTUs)
        dataf = robjects.DataFrame(od)

        logger.info("After creating the R dataframe")

        pca = self.rViz.pca(dataf)
        pcaVals = pca[0]
        pcaVariances = pca[1]

        logger.info("After running the R PCA")

        pca1Min = 1000000
        pca2Min = 1000000
        pca3Min = 1000000
        pca1Max = 0
        pca2Max = 0
        pca3Max = 0

        pca1 = user_request.get_custom_attr("pca1")
        pca2 = user_request.get_custom_attr("pca2")
        pca3 = user_request.get_custom_attr("pca3")

        pcaRow = []
        i = 1  # RObjects use 1 based indexing
        while i <= pcaVals.nrow:
            meta = ""
            if metaVals and len(metaVals) == pcaVals.nrow:
                meta = metaVals[i - 1]

            pcaObj = {"s": sample_labels[i - 1],
                      "m": meta,
                      "pca1": round(float(pcaVals.rx(i, int(pca1))[0]), 8),
                      "pca2": round(float(pcaVals.rx(i, int(pca2))[0]), 8),
                      "pca3": round(float(pcaVals.rx(i, int(pca3))[0]), 8)
                      }
            if pcaObj["pca1"] > pca1Max:
                pca1Max = pcaObj["pca1"]
            if pcaObj["pca1"] < pca1Min:
                pca1Min = pcaObj["pca1"]

            if pcaObj["pca2"] > pca2Max:
                pca2Max = pcaObj["pca2"]
            if pcaObj["pca2"] < pca2Min:
                pca2Min = pcaObj["pca2"]

            if pcaObj["pca3"] > pca3Max:
                pca3Max = pcaObj["pca3"]
            if pcaObj["pca3"] < pca3Min:
                pca3Min = pcaObj["pca3"]

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
        abundancesObj["pca3Max"] = pca3Max
        abundancesObj["pca3Min"] = pca3Min
        return abundancesObj
