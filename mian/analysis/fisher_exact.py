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

import rpy2.robjects as robjects
import rpy2.rlike.container as rlc
from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage
import rpy2.robjects.numpy2ri
rpy2.robjects.numpy2ri.activate()

from mian.model.gene_table import GeneTable


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
            results[i,5] = totalSumCat2
            results[i,6] = fisherMatrix[2, 1]
            results[i,7] = totalSumCat1
        }
    
        results[,3] = p.adjust(results[,2], method = "fdr");
    
        # Sorts the table according to the (p-val) column
        results = results[order(results[,2]),]
    
        return(results)
    }

    """

    rStats = SignatureTranslatedAnonymousPackage(rcode, "rStats")

    def run(self, user_request):
        table = GeneTable(user_request.user_id, user_request.pid)
        otu_table, headers, sample_labels = table.get_table_after_filtering(user_request)

        metadata_vals = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.catvar)
        return self.analyse(user_request, otu_table, headers, metadata_vals)

    def analyse(self, user_request, otuTable, headers, metaVals):
        groups = robjects.FactorVector(robjects.StrVector(metaVals))
        # Forms an OTU only table (without IDs)
        allOTUs = []
        col = 0
        while col < len(otuTable[0]):
            allOTUs.append((headers[col], otuTable[:, col]))
            col += 1

        od = rlc.OrdDict(allOTUs)
        dataf = robjects.DataFrame(od)

        catVar1 = user_request.get_custom_attr("pwVar1")
        catVar2 = user_request.get_custom_attr("pwVar2")
        minthreshold = user_request.get_custom_attr("minthreshold")

        fisherResults = self.rStats.fisher_exact(dataf, groups, catVar1, catVar2, int(minthreshold))

        results = []
        i = 1
        while i <= fisherResults.nrow:
            newRow = []
            j = 1
            while j <= fisherResults.ncol:
                if j > 1:
                    newRow.append(round(float(fisherResults.rx(i, j)[0]), 6))
                else:
                    newRow.append(str(fisherResults.rx(i, j)[0]))
                j += 1
            i += 1
            results.append(newRow)

        cat1 = catVar1
        cat2 = catVar2
        abundancesObj = {}
        abundancesObj["results"] = results
        abundancesObj["cat1"] = cat1
        abundancesObj["cat2"] = cat2

        return abundancesObj
