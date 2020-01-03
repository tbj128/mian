# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#
import math

#
# ======== R specific setup =========
#

import rpy2.robjects as robjects
import rpy2.rlike.container as rlc
from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage
import rpy2.robjects.numpy2ri
rpy2.robjects.numpy2ri.activate()

from mian.model.otu_table import OTUTable


### Update GLMNet descriptions, add additional family types
### Update tree description and check accuracy
### Elasticnet overcomes limitations of L1 regularization on its own, which can saturate with high-dimensional datasets


# GLMNet Usage Example
# Source: https://stackoverflow.com/questions/25206844/how-to-specify-log-link-in-glmnet
#
# # Generate data
# set.seed(1)
# x <- replicate(3,runif(1000))
# y <- exp(2*x[,1] + 3*x[,2] + x[,3] + runif(1000))
# df <- data.frame(y,x)
#
# # Recreate the model using a Gaussian with a log-link function (in GLMNet, this is usually an identity function, which makes it linear regression as opposed to logistic)
# glm(y~., family=gaussian(link="log"), data=df)$coef
# # (Intercept)          X1          X2          X3
# #   0.4977746   2.0449443   3.0812333   0.9451073
#
# # Creating the model using the identity function, two ways
# glm(log(y)~., family=gaussian(link='identity'), data=df)$coef
# # (Intercept)          X1          X2          X3
# #   0.4726745   2.0395798   3.0167274   0.9957110
# lm(log(y)~.,data=df)$coef
# # (Intercept)          X1          X2          X3
# #   0.4726745   2.0395798   3.0167274   0.9957110
#
# # Create model using Gaussian. Note that the original 'y' is no longer using exp function
# Remember that GLMNet is essentially GLM with regularization
# y <- 2*x[,1] + 3*x[,2] + x[,3] + runif(1000)
# library(glmnet)
# glmnet.model <- glmnet(x,y,family="gaussian", thresh=1e-8, lambda=0)
# c(glmnet.model$a0, glmnet.model$beta[,1])
# #        s0        V1        V2        V3
# # 0.4726745 2.0395798 3.0167274 0.9957110


class GLMNet(object):
    r = robjects.r

    rcode = """
    library(glmnet)

    run_glmnet <- function(base, groups, alphaVal, familyType, lambda_threshold_type) {
        x = base
        x <- as.matrix(data.frame(x))
        
        y = groups
        if (familyType == "multinomial") {
            y <- as.factor(groups)
        }
        
        # Use cross validation to find an appropriate value for the regularization parameter lambda
        cv <- cv.glmnet(x,y,alpha=alphaVal,family=familyType)
        lambda <- cv$lambda.min
        if (lambda_threshold_type == "lambda1se") {
            lambda <- cv$lambda.1se
        }
        
        # Use the lambda to get the actual model
        # Note: x is standardized by default but coefficients are returned on original scale
        glmnet.model <- glmnet(x,y,alpha=alphaVal,family=familyType,lambda=lambda)
        scAll = coef(glmnet.model)
        
        # Creates an empty matrix to use as the return value
        uniqueGroups = unique(groups)
        if (familyType == "binomial") {
            results = matrix(,(length(scAll) - 1)*length(uniqueGroups), 3)
        } else if (familyType == "multinomial") {
            results = matrix(,(length(scAll[[uniqueGroups[1]]]) - 1)*length(uniqueGroups), 3)
        } else {
            # Quantitative variables will not have categories
            results = matrix(,(length(scAll) - 1), 3)
        }
        
        index = 1
        if (familyType == "binomial" || familyType == "multinomial") {
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
        } else {
            sc = scAll

            # Start at 2 to discount the intercept entry
            for (s in 2:length(scAll)) {
                results[index, 1] = ""
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
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        expvar = user_request.get_custom_attr("expvar")
        metadata_vals = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, expvar)
        taxonomy_map = table.get_otu_metadata().get_taxonomy_map()

        return self.analyse(user_request, otu_table, headers, metadata_vals, taxonomy_map)

    def analyse(self, user_request, otuTable, headers, metadata_vals, taxonomy_map):
        otu_to_genus = {}
        if int(user_request.level) == -1:
            # We want to display a short hint for the OTU using the genus (column 5)
            for header in headers:
                if header in taxonomy_map and len(taxonomy_map[header]) > 5:
                    otu_to_genus[header] = taxonomy_map[header][5]
                else:
                    otu_to_genus[header] = ""

        allOTUs = []
        col = 0
        while col < len(otuTable[0]):
            allOTUs.append((headers[col], otuTable[:, col]))
            col += 1

        od = rlc.OrdDict(allOTUs)
        dataf = robjects.DataFrame(od)

        alphaVal = user_request.get_custom_attr("alpha")
        model = user_request.get_custom_attr("model")
        lambda_threshold_type = user_request.get_custom_attr("lambdathreshold")

        if model == "poisson":
            for val in metadata_vals:
                if val.isnumeric() and val < 0:
                    return {
                        "error": "Negative metadata values are not allowed for the Poisson model"
                    }

        groups = robjects.FactorVector(robjects.StrVector(metadata_vals)) if model == "multinomial" or model == "binomial" else robjects.FloatVector(metadata_vals)

        glmnetResult = self.rStats.run_glmnet(dataf, groups, float(alphaVal), model,
                                              lambda_threshold_type)

        hints = {}
        accumResults = {}
        i = 1
        while i <= glmnetResult.nrow:
            newRow = []
            newRow.append(glmnetResult.rx(i, 2)[0])
            if model == "multinomial" or model == "binomial":
                newRow.append(round(math.exp(float(glmnetResult.rx(i, 3)[0])), 6))
                # newRow.append(round(float(glmnetResult.rx(i, 3)[0]), 6))
            else:
                newRow.append(round(float(glmnetResult.rx(i, 3)[0]), 6))

            g = glmnetResult.rx(i, 1)[0]
            if g in accumResults:
                accumResults[g].append(newRow)
            else:
                accumResults[g] = [newRow]
            if int(user_request.level) == -1:
                hints[newRow[0]] = otu_to_genus[newRow[0]]

            i += 1

        abundancesObj = {}
        abundancesObj["results"] = accumResults
        abundancesObj["hints"] = hints

        return abundancesObj

