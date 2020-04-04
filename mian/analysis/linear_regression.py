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
from sklearn.linear_model import ElasticNet, SGDRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split, StratifiedKFold, KFold
from sklearn.utils import shuffle

from mian.model.otu_table import OTUTable
from sklearn.preprocessing import LabelEncoder, normalize
import numpy as np


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
        existing_training_indexes = np.array(user_request.get_custom_attr("trainingIndexes"))
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
                "cv_mae": cv_obj["cv_mae"],
                "cv_mae_std": cv_obj["cv_mae_std"],
                "cv_mse": cv_obj["cv_mse"],
                "cv_mse_std": cv_obj["cv_mse_std"]
            }
        else:
            if fix_training == "yes" and len(existing_training_indexes) > 0:
                existing_training_indexes = np.array([int(i) for i in existing_training_indexes])
                X_train = X[X.index.isin(existing_training_indexes)]
                X_test = X[~X.index.isin(existing_training_indexes)]
                y_train = Y[X.index.isin(existing_training_indexes)]
                y_test = Y[~X.index.isin(existing_training_indexes)]
                ind_train = existing_training_indexes
                X_train, y_train = shuffle(X_train, y_train)
                X_test, y_test = shuffle(X_test, y_test)
            else:
                indices = np.arange(len(X))
                X_train, X_test, y_train, y_test, ind_train, ind_test = train_test_split(X, Y, indices,
                                                                                         train_size=training_proportion)

            X_train = normalize(X_train)
            X_test = normalize(X_test)

            train_mae = 0
            train_mse = 0
            test_mae = 0
            test_mse = 0
            scores_train = []
            scores_test = []
            classifier = SGDRegressor(l1_ratio=mixing_ratio, max_iter=max_iterations)
            epoch = 0
            while epoch < max_iterations:
                classifier.partial_fit(X_train, y_train)
                preds_train = classifier.predict(X_train)
                train_mae = mean_absolute_error(y_train.astype(float), preds_train)
                train_mse = mean_squared_error(y_train.astype(float), preds_train)

                preds_test = classifier.predict(X_test)
                test_mae = mean_absolute_error(y_test.astype(float), preds_test)
                test_mse = mean_squared_error(y_test.astype(float), preds_test)

                scores_train.append(train_mae)
                scores_test.append(test_mae)

                epoch += 1

            abundances_obj = {
                "train_mae": train_mae,
                "train_mse": train_mse,
                "test_mae": test_mae,
                "test_mse": test_mse,
                "scores_train": scores_train,
                "scores_test": scores_test,
                "training_indexes": ind_train.tolist()
            }

            return abundances_obj
