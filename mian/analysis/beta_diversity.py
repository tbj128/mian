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
    
        mod <- betadisper(Habc, groups)
        distances = mod$distances
        return(distances)
    }
    
    betaDiversityPERMANOVA <- function(allOTUs, groups, strata) {
        return(adonis(allOTUs~groups, strata=strata))
    }
    
    betaDiversityPERMANOVA2 <- function(allOTUs, groups) {
        return(adonis(allOTUs~groups))
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
        otu_table = table.get_table_after_filtering_and_aggregation(user_request.taxonomy_filter,
                                                                    user_request.taxonomy_filter_role,
                                                                    user_request.taxonomy_filter_vals,
                                                                    user_request.sample_filter,
                                                                    user_request.sample_filter_role,
                                                                    user_request.sample_filter_vals,
                                                                    user_request.level)

        metadata_values = table.get_sample_metadata().get_metadata_column_table_order(otu_table, user_request.catvar)
        sample_ids_to_metadata_map = table.get_sample_metadata().get_sample_id_to_metadata_map(user_request.catvar)

        # =====================================================================
        # TODO: FIX
        #
        # table.get_sample_metadata().get_metadata_column_table_order(TBD)
        # metaVals2 = Metadata.get_metadata_in_otu_table_order(otuTable, otuMetadata,
        #                                                      Metadata.get_cat_col(otuMetadata, "Individual"))
        #
        # strata = robjects.FactorVector(robjects.StrVector(metaVals2))
        #
        # TODO: FIX
        # =====================================================================

        return self.analyse(user_request, otu_table, metadata_values, sample_ids_to_metadata_map)

    def analyse(self, user_request, otu_table, metadata_values, sample_ids_from_metadata):
        groups = robjects.FactorVector(robjects.StrVector(metadata_values))

        # Forms an OTU only table (without IDs)
        allOTUs = []
        col = OTUTable.OTU_START_COL
        while col < len(otu_table[0]):
            colVals = []
            row = 1
            while row < len(otu_table):
                sampleID = otu_table[row][OTUTable.SAMPLE_ID_COL]
                if sampleID in sample_ids_from_metadata:
                    colVals.append(otu_table[row][col])
                row += 1
            allOTUs.append((otu_table[0][col], robjects.FloatVector(colVals)))
            col += 1

        od = rlc.OrdDict(allOTUs)
        dataf = robjects.DataFrame(od)

        betaType = user_request.get_custom_attr("betaType")

        # See: http://stackoverflow.com/questions/35410860/permanova-multivariate-spread-among-groups-is-not-similar-to-variance-homogeneit
        vals = self.veganR.betaDiversity(dataf, groups, betaType)

        # Calculate the statistical p-value
        abundances = {}
        statsAbundances = {}
        i = 0
        while i < len(vals):
            obj = {}
            obj["s"] = str(otu_table[i + 1][OTUTable.SAMPLE_ID_COL]) # the values don't include the header, but the OTU table does
            obj["a"] = round(vals[i], 6)

            if metadata_values[i] in statsAbundances:
                statsAbundances[metadata_values[i]].append(vals[i])
                abundances[metadata_values[i]].append(obj)
            else:
                statsAbundances[metadata_values[i]] = [vals[i]]
                abundances[metadata_values[i]] = [obj]

            i += 1

        statistics = Statistics.getTtest(statsAbundances)

        abundancesObj = {}
        abundancesObj["abundances"] = abundances
        abundancesObj["stats"] = statistics

        # permanova = veganR.betaDiversityPERMANOVA(dataf, groups, strata)
        permanova = self.veganR.betaDiversityPERMANOVA2(dataf, groups)
        # print strata
        # print permanova
        # print permanova2
        dispersions = self.veganR.betaDiversityDisper(dataf, groups, betaType)
        abundancesObj["permanova"] = str(permanova)
        abundancesObj["dispersions"] = str(dispersions)

        return abundancesObj
