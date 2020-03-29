# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#

import numpy as np
import rpy2.robjects as robjects
import rpy2.rlike.container as rlc
from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage
import rpy2.robjects.numpy2ri
from sklearn.model_selection import train_test_split

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
        taxonomy_map = table.get_otu_metadata().get_taxonomy_map()

        return self.analyse(user_request, otu_table, headers, metadata_values, taxonomy_map)

    def analyse(self, user_request, otuTable, headers, metaVals, taxonomy_map):
        # Subsample the input to match the training proportion
        # We do this because we want to generate the microbial fingerprint on the training set and
        # later independently test on a test set
        #
        fix_training = user_request.get_custom_attr("fixTraining") == "yes"
        existing_training_indexes = user_request.get_custom_attr("trainingIndexes")
        training_proportion = float(user_request.get_custom_attr("trainingProportion"))
        if fix_training and len(existing_training_indexes) > 0:
            existing_training_indexes = [int(i) for i in existing_training_indexes]
            training_indexes = np.array(existing_training_indexes)
        else:
            if training_proportion == 1:
                training_indexes = np.array(range(len(otuTable)))
            else:
                _, training_indexes = train_test_split(range(len(otuTable)), test_size=(1 - training_proportion))
        training_indexes = np.array(training_indexes)
        otuTable = otuTable[training_indexes, :]
        metaVals = [metaVals[i] for i in training_indexes]

        otu_to_genus = {}
        if int(user_request.level) == -1:
            # We want to display a short hint for the OTU using the genus (column 5)
            for header in headers:
                if header in taxonomy_map and len(taxonomy_map[header]) > 5:
                    otu_to_genus[header] = taxonomy_map[header][5]
                else:
                    otu_to_genus[header] = ""

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
        hints = {}

        i = 0
        for lab in borutaResults.iter_labels():
            if lab in assignments:
                assignments[lab].append(allOTUs[i][0])
            else:
                assignments[lab] = [allOTUs[i][0]]
            if int(user_request.level) == -1:
                hints[allOTUs[i][0]] = otu_to_genus[allOTUs[i][0]]
            i += 1

        abundancesObj = {}
        abundancesObj["results"] = assignments
        abundancesObj["hints"] = hints
        abundancesObj["training_indexes"] = training_indexes.tolist()

        return abundancesObj
