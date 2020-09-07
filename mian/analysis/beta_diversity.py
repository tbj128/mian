# ===========================================
# 
# mian Analysis Alpha/Beta Diversity Library
# @author: tbj128
#
# ===========================================

#
# ======== R specific setup =========
#
from functools import partial

import pandas as pd
import rpy2.robjects as robjects
import rpy2.rlike.container as rlc
from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage
from scipy.spatial.distance import cdist
from scipy.stats import stats
from skbio import TreeNode
from skbio.diversity import beta_diversity
from io import StringIO

from skbio.stats.distance import permdisp
from skbio.stats.distance._base import _preprocess_input, _run_monte_carlo_stats, _build_results
from skbio.stats.distance._permdisp import _compute_groups
from skbio.stats.ordination import pcoa

from mian.analysis.analysis_base import AnalysisBase

from mian.model.otu_table import OTUTable
from mian.model.map import Map


class BetaDiversity(AnalysisBase):
    r = robjects.r

    #
    # ======== Main code begins =========
    #

    rcode = """
    betaDiversityFromDistanceMatrix <- function(Habc, groups) {
        dm <- as.dist(Habc)
        mod <- betadisper(dm, groups)
        distances = mod$distances
        return(distances)
    }
    
    betaDiversity <- function(allOTUs, groups, method) {
        if (method == "bray") {
            Habc = vegdist(allOTUs, method=method)
    
            mod <- betadisper(Habc, groups)
            distances = mod$distances
            
            return(list(distances, anova(mod)))
        } else {
            abc <- betadiver(allOTUs, method=method)
            Habc = abc
            if (method == "sor") {
                Habc = 1 - abc
            }
    
            mod <- betadisper(Habc, groups)
            distances = mod$distances
            return(list(distances, anova(mod)))
        }
    }
    
    betaDiversityPERMANOVA <- function(allOTUs, groups, permutations) {
        # Note, you can also pass in the data arg and specify the actual feature name instead of passing the array directly in as groups
        return(adonis(allOTUs~groups, permutations=permutations))
    }

    betaDiversityPERMANOVAWithStrata <- function(allOTUs, groups, strata, permutations) {
        return(adonis(allOTUs~groups, strata=strata, permutations=permutations))
    }
    
    betaDiversityDisper <- function(allOTUs, groups, method) {
        if (method == "bray") {
            Habc = vegdist(allOTUs, method=method)
    
            # TODO: Use bias adjust?
            mod <- betadisper(Habc, groups)
            return(anova(mod))
        } else {
            abc <- betadiver(allOTUs, method=method)
            Habc = abc
            if (method == "sor") {
                Habc = 1 - abc
            }
    
            # TODO: Use bias adjust?
            mod <- betadisper(Habc, groups)
            return(anova(mod))
        }
    }
    
    """

    veganR = SignatureTranslatedAnonymousPackage(rcode, "veganR")

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid, use_sparse=True)
        table.load_phylogenetic_tree_if_exists()

        # No OTUs should be excluded for diversity analysis
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        metadata_values = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.catvar)
        if user_request.get_custom_attr("colorvar") != "None":
            color_metadata_values = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.get_custom_attr("colorvar"))
        else:
            color_metadata_values = []

        strata_values = None
        if user_request.get_custom_attr("strata").lower() != "none":
            strata_values = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.get_custom_attr("strata"))

        phylogenetic_tree = table.get_phylogenetic_tree()

        if user_request.get_custom_attr("api").lower() == "beta":
            return self.analyse(user_request, otu_table, headers, sample_labels, metadata_values, color_metadata_values, phylogenetic_tree)
        else:
            return self.analyse_permanova(user_request, otu_table, headers, metadata_values, strata_values)

    def analyse(self, user_request, otu_table, headers, sample_labels, metadata_values, color_metadata_values, phylogenetic_tree):
        if len(metadata_values) == 0:
            raise ValueError("Beta diversity can only be used when there are at least two groups to compare between")

        print("Starting Beta Diversity Analysis")

        betaType = user_request.get_custom_attr("betaType")
        numPermutations = int(user_request.get_custom_attr("numPermutations"))

        if int(user_request.level) == -1:
            # OTU tables are returned as a CSR matrix
            otu_table = pd.DataFrame.sparse.from_spmatrix(otu_table, columns=headers, index=range(otu_table.shape[0]))

        if (betaType == "weighted_unifrac" or betaType == "unweighted_unifrac") and phylogenetic_tree == "":
            return {
                "no_tree": True
            }

        project_map = Map(user_request.user_id, user_request.pid)
        if project_map.matrix_type == "float":
            return {
                "has_float": True
            }

        sample_id_to_index = {}
        for i in range(len(sample_labels)):
            sample_id_to_index[sample_labels[i]] = i

        if betaType == "weighted_unifrac" or betaType == "unweighted_unifrac":
            tree = TreeNode.read(StringIO(phylogenetic_tree))
            if len(tree.root().children) > 2:
                # Ensure that the tree is rooted if it is not already rooted
                tree = tree.root_at_midpoint()
            dist_matrix = beta_diversity(betaType, otu_table, ids=sample_labels, otu_ids=headers, tree=tree)
        else:
            dist_matrix = beta_diversity(betaType, otu_table, ids=sample_labels)

        ordination = pcoa(dist_matrix)
        samples = ordination.samples

        # Copied from the actual _permdisp method to avoid running pcoa twice
        sample_size, num_groups, grouping, tri_idxs, distances = _preprocess_input(
            dist_matrix, metadata_values, None)
        test_stat_function = partial(_compute_groups, samples, 'centroid')
        stat, p_value = _run_monte_carlo_stats(test_stat_function, grouping, permutations=numPermutations)
        permdisp_out = _build_results('PERMDISP', 'F-value', sample_size, num_groups,
                              stat, p_value, permutations=numPermutations)

        samples['grouping'] = metadata_values
        centroids = samples.groupby('grouping').aggregate('mean')

        abundances = {}
        for label, df in samples.groupby('grouping'):
            distances = cdist(df.values[:, :-1], [centroids.loc[label].values], metric='euclidean')
            for k in range(len(distances)):
                sample_id = df.index[k]
                sample_index = sample_id_to_index[sample_id]
                obj = {
                    "s": sample_labels[sample_index],
                    "a": round(distances[k, 0].item(), 6),
                    "color": color_metadata_values[sample_index] if len(color_metadata_values) > 0 else ""
                }

                if label in abundances:
                    abundances[label].append(obj)
                else:
                    abundances[label] = [obj]

        # https://www.researchgate.net/post/What_can_I_infer_from_PERMANOVA_outputs_indicating_similarity_between_two_groups_but_the_PERMDISP2_outlining_differences_in_the_beta_diversity
        return {
            "abundances": abundances,
            "dispersions": str(permdisp_out)
        }

    def analyse_permanova(self, user_request, otu_table, headers, metadata_values, strata_values):

        numPermutations = int(user_request.get_custom_attr("numPermutations"))

        if int(user_request.level) == -1:
            # OTU tables are returned as a CSR matrix
            otu_table = otu_table.toarray()

        print("Starting PERMANOVA")
        groups = robjects.FactorVector(robjects.StrVector(metadata_values))

        # Forms an OTU only table (without IDs)
        allOTUs = []
        col = 0
        while col < otu_table.shape[1]:
            colVals = []
            row = 0
            while row < otu_table.shape[0]:
                colVals.append(otu_table[row, col])
                row += 1
            allOTUs.append((headers[col], robjects.FloatVector(colVals)))
            col += 1

        od = rlc.OrdDict(allOTUs)
        dataf = robjects.DataFrame(od)

        if strata_values is None:
            permanova = self.veganR.betaDiversityPERMANOVA(dataf, groups, numPermutations)
        else:
            strata = robjects.FactorVector(robjects.StrVector(strata_values))
            permanova = self.veganR.betaDiversityPERMANOVAWithStrata(dataf, groups, strata, numPermutations)
        abundancesObj = {}
        abundancesObj["permanova"] = str(permanova)

        return abundancesObj
