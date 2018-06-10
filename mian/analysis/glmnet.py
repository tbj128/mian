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


class GLMNet(object):
    r = robjects.r

    rcode = """
    library(glmnet)

    run_glmnet <- function(base, groups, keepthreshold, alphaVal, familyType, lambda_threshold_type, lambda_val) {
        # Remove any OTUs with presence < keepthreshold (for efficiency)
        x = base[,colSums(base!=0)>=keepthreshold]
        y.1 = as.factor(groups)
    
        # x = x[,2:ncol(x)];
        x <- as.matrix(data.frame(x))
        y <- as.factor(groups)
        yN = as.numeric(y)
        # y <- base[,SAV]
        cv <- cv.glmnet(x,y,alpha=alphaVal,family=familyType)
    
        # plot(cv,cex=2)
        if (lambda_threshold_type == "Custom") {
            scAll = coef(cv,s=exp(lambda_val))
        } else if (lambda_threshold_type == "lambda1se") {
            scAll = coef(cv,s=cv$lambda.1se)
        } else {
            scAll = coef(cv,s=cv$lambda.min)
        }
    
    
        uniqueGroups = unique(groups)
        if (familyType == "binomial") {
            results = matrix(,(length(scAll) - 1)*length(uniqueGroups), 3)
        } else {
            results = matrix(,(length(scAll[[uniqueGroups[1]]]) - 1)*length(uniqueGroups), 3)
        }
        index = 1
        for (g in 1:length(uniqueGroups)) {
            if (familyType == "binomial") {
                sc = scAll
            } else {
                sc = scAll[[uniqueGroups[g]]]
            }
    
            # Start at 2 to discount the intercept entry
            for (s in 2:length(sc)) {
                results[index, 1] = as.character(uniqueGroups[g])
                results[index, 2] = rownames(sc)[s]
                results[index, 3] = sc[s]
                index = index + 1
            }
        }
        return(results)
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

        metadata_vals = table.get_sample_metadata().get_metadata_column_table_order(otu_table, user_request.catvar)
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

        keepthreshold = user_request.get_custom_attr("keepthreshold")
        alphaVal = user_request.get_custom_attr("alpha")
        family = user_request.get_custom_attr("family")
        lambda_threshold_type = user_request.get_custom_attr("lambdathreshold")
        lambda_val = user_request.get_custom_attr("lambdaval")

        print("Analyse GLMNET")

        glmnetResult = self.rStats.run_glmnet(dataf, groups, int(keepthreshold), float(alphaVal), family,
                                              lambda_threshold_type, float(lambda_val))

        accumResults = {}
        i = 1
        while i <= glmnetResult.nrow:
            newRow = []
            newRow.append(glmnetResult.rx(i, 2)[0])
            newRow.append(round(float(glmnetResult.rx(i, 3)[0]), 6))

            g = glmnetResult.rx(i, 1)[0]
            if g in accumResults:
                accumResults[g].append(newRow)
            else:
                accumResults[g] = [newRow]

            i += 1

        abundancesObj = {}
        print(accumResults)
        abundancesObj["results"] = accumResults

        return abundancesObj

