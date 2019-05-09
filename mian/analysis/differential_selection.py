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
from skbio.stats.composition import ancom
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


class DifferentialSelection(object):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)

        differential_type = user_request.get_custom_attr("type")

        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(
            user_request)

        sample_ids_to_metadata_map = table.get_sample_metadata().get_sample_id_to_metadata_map(user_request.catvar)
        taxonomy_map = table.get_otu_metadata().get_taxonomy_map()

        if differential_type == "ANCOM":
            logger.info("Running ANCOM")
            return self.analyse_with_ancom(user_request, otu_table, headers, sample_labels, sample_ids_to_metadata_map, taxonomy_map)
        else:
            return self.analyse(user_request, otu_table, headers, sample_labels, sample_ids_to_metadata_map, taxonomy_map)

    def analyse(self, user_request, base, headers, sample_labels, sample_ids_to_metadata_map, taxonomy_map):
        otu_to_genus = {}
        if int(user_request.level) == -1:
            # We want to display a short hint for the OTU using the genus (column 5)
            for header in headers:
                if header in taxonomy_map and len(taxonomy_map[header]) > 5:
                    otu_to_genus[header] = taxonomy_map[header][5]
                else:
                    otu_to_genus[header] = ""

        pvalthreshold = float(user_request.get_custom_attr("pvalthreshold"))
        catVar1 = user_request.get_custom_attr("pwVar1")
        catVar2 = user_request.get_custom_attr("pwVar2")
        statistical_test = user_request.get_custom_attr("type")
        logger.info("Running statistical test " + statistical_test)

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
            statistics = Statistics.getTtest(groups_abundance, statistical_test)
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
                if int(user_request.level) == -1 and otu_id in otu_to_genus:
                    otus.append({"otu": otu_id, "pval": pval, "qval": qval, "hint": otu_to_genus[otu_id]})
                else:
                    otus.append({"otu": otu_id, "pval": pval, "qval": qval})
            j += 1

        return {"differentials": otus}

    def analyse_with_ancom(self, user_request, base, headers, sample_labels, sample_ids_to_metadata_map, taxonomy_map):
        otu_to_genus = {}
        if int(user_request.level) == -1:
            # We want to display a short hint for the OTU using the genus (column 5)
            for header in headers:
                if header in taxonomy_map and len(taxonomy_map[header]) > 5:
                    otu_to_genus[header] = taxonomy_map[header][5]
                else:
                    otu_to_genus[header] = ""

        pvalthreshold = float(user_request.get_custom_attr("pvalthreshold"))
        catVar1 = user_request.get_custom_attr("pwVar1")
        catVar2 = user_request.get_custom_attr("pwVar2")

        # Remove non-relevant base rows
        relevant_rows = {}
        new_sample_labels = []
        row_groups = []
        i = 0
        while i < len(sample_labels):
            sample_id = sample_labels[i]
            if sample_ids_to_metadata_map[sample_id] == catVar1 or sample_ids_to_metadata_map[sample_id] == catVar2:
                relevant_rows[i] = True
                new_sample_labels.append(sample_id)
                row_groups.append(sample_ids_to_metadata_map[sample_id])
            i += 1

        new_base = []
        i = 0
        while i < len(base):
            if relevant_rows[i]:
                new_row = []
                j = 0
                while j < len(base[i]):
                    if float(base[i][j]) > 0:
                        new_row.append(float(base[i][j]))
                    else:
                        # Use pseudocount as ANCOM does not accept zeros or negatives
                        new_row.append(0.001)
                    j += 1
                new_base.append(new_row)
            i += 1

        table = pd.DataFrame(new_base, index=new_sample_labels, columns=headers)
        grouping = pd.Series(row_groups, index=new_sample_labels)

        results = ancom(table, grouping, alpha=pvalthreshold)
        results_rejects = results[0]["Reject null hypothesis"].tolist()
        otus = []
        i = 0
        while i < len(headers):
            if results_rejects[i]:
                if int(user_request.level) == -1 and headers[i] in otu_to_genus:
                    otus.append({"otu": headers[i], "pval": "< " + str(pvalthreshold), "qval": "N/A for ANCOM", "hint": otu_to_genus[headers[i]]})
                else:
                    otus.append({"otu": headers[i], "pval": "< " + str(pvalthreshold), "qval": "N/A for ANCOM"})
            i += 1
        return {"differentials": otus}