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
from sklearn.metrics import roc_curve, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle

from mian.model.otu_table import OTUTable
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import numpy as np


class RandomForest(object):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        metadata_vals = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.catvar)

        return self.analyse(user_request, otu_table, headers, metadata_vals)

    def analyse(self, user_request, otu_table, headers, metadata_vals):
        fix_training = user_request.get_custom_attr("fixTraining")
        training_proportion = user_request.get_custom_attr("trainingProportion")
        existing_training_indexes = np.array(user_request.get_custom_attr("trainingIndexes"))
        num_trees = int(user_request.get_custom_attr("numTrees"))
        max_depth = int(user_request.get_custom_attr("maxDepth")) if user_request.get_custom_attr("maxDepth") != "" else None

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

        rf = RandomForestClassifier(n_estimators=num_trees, max_depth=max_depth, oob_score=True)
        rf.fit(X_train, y_train)

        accuracy = rf.score(X_test, y_test)
        probs = np.array(rf.predict_proba(X_test))
        class_to_roc = {}
        classes = rf.classes_
        i = 0
        for c in classes:
            orig_c = list(le.inverse_transform([c]))[0]
            y_test_mask = []
            for y in y_test:
                y_test_mask.append(1 if y == c else 0)
            fpr, tpr, thresholds = roc_curve(y_test_mask, probs[:, i])
            auc = roc_auc_score(y_test_mask, probs[:, i])
            class_to_roc[orig_c] = {
                "fpr": [a.item() for a in fpr],
                "tpr": [a.item() for a in tpr],
                "auc": auc.item()
            }
            i += 1

        abundances_obj = {
            "oob_error": 1 - rf.oob_score_,
            "accuracy": accuracy,
            "class_to_roc": class_to_roc,
            "training_indexes": ind_train.tolist()
        }

        return abundances_obj
