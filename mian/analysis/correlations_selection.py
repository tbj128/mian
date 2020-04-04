# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================
import pandas as pd
from scipy import stats, math
import numpy as np
from sklearn.model_selection import train_test_split

from mian.analysis.alpha_diversity import AlphaDiversity
from mian.analysis.analysis_base import AnalysisBase
from mian.core.statistics import Statistics
from mian.model.otu_table import OTUTable
from mian.model.genes import Genes
from mian.model.metadata import Metadata
from mian.model.user_request import UserRequest


class CorrelationsSelection(AnalysisBase):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        table.load_phylogenetic_tree_if_exists()
        metadata = table.get_sample_metadata()
        otu_metadata = table.get_otu_metadata()
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)
        phylogenetic_tree = table.get_phylogenetic_tree()

        self.table = table

        return self.analyse(user_request, otu_table, headers, sample_labels, metadata, otu_metadata, phylogenetic_tree)

    def analyse(self, user_request, otu_table, headers, sample_labels, metadata, otu_metadata, phylogenetic_tree):
        select = user_request.get_custom_attr("select")
        against = user_request.get_custom_attr("against")
        expvar = user_request.get_custom_attr("expvar")
        pvalthreshold = user_request.get_custom_attr("pvalthreshold")

        fix_training = user_request.get_custom_attr("fixTraining") == "yes"
        existing_training_indexes = user_request.get_custom_attr("trainingIndexes")
        training_proportion = float(user_request.get_custom_attr("trainingProportion"))
        if fix_training and len(existing_training_indexes) > 0:
            existing_training_indexes = [int(i) for i in existing_training_indexes]
            training_indexes = np.array(existing_training_indexes)
        else:
            if training_proportion == 1:
                training_indexes = np.array(range(otu_table.shape[0]))
            else:
                training_indexes, _ = train_test_split(range(otu_table.shape[0]), test_size=(1 - training_proportion))
        training_indexes = np.array(training_indexes)
        otu_table = otu_table[training_indexes, :]
        sample_labels = np.array(sample_labels)[training_indexes]

        if expvar == "":
            return {"correlations": []}

        against_vals = []
        if against == "gene":
            genes = Genes(user_request.user_id, user_request.pid)
            gene_list = expvar.split(",")
            against_vals = genes.get_multi_gene_values(gene_list, sample_labels=sample_labels)
        elif against == "metadata":
            metadata_values = metadata.get_metadata_column_table_order(sample_labels, expvar)
            against_vals = list(map(float, metadata_values))
        elif against == "alpha":
            expvar_vals = expvar.split(",")
            alpha = AlphaDiversity()

            # We should only calculated the alpha diversity on an unfiltered OTU table
            unfiltered_user_request = UserRequest(user_request.user_id, user_request.pid, taxonomy_filter_count=0,
                                                  taxonomy_filter_prevalence=0, taxonomy_filter = -2,
                                                  taxonomy_filter_role="Include", taxonomy_filter_vals=[], sample_filter=user_request.sample_filter,
                                                  sample_filter_role=user_request.sample_filter_role,
                                                  sample_filter_vals=user_request.sample_filter_vals, level=user_request.level, catvar="")

            unfiltered_otu_table, unfiltered_headers, unfiltered_sample_labels = self.table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(unfiltered_user_request)
            unfiltered_otu_table = unfiltered_otu_table[training_indexes, :]
            unfiltered_sample_labels = np.array(unfiltered_sample_labels)[training_indexes]

            if int(user_request.level) == -1:
                # OTU tables are returned as a CSR matrix
                unfiltered_otu_table = pd.DataFrame.sparse.from_spmatrix(unfiltered_otu_table, columns=unfiltered_headers,
                                                              index=range(unfiltered_otu_table.shape[0]))

            against_vals = alpha.calculate_alpha_diversity(unfiltered_otu_table, unfiltered_sample_labels, unfiltered_headers, phylogenetic_tree, expvar_vals[1], expvar_vals[0])
        else:
            expvar_arr = expvar.split(",")
            relevant_cols = []
            c = 0
            for header in headers:
                if header in expvar_arr:
                    relevant_cols.append(c)
                c += 1
            r = 0
            while r < otu_table.shape[0]:
                total_row_sum = 0
                for c in relevant_cols:
                    total_row_sum += otu_table[r, c]
                against_vals.append(total_row_sum)
                r += 1

        taxonomy_map = otu_metadata.get_taxonomy_map()

        if select == "gene":
            abunObj = self.analyse_select_gene(user_request, sample_labels, against_vals, pvalthreshold)
        elif select == "metadata":
            abunObj = self.analyse_select_metadata(user_request, sample_labels, against_vals, pvalthreshold)
        else:
            abunObj = self.analyse_select_otu(user_request, otu_table, headers, against_vals, taxonomy_map, pvalthreshold)

        abunObj["training_indexes"] = training_indexes.tolist()
        return abunObj

    def analyse_select_gene(self, user_request, sample_labels, against_vals, pvalthreshold):
        genes = Genes(user_request.user_id, user_request.pid)
        gene_table, gene_list, gene_sample_labels = genes.get_as_table()

        sample_labels_map = {}
        for i, sample_label in enumerate(gene_sample_labels):
            sample_labels_map[sample_label] = i

        label_index_ordered = []
        for label in sample_labels:
            if label in gene_sample_labels:
                label_index_ordered.append(gene_sample_labels[label])
            else:
                label_index_ordered.append(-1)

        correlations = []
        pvals = []

        c = 0
        for gene in gene_list:
            gene_vals = []
            for r in label_index_ordered:
                if r == -1:
                    gene_vals.append(0)
                else:
                    gene_vals.append(float(gene_table[r, c]))
                r += 1

            coef, pval = stats.pearsonr(against_vals, gene_vals)
            if math.isnan(coef):
                coef = 0
            if math.isnan(pval):
                pval = 1
            correlations.append({"otu": gene, "coef": coef, "pval": pval})
            if len(correlations) > 100:
                break
            pvals.append(pval)
            c += 1

        qvals = Statistics.getFDRCorrection(pvals)

        correlations_retval = []
        i = 0
        while i < len(qvals):
            if correlations[i]["pval"] <= float(pvalthreshold):
                correlations[i]["qval"] = qvals[i]
                correlations_retval.append(correlations[i])
            i += 1

        return {"correlations": correlations_retval}

    def analyse_select_metadata(self, user_request, sample_labels, against_vals, pvalthreshold):
        metadata = Metadata(user_request.user_id, user_request.pid)
        metadata_table, metadata_headers, _ = metadata.get_as_table_in_table_order(sample_labels)

        correlations = []
        pvals = []

        c = 0
        while c < len(metadata_headers):
            metadata = metadata_headers[c]
            metadata_vals = []
            is_numeric = True
            r = 0
            while r < len(metadata_table):
                if not metadata_table[r][c].isnumeric():
                    is_numeric = False
                    break
                metadata_vals.append(float(metadata_table[r][c]))
                r += 1

            if is_numeric:
                coef, pval = stats.pearsonr(against_vals, metadata_vals)
                if math.isnan(coef):
                    coef = 0
                if math.isnan(pval):
                    pval = 1
                correlations.append({"otu": metadata, "coef": coef, "pval": pval})
                pvals.append(pval)
            c += 1

        qvals = Statistics.getFDRCorrection(pvals)

        correlations_retval = []
        i = 0
        while i < len(qvals):
            if correlations[i]["pval"] <= float(pvalthreshold):
                correlations[i]["qval"] = qvals[i]
                correlations_retval.append(correlations[i])
            i += 1

        return {"correlations": correlations_retval}

    def analyse_select_otu(self, user_request, base, headers, metadata_values, taxonomy_map, pvalthreshold):
        otu_to_genus = {}
        if int(user_request.level) == -1:
            # We want to display a short hint for the OTU using the genus (column 5)
            for header in headers:
                if header in taxonomy_map and len(taxonomy_map[header]) > 5:
                    otu_to_genus[header] = taxonomy_map[header][5]
                else:
                    otu_to_genus[header] = ""

        correlations = []
        pvals = []

        c = 0
        while c < base.shape[1]:
            otu_name = headers[c]
            otu_vals = []
            r = 0
            while r < base.shape[0]:
                otu_vals.append(base[r, c])
                r += 1

            coef, pval = stats.pearsonr(metadata_values, otu_vals)
            if math.isnan(coef):
                coef = 0
            if math.isnan(pval):
                pval = 1

            if int(user_request.level) == -1 and otu_name in otu_to_genus:
                correlations.append({"otu": otu_name, "coef": coef, "pval": pval, "hint": otu_to_genus[otu_name]})
            else:
                correlations.append({"otu": otu_name, "coef": coef, "pval": pval})
            pvals.append(pval)

            c += 1

        qvals = Statistics.getFDRCorrection(pvals)

        correlations_retval = []
        i = 0
        while i < len(qvals):
            if correlations[i]["pval"] <= float(pvalthreshold):
                correlations[i]["qval"] = qvals[i]
                correlations_retval.append(correlations[i])
            i += 1

        return {"correlations": correlations_retval}
