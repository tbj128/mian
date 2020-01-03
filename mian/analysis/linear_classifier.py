# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#
from sklearn import svm

import pandas as pd
from sklearn.linear_model import ElasticNet, SGDClassifier
from sklearn.metrics import mean_absolute_error, mean_squared_error, roc_curve, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.utils import shuffle

from mian.model.otu_table import OTUTable
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
import numpy as np


class LinearClassifier(object):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        metadata_vals = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.catvar)

        return self.analyse(user_request, otu_table, headers, metadata_vals)

    def analyse(self, user_request, otu_table, headers, metadata_vals):
        loss_function = user_request.get_custom_attr("lossFunction")
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

        mlb = MultiLabelBinarizer()
        Y = mlb.fit_transform([(a,) for a in metadata_vals])
        print(Y)

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

        classifier = OneVsRestClassifier(SGDClassifier(loss=loss_function, l1_ratio=mixing_ratio, max_iter=max_iterations))
        classifier.fit(X_train, y_train)
        test_probs = classifier.decision_function(X_test)
        train_accuracy = classifier.score(X_train, y_train)
        test_accuracy = classifier.score(X_test, y_test)

        class_to_roc = {}
        for i in range(len(mlb.classes_)):
            fpr, tpr, _ = roc_curve(y_test[:, i], test_probs[:, i])
            auc = roc_auc_score(y_test[:, i], test_probs[:, i])

            class_to_roc[mlb.classes_[i]] = {
                "fpr": [a.item() for a in fpr],
                "tpr": [a.item() for a in tpr],
                "auc": auc.item()
            }
            i += 1

        abundances_obj = {
            "train_accuracy": train_accuracy,
            "test_accuracy": test_accuracy,
            "class_to_roc": class_to_roc,
            "training_indexes": ind_train.tolist()
        }

        return abundances_obj
