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

from scipy import stats, math
from mian.analysis.analysis_base import AnalysisBase
from mian.core.statistics import Statistics
from mian.model.otu_table import OTUTable


class CorrelationsSelection(AnalysisBase):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        metadata = table.get_sample_metadata()

        return self.analyse(user_request, otu_table, headers, sample_labels, metadata)

    def analyse(self, user_request, base, headers, sample_labels, metadata):
        expvar = user_request.get_custom_attr("expvar")
        metadata_values = metadata.get_metadata_column_table_order(sample_labels, expvar)
        metadata_values = list(map(float, metadata_values))

        correlations = []
        pvals = []

        c = 0
        while c < len(base[0]):
            otu_name = headers[c]
            otu_vals = []
            r = 0
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

        qvals = Statistics.getFDRCorrection(pvals)

        i = 0
        while i < len(qvals):
            correlations[i]["qval"] = qvals[i]
            i += 1

        return {"correlations": correlations}
