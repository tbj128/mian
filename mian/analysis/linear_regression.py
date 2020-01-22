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
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split, StratifiedKFold, KFold
from sklearn.utils import shuffle

from mian.model.otu_table import OTUTable
from sklearn.preprocessing import LabelEncoder
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

        # NORMALIZE THE DATASET
        df = pd.DataFrame(data=otu_table, columns=headers, index=range(len(otu_table)))
        stats = df.describe()
        stats = stats.transpose()

        def norm(x):
            return (x - stats['mean']) / stats['std']

        X = norm(df)
        Y = np.array(metadata_vals)

        def performCrossValidationForAUC(X_cv, metadata_vals_cv, Y_cv):
            cv = KFold(n_splits=cross_validate_folds)

            classifier = ElasticNet(l1_ratio=mixing_ratio, max_iter=max_iterations)

            train_maes = []
            train_mses = []
            test_maes = []
            test_mses = []

            for i, (train, test) in enumerate(cv.split(X_cv, metadata_vals_cv)):
                classifier.fit(X_cv[X_cv.index.isin(train)], Y_cv[train])
                preds = classifier.predict(X_cv[X_cv.index.isin(train)])
                train_mae = mean_absolute_error(Y_cv[train].astype(float), preds)
                train_mse = mean_squared_error(Y_cv[train].astype(float), preds)
                train_maes.append(train_mae)
                train_mses.append(train_mse)

                preds = classifier.predict(X_cv[X_cv.index.isin(test)])
                test_mae = mean_absolute_error(Y_cv[test].astype(float), preds)
                test_mse = mean_squared_error(Y_cv[test].astype(float), preds)
                test_maes.append(test_mae)
                test_mses.append(test_mse)

            cv_obj = {
                "train_mae": np.array(train_maes).mean(),
                "train_mae_std": np.array(train_maes).std(),
                "train_mse": np.array(train_mses).mean(),
                "train_mse_std": np.array(train_mses).std(),
                "cv_mae": np.array(test_maes).mean(),
                "cv_mae_std": np.array(test_maes).std(),
                "cv_mse": np.array(test_mses).mean(),
                "cv_mse_std": np.array(test_mses).std()
            }
            return cv_obj

        if cross_validate_set == "full":
            cv_obj = performCrossValidationForAUC(X, metadata_vals, Y)
            return {
                "train_mae": cv_obj["train_mae"],
                "train_mae_std": cv_obj["train_mae_std"],
                "train_mse": cv_obj["train_mse"],
                "train_mse_std": cv_obj["train_mse_std"],
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

            X_train = X_train.reset_index(drop=True)
            X_test = X_test.reset_index(drop=True)
            cv_obj = performCrossValidationForAUC(X_train, np.array(metadata_vals)[ind_train], y_train)

            classifier = ElasticNet(l1_ratio=mixing_ratio, max_iter=max_iterations)
            classifier.fit(X_train, y_train)
            preds = classifier.predict(X_test)
            test_mae = mean_absolute_error(y_test.astype(float), preds)
            test_mse = mean_squared_error(y_test.astype(float), preds)

            abundances_obj = {
                "train_mae": cv_obj["train_mae"],
                "train_mae_std": cv_obj["train_mae_std"],
                "train_mse": cv_obj["train_mse"],
                "train_mse_std": cv_obj["train_mse_std"],
                "cv_mae": cv_obj["cv_mae"],
                "cv_mae_std": cv_obj["cv_mae_std"],
                "cv_mse": cv_obj["cv_mse"],
                "cv_mse_std": cv_obj["cv_mse_std"],
                "test_mae": test_mae,
                "test_mse": test_mse,
                "training_indexes": ind_train.tolist()
            }

            return abundances_obj
