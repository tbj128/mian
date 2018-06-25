# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#

import rpy2.robjects as robjects
import rpy2.rlike.container as rlc
from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage

from mian.model.otu_table import OTUTable

class Boruta(object):
    r = robjects.r

    rcode = """
    
    library(Boruta)

    boruta <- function(base, groups, keepthreshold, pval, maxruns) {
        # Remove any OTUs with presence < keepthreshold (for efficiency)
        x = base[,colSums(base!=0)>=keepthreshold]
        y.1 = as.factor(groups)
        b <- Boruta(x, y.1, doTrace=0, holdHistory=FALSE, pValue=pval, maxRuns=maxruns)
        return (b$finalDecision)
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

        metadata_values = table.get_sample_metadata().get_metadata_column_table_order(otu_table, user_request.catvar)
        sample_ids_to_metadata_map = table.get_sample_metadata().get_sample_id_to_metadata_map(user_request.catvar)

        return self.analyse(user_request, otu_table, metadata_values, sample_ids_to_metadata_map)

    def analyse(self, user_request, otuTable, metaVals, metaIDs):
        groups = robjects.FactorVector(robjects.StrVector(metaVals))

        # Forms an OTU only table (without IDs)
        allOTUs = []
        col = OTUTable.OTU_START_COL
        while col < len(otuTable[0]):
            colVals = []
            row = 1
            while row < len(otuTable):
                sampleID = otuTable[row][OTUTable.SAMPLE_ID_COL]
                if sampleID in metaIDs:
                    colVals.append(otuTable[row][col])
                row += 1
            allOTUs.append((otuTable[0][col], robjects.FloatVector(colVals)))
            col += 1

        od = rlc.OrdDict(allOTUs)
        dataf = robjects.DataFrame(od)

        keepthreshold = user_request.get_custom_attr("keepthreshold")
        pval = user_request.get_custom_attr("pval")
        maxruns = user_request.get_custom_attr("maxruns")

        print("Boruta")

        borutaResults = self.rStats.boruta(dataf, groups, int(keepthreshold), float(pval), int(maxruns))

        assignments = {}

        i = 0
        for lab in borutaResults.iter_labels():
            if lab in assignments:
                assignments[lab].append(allOTUs[i][0])
            else:
                assignments[lab] = [allOTUs[i][0]]
            i += 1

        abundancesObj = {}
        abundancesObj["results"] = assignments

        return abundancesObj

