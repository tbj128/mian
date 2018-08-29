# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#

from mian.model.otu_table import OTUTable
from mian.core.statistics import Statistics
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


class DifferentialSelection(object):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        sample_ids_to_metadata_map = table.get_sample_metadata().get_sample_id_to_metadata_map(user_request.catvar)

        return self.analyse(user_request, otu_table, headers, sample_labels, sample_ids_to_metadata_map)

    def analyse(self, user_request, base, headers, sample_labels, sample_ids_to_metadata_map):
        pvalthreshold = float(user_request.get_custom_attr("pvalthreshold"))
        catVar1 = user_request.get_custom_attr("pwVar1")
        catVar2 = user_request.get_custom_attr("pwVar2")

        # Perform differential analysis between two groups

        logger.info("Starting differential analysis")
        otu_pvals = []

        j = 0
        while j < len(base[0]):
            group1_arr = []
            group2_arr = []

            # Go through each sample for this OTU
            i = 0
            while i < len(base):
                sample_id = sample_labels[i]
                metadata_val = sample_ids_to_metadata_map[sample_id]
                if metadata_val == catVar1:
                    group1_arr.append(float(base[i][j]))
                if metadata_val == catVar2:
                    group2_arr.append(float(base[i][j]))
                i += 1
            groups_abundance = {catVar1: group1_arr, catVar2: group2_arr}

            # Calculate the statistical p-value
            statistics = Statistics.getTtest(groups_abundance)
            otu_pvals.append(statistics[0]["pval"])

            j += 1

        otu_qvals = Statistics.getFDRCorrection(otu_pvals)

        otus = []

        j = 0
        while j < len(base[0]):
            otu_id = headers[j]
            pval = otu_pvals[j]
            qval = otu_qvals[j]
            if float(pval) < pvalthreshold:
                otu_results = {}
                otu_results["pval"] = pval
                otu_results["qval"] = qval
                otus.append({"otu": otu_id, "pval": pval, "qval": qval})
            j += 1

        return {"differentials": otus}
