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
import rpy2.robjects.numpy2ri
rpy2.robjects.numpy2ri.activate()

from mian.model.otu_table import OTUTable

class Boruta(object):
    r = robjects.r

    rcode = """
    
    library(Boruta)

    boruta <- function(base, groups, pval, maxruns) {
        y.1 = as.factor(groups)
        b <- Boruta(base, y.1, doTrace=0, holdHistory=FALSE, pValue=pval, maxRuns=maxruns)
        return (b$finalDecision)
    }
    """

    rStats = SignatureTranslatedAnonymousPackage(rcode, "rStats")

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        metadata_values = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.catvar)

        return self.analyse(user_request, otu_table, headers, metadata_values)

    def analyse(self, user_request, otuTable, headers, metaVals):
        groups = robjects.FactorVector(robjects.StrVector(metaVals))

        allOTUs = []
        col = 0
        while col < len(otuTable[0]):
            allOTUs.append((headers[col], otuTable[:, col]))
            col += 1

        od = rlc.OrdDict(allOTUs)
        dataf = robjects.DataFrame(od)

        pval = user_request.get_custom_attr("pval")
        maxruns = user_request.get_custom_attr("maxruns")

        borutaResults = self.rStats.boruta(dataf, groups, float(pval), int(maxruns))

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

