# ===========================================
# 
# mian Analysis Alpha/Beta Diversity Library
# @author: tbj128
#
# ===========================================

#
# ======== R specific setup =========
#

import rpy2.robjects as robjects
import rpy2.rlike.container as rlc
from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage

from mian.analysis.analysis_base import AnalysisBase
from mian.core.statistics import Statistics

from mian.model.otu_table import OTUTable


class BetaDiversity(AnalysisBase):
    r = robjects.r

    #
    # ======== Main code begins =========
    #

    rcode = """
    
    betaDiversity <- function(allOTUs, groups, method) {
        if (method == "bray") {
            Habc = vegdist(allOTUs, method=method)
    
            mod <- betadisper(Habc, groups)
            distances = mod$distances
            return(distances)
        } else {
            abc <- betadiver(allOTUs, method=method)
            Habc = abc
            if (method == "sor") {
                Habc = 1 - abc
            }
    
            mod <- betadisper(Habc, groups)
            distances = mod$distances
            return(distances)
        }
    }
    
    betaDiversityPERMANOVA <- function(allOTUs, groups) {
        # Note, you can also pass in the data arg and specify the actual feature name instead of passing the array directly in as groups
        return(adonis(allOTUs~groups))
    }

    betaDiversityPERMANOVAWithStrata <- function(allOTUs, groups, strata) {
        return(adonis(allOTUs~groups, strata=strata))
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
        table = OTUTable(user_request.user_id, user_request.pid)

        # No OTUs should be excluded for diversity analysis
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation(user_request)

        metadata_values = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.catvar)

        strata_values = None
        if user_request.get_custom_attr("strata").lower() != "none":
            strata_values = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.get_custom_attr("strata"))

        sample_ids_to_metadata_map = table.get_sample_metadata().get_sample_id_to_metadata_map(user_request.catvar)

        return self.analyse(user_request, otu_table, headers, sample_labels, metadata_values, strata_values, sample_ids_to_metadata_map)

    def analyse(self, user_request, otu_table, headers, sample_labels, metadata_values, strata_values, sample_ids_from_metadata):
        if len(metadata_values) == 0:
            raise ValueError("Beta diversity can only be used when there are at least two groups to compare between")

        groups = robjects.FactorVector(robjects.StrVector(metadata_values))

        # Forms an OTU only table (without IDs)
        allOTUs = []
        col = 0
        while col < len(otu_table[0]):
            colVals = []
            row = 0
            while row < len(otu_table):
                sampleID = sample_labels[row]
                if sampleID in sample_ids_from_metadata:
                    colVals.append(otu_table[row][col])
                row += 1
            allOTUs.append((headers[col], robjects.FloatVector(colVals)))
            col += 1

        od = rlc.OrdDict(allOTUs)
        dataf = robjects.DataFrame(od)

        betaType = user_request.get_custom_attr("betaType")

        # See: http://stackoverflow.com/questions/35410860/permanova-multivariate-spread-among-groups-is-not-similar-to-variance-homogeneit
        vals = self.veganR.betaDiversity(dataf, groups, betaType)

        # https://www.researchgate.net/post/What_can_I_infer_from_PERMANOVA_outputs_indicating_similarity_between_two_groups_but_the_PERMDISP2_outlining_differences_in_the_beta_diversity

        # Calculate the statistical p-value
        abundances = {}
        statsAbundances = {}
        i = 0
        while i < len(vals):
            obj = {}
            obj["s"] = sample_labels[i]
            obj["a"] = round(vals[i], 6)

            if metadata_values[i] in statsAbundances:
                statsAbundances[metadata_values[i]].append(vals[i])
                abundances[metadata_values[i]].append(obj)
            else:
                statsAbundances[metadata_values[i]] = [vals[i]]
                abundances[metadata_values[i]] = [obj]

            i += 1

        abundancesObj = {}
        abundancesObj["abundances"] = abundances

        if strata_values is None:
            permanova = self.veganR.betaDiversityPERMANOVA(dataf, groups)
        else:
            strata = robjects.FactorVector(robjects.StrVector(strata_values))
            permanova = self.veganR.betaDiversityPERMANOVAWithStrata(dataf, groups, strata)

        dispersions = self.veganR.betaDiversityDisper(dataf, groups, betaType)
        abundancesObj["permanova"] = str(permanova)
        abundancesObj["dispersions"] = str(dispersions)

        return abundancesObj
