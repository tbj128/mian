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

from mian.model.otu_table import OTUTable


class FisherExact(object):
    r = robjects.r

    rcode = """
    fisher_exact <- function(base, groups, cat2, cat1, minthreshold, keepthreshold) {
    
        base = base[,colSums(base!=0)>keepthreshold, drop=FALSE]
    
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
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table = table.get_table_after_filtering_and_aggregation(user_request.sample_filter,
                                                                    user_request.sample_filter_vals,
                                                                    user_request.taxonomy_filter_vals,
                                                                    user_request.taxonomy_filter)
        metadata_vals = table.get_sample_metadata().get_metadata_in_otu_table_order(user_request.catvar)
        sample_ids_to_metadata_map = table.get_sample_metadata().get_sample_id_to_metadata_map(user_request.catvar)

        return self.analyse(user_request, otu_table, metadata_vals, sample_ids_to_metadata_map)

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

        catVar1 = user_request.get_custom_attr("pwVar1")
        catVar2 = user_request.get_custom_attr("pwVar2")
        minthreshold = user_request.get_custom_attr("minthreshold")
        keepthreshold = user_request.get_custom_attr("keepthreshold")

        fisherResults = self.rStats.fisher_exact(dataf, groups, catVar1, catVar2, int(minthreshold), int(keepthreshold))

        results = []
        i = 1
        while i <= fisherResults.nrow:
            newRow = []
            j = 1
            while j <= fisherResults.ncol:
                if j > 1:
                    newRow.append(float(fisherResults.rx(i, j)[0]))
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

    # fisherExact("1", "BatchsubOTULevel", 1, ["Firmicutes","Fusobacteria"], "Disease", 0, 5)
