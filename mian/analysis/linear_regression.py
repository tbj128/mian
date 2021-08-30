# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, SGDRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split, KFold

from mian.model.otu_table import OTUTable
import numpy as np
import random


class LinearRegression(object):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        expvar = user_request.get_custom_attr("expvar")
        metadata_vals = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, expvar)

        return self.analyse(user_request, otu_table, headers, metadata_vals)

    def analyse(self, user_request, otu_table, headers, metadata_vals):
        cross_validate_set = user_request.get_custom_attr("crossValidate")
        cross_validate_folds = int(user_request.get_custom_attr("crossValidateFolds"))
        fix_training = user_request.get_custom_attr("fixTraining")
        training_proportion = user_request.get_custom_attr("trainingProportion")
        seed = int(user_request.get_custom_attr("seed")) if user_request.get_custom_attr("seed") is not "" else random.randint(0, 100000)
        mixing_ratio = float(user_request.get_custom_attr("mixingRatio"))
        max_iterations = int(user_request.get_custom_attr("maxIterations"))

        if int(user_request.level) == -1:
            # OTU tables are returned as a CSR matrix
            X = pd.DataFrame.sparse.from_spmatrix(otu_table, columns=headers, index=range(otu_table.shape[0]))
        else:
            X = otu_table

        Y = np.array(metadata_vals)

        def performCrossValidationForAUC(X_cv, metadata_vals_cv, Y_cv):
            cv = KFold(n_splits=cross_validate_folds)

            classifier = ElasticNet(l1_ratio=mixing_ratio, max_iter=max_iterations)

            test_maes = []
            test_mses = []

            for i, (train, test) in enumerate(cv.split(X_cv, metadata_vals_cv)):
                classifier.fit(X_cv[X_cv.index.isin(train)], Y_cv[train])
                preds = classifier.predict(X_cv[X_cv.index.isin(test)])
                test_mae = mean_absolute_error(Y_cv[test].astype(float), preds)
                test_mse = mean_squared_error(Y_cv[test].astype(float), preds)
                test_maes.append(test_mae)
                test_mses.append(test_mse)

            cv_obj = {
                "cv_mae": np.array(test_maes).mean(),
                "cv_mae_std": np.array(test_maes).std(),
                "cv_mse": np.array(test_mses).mean(),
                "cv_mse_std": np.array(test_mses).std()
            }
            return cv_obj

        if cross_validate_set == "full":
            cv_obj = performCrossValidationForAUC(X, metadata_vals, Y)
            return {
                "cv_mae": round(cv_obj["cv_mae"], 2),
                "cv_mae_std": round(cv_obj["cv_mae_std"], 2),
                "cv_mse": round(cv_obj["cv_mse"], 2),
                "cv_mse_std": round(cv_obj["cv_mse_std"], 2)
            }
        else:
            if fix_training == "yes":
                X_train, X_test, y_train, y_test = train_test_split(X, Y, train_size=training_proportion, random_state=seed)
                X_val, X_test, y_val, y_test = train_test_split(X_test, y_test, train_size=0.5, random_state=seed)
            else:
                # Use a random seed each time (not recommended)
                X_train, X_test, y_train, y_test = train_test_split(X, Y, train_size=training_proportion)
                X_val, X_test, y_val, y_test = train_test_split(X_test, y_test, train_size=0.5)

            imp_mean = SimpleImputer(missing_values=np.nan, strategy='mean')
            X_train = imp_mean.fit_transform(X_train)
            X_val = imp_mean.transform(X_val)
            X_test = imp_mean.transform(X_test)

            classifier = ElasticNet(l1_ratio=mixing_ratio, fit_intercept=True, max_iter=max_iterations)
            classifier.fit(X_train, y_train)
            preds_train = classifier.predict(X_train)
            train_mae = mean_absolute_error(y_train.astype(float), preds_train)
            train_mse = mean_squared_error(y_train.astype(float), preds_train)

            preds_val = classifier.predict(X_val)
            val_mae = mean_absolute_error(y_val.astype(float), preds_val)
            val_mse = mean_squared_error(y_val.astype(float), preds_val)

            preds_test = classifier.predict(X_test)
            test_mae = mean_absolute_error(y_test.astype(float), preds_test)
            test_mse = mean_squared_error(y_test.astype(float), preds_test)

            abundances_obj = {
                "train_mae": round(train_mae, 2),
                "train_mse": round(train_mse, 2),
                "val_mae": round(val_mae, 2),
                "val_mse": round(val_mse, 2),
                "test_mae": round(test_mae, 2),
                "test_mse": round(test_mse, 2),
                "train_size": X_train.shape,
                "val_size": X_val.shape,
                "test_size": X_test.shape,
                "seed": seed
            }

            return abundances_obj
