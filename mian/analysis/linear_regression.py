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
from sklearn.model_selection import train_test_split
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

        le = LabelEncoder()
        le.fit(metadata_vals)
        Y = le.transform(metadata_vals)

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

        rf = ElasticNet(l1_ratio=mixing_ratio, max_iter=max_iterations)
        rf.fit(X_train, y_train)
        preds = rf.predict(X_train)
        train_mae = mean_absolute_error(y_train, preds)
        train_mse = mean_squared_error(y_train, preds)

        preds = rf.predict(X_test)
        test_mae = mean_absolute_error(y_test, preds)
        test_mse = mean_squared_error(y_test, preds)

        abundances_obj = {
            "train_mae": train_mae,
            "train_mse": train_mse,
            "test_mae": test_mae,
            "test_mse": test_mse,
            "training_indexes": ind_train.tolist()
        }

        return abundances_obj
