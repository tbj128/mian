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
from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage

from scipy import stats, math
from mian.analysis.analysis_base import AnalysisBase

from mian.model.otu_table import OTUTable


class CorrelationsSelection(AnalysisBase):
    r = robjects.r

    rcode = """
        fdr <- function(pvals) {
            return(p.adjust(pvals, method = "fdr"))
        }
        """

    rStats = SignatureTranslatedAnonymousPackage(rcode, "rStats")

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
        metadata_values = metadata.get_metadata_column_table_order(base, user_request.catvar)
        metadata_values = list(map(float, metadata_values))

        correlations = []
        pvals = []

        c = OTUTable.OTU_START_COL
        while c < len(base[0]):
            otu_name = base[0][c]
            otu_vals = []
            r = 1
            while r < len(base):
                otu_vals.append(float(base[r][c]))
                r += 1

            coef, pval = stats.pearsonr(metadata_values, otu_vals)
            if math.isnan(coef):
                coef = 0
            if math.isnan(pval):
                pval = 1

            correlations.append({"otu": otu_name, "coef": coef, "pval": pval})
            pvals.append(pval)

            c += 1

        pvals_r = robjects.FloatVector(pvals)

        qvals = self.rStats.fdr(pvals_r)

        i = 0
        while i < len(qvals):
            correlations[i]["qval"] = qvals[i]
            i += 1

        return {"correlations": correlations}
