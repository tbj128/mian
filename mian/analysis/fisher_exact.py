# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#

#
# ======== R specific setup =========
#
import numpy as np
import rpy2.robjects as robjects
import rpy2.rlike.container as rlc
from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage
import rpy2.robjects.numpy2ri
from sklearn.model_selection import train_test_split

rpy2.robjects.numpy2ri.activate()

from mian.model.otu_table import OTUTable
import random


class FisherExact(object):
    r = robjects.r

    rcode = """
    fisher_exact <- function(base, groups, cat2, cat1, minthreshold) {
    
        if (ncol(base) <= 0) {
            return(matrix(,0,7))
        }
    
        cat1OTUs = base[groups == cat1,, drop=FALSE];
        cat2OTUs = base[groups == cat2,, drop=FALSE];
    
        results = matrix(,ncol(cat1OTUs),7)
        results = data.frame(results)
        colnames(results) = c("P-Value", "Q-Value", "Cat1 Present", "Cat1 Total", "Cat2 Present", "Cat2 Total")
        rownames(results) = colnames(cat1OTUs)
    
        for (i in 1:ncol(cat1OTUs)) {
            fisherMatrix = matrix(,2,2);
            fisherMatrix[1, 1] = sum(cat2OTUs[,i] > minthreshold);
            fisherMatrix[1, 2] = sum(cat2OTUs[,i] <= minthreshold);
            fisherMatrix[2, 1] = sum(cat1OTUs[,i] > minthreshold);
            fisherMatrix[2, 2] = sum(cat1OTUs[,i] <= minthreshold);
            totalSumCat1 = fisherMatrix[2, 1] + fisherMatrix[2, 2]
            totalSumCat2 = fisherMatrix[1, 1] + fisherMatrix[1, 2]
    
            ftest = fisher.test(fisherMatrix);
    
            results[i,1] = colnames(cat1OTUs)[i]
            results[i,2] = ftest$p.value
            results[i,3] = 1
            results[i,4] = fisherMatrix[1, 1]
            results[i,5] = totalSumCat2 - fisherMatrix[1, 1]
            results[i,6] = fisherMatrix[2, 1]
            results[i,7] = totalSumCat1 - fisherMatrix[2, 1]
        }
    
        results[,3] = p.adjust(results[,2], method = "fdr");
    
        # Sorts the table according to the (p-val) column
        results = results[order(results[,2]),]
    
        return(results)
    }

    """

    rStats = SignatureTranslatedAnonymousPackage(rcode, "rStats")

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        metadata_vals = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.catvar)
        taxonomy_map = table.get_otu_metadata().get_taxonomy_map()
        return self.analyse(user_request, otu_table, headers, metadata_vals, taxonomy_map)

    def analyse(self, user_request, otuTable, headers, metaVals, taxonomy_map):
        otu_to_genus = {}
        if int(user_request.level) == -1:
            # We want to display a short hint for the OTU using the genus (column 5)
            for header in headers:
                if header in taxonomy_map and len(taxonomy_map[header]) > 5:
                    otu_to_genus[header] = taxonomy_map[header][5]
                else:
                    otu_to_genus[header] = ""

        seed = int(user_request.get_custom_attr("seed")) if user_request.get_custom_attr("seed") is not "" else random.randint(0, 100000)
        training_proportion = float(user_request.get_custom_attr("trainingProportion"))

        if training_proportion < 1:
            otuTable, _, metaVals, _ = train_test_split(otuTable, metaVals, train_size=training_proportion, random_state=seed)

        if int(user_request.level) == -1:
            # OTU tables are returned as a CSR matrix
            otuTable = otuTable.toarray()

        groups = robjects.FactorVector(robjects.StrVector(metaVals))
        # Forms an OTU only table (without IDs)
        allOTUs = []
        col = 0
        while col < otuTable.shape[1]:
            allOTUs.append((headers[col], otuTable[:, col]))
            col += 1

        od = rlc.OrdDict(allOTUs)
        dataf = robjects.DataFrame(od)

        catVar1 = user_request.get_custom_attr("pwVar1")
        catVar2 = user_request.get_custom_attr("pwVar2")
        minthreshold = user_request.get_custom_attr("minthreshold")
        pvalthreshold = float(user_request.get_custom_attr("pvalthreshold"))

        fisherResults = self.rStats.fisher_exact(dataf, groups, catVar1, catVar2, int(minthreshold))

        hints = {}
        results = []
        i = 0
        while i < fisherResults.size:
            newRow = []
            j = 0
            while j < len(fisherResults[i]):
                if j > 0:
                    newRow.append(round(float(fisherResults[i][j]), 6))
                else:
                    newRow.append(str(fisherResults[i][j]))
                j += 1
            otu = newRow[0]

            if int(user_request.level) == -1:
                hints[otu] = otu_to_genus[otu]
            i += 1

            if float(newRow[1]) < pvalthreshold:
                results.append(newRow)

        cat1 = catVar1
        cat2 = catVar2
        abundancesObj = {}
        abundancesObj["results"] = results
        abundancesObj["hints"] = hints
        abundancesObj["cat1"] = cat1
        abundancesObj["cat2"] = cat2
        abundancesObj["seed"] = seed

        return abundancesObj
