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
        otu_table = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(
            user_request.taxonomy_filter,
            user_request.taxonomy_filter_role,
            user_request.taxonomy_filter_vals,
            user_request.sample_filter,
            user_request.sample_filter_role,
            user_request.sample_filter_vals,
            user_request.level)

        sample_ids_to_metadata_map = table.get_sample_metadata().get_sample_id_to_metadata_map(user_request.catvar)

        return self.analyse(user_request, otu_table, sample_ids_to_metadata_map)

    def analyse(self, user_request, base, sample_ids_to_metadata_map):
        pvalthreshold = float(user_request.get_custom_attr("pvalthreshold"))
        catVar1 = user_request.get_custom_attr("pwVar1")
        catVar2 = user_request.get_custom_attr("pwVar2")

        # Perform differential analysis between two groups

        logger.info("Starting differential analysis")
        otu_pvals = []

        j = OTUTable.OTU_START_COL
        while j < len(base[0]):
            logger.info("Running t-test for " + str(j))
            group1_arr = []
            group2_arr = []

            # Go through each sample for this OTU
            i = 1
            while i < len(base):
                sample_id = base[i][OTUTable.SAMPLE_ID_COL]
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

        j = OTUTable.OTU_START_COL
        while j < len(base[0]):
            otu_id = base[0][j]
            # TODO: Do some assertions on this
            pval = otu_pvals[j - OTUTable.OTU_START_COL]
            qval = otu_qvals[j - OTUTable.OTU_START_COL]
            if float(pval) < pvalthreshold:
                otu_results = {}
                otu_results["pval"] = pval
                otu_results["qval"] = qval
                otus.append({"otu": otu_id, "pval": pval, "qval": qval})
            j += 1

        return {"differentials": otus}
