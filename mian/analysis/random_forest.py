# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#

import numpy as np
import pandas as pd
from scipy import interp
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import roc_curve, roc_auc_score
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import normalize
from sklearn.utils import shuffle

from mian.model.otu_table import OTUTable


class RandomForest(object):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        metadata_vals = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.catvar)

        return self.analyse(user_request, otu_table, headers, metadata_vals)

    def analyse(self, user_request, otu_table, headers, metadata_vals):
        cross_validate_set = user_request.get_custom_attr("crossValidate")
        cross_validate_folds = int(user_request.get_custom_attr("crossValidateFolds"))
        fix_training = user_request.get_custom_attr("fixTraining")
        training_proportion = user_request.get_custom_attr("trainingProportion")
        existing_training_indexes = np.array(user_request.get_custom_attr("trainingIndexes"))
        num_trees = int(user_request.get_custom_attr("numTrees"))
        max_depth = int(user_request.get_custom_attr("maxDepth")) if user_request.get_custom_attr("maxDepth") != "" else None


        if int(user_request.level) == -1:
            # OTU tables are returned as a CSR matrix
            X = pd.DataFrame.sparse.from_spmatrix(otu_table, columns=headers, index=range(otu_table.shape[0]))
        else:
            X = otu_table

        Y = np.array(metadata_vals)
        uniq_metadata_vals = list(set(Y))

        # https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0188475

        def binarize(classifier, Y_cv):
            actual_class_to_index = {}
            for i in range(len(classifier.classes_)):
                actual_class_to_index[classifier.classes_[i]] = i

            Y_cv_binarize = []
            for y_val in Y_cv:
                binarized = [0] * len(classifier.classes_)
                binarized[actual_class_to_index[y_val]] = 1
                Y_cv_binarize.append(binarized)
            return np.array(Y_cv_binarize)

        def performCrossValidationForAUC(X_cv, metadata_vals_cv, Y_cv):
            cv = StratifiedKFold(n_splits=cross_validate_folds)

            classifier = RandomForestClassifier(n_estimators=num_trees, max_depth=max_depth, oob_score=True)

            base_fpr = np.linspace(0, 1, 51)
            class_to_roc = {}
            test_accuracies = []
            for i in range(len(uniq_metadata_vals)):
                class_to_roc[uniq_metadata_vals[i]] = {
                    "fprs": [],
                    "tprs": [],
                    "aucs": []
                }

            for i, (train, test) in enumerate(cv.split(X_cv, metadata_vals_cv)):
                classifier.fit(X_cv[X_cv.index.isin(train)], Y_cv[train])
                test_probs = classifier.decision_function(X_cv[X_cv.index.isin(test)])
                test_accuracy = classifier.score(X_cv[X_cv.index.isin(test)], Y_cv[test])
                test_accuracies.append(test_accuracy)

                Y_cv_binarize = binarize(classifier, Y_cv[test])
                if len(classifier.classes_) == 2:
                    fpr, tpr, _ = roc_curve(Y_cv_binarize[:, 1], test_probs[:])
                    auc = roc_auc_score(Y_cv_binarize[:, 1], test_probs[:])
                    tpr = interp(base_fpr, fpr, tpr)
                    tpr[0] = 0.0

                    label = classifier.classes_[1]
                    class_to_roc[label]["fprs"].append(base_fpr)
                    class_to_roc[label]["tprs"].append(tpr)
                    class_to_roc[label]["aucs"].append(auc)
                else:
                    for c in range(len(classifier.classes_)):
                        actual_class = classifier.classes_[c]

                        fpr, tpr, _ = roc_curve(Y_cv_binarize[:, c], test_probs[:, c])
                        auc = roc_auc_score(Y_cv_binarize[:, c], test_probs[:, c])

                        tpr = interp(base_fpr, fpr, tpr)
                        tpr[0] = 0.0

                        class_to_roc[actual_class]["fprs"].append(base_fpr)
                        class_to_roc[actual_class]["tprs"].append(tpr)
                        class_to_roc[actual_class]["aucs"].append(auc)

                        i += 1

            average_class_to_roc = {}
            for k, v in class_to_roc.items():
                if len(class_to_roc[k]["tprs"]) > 0:
                    average_class_to_roc[k] = {
                        "fpr": [round(a.item(), 4) for a in np.array(class_to_roc[k]["fprs"]).mean(axis=0)],
                        "tpr": [round(a.item(), 4) for a in np.array(class_to_roc[k]["tprs"]).mean(axis=0)],
                        "auc": round(np.array(class_to_roc[k]["aucs"]).mean(), 4),
                        "auc_std": round(np.array(class_to_roc[k]["aucs"]).std(), 4)
                    }

            cv_obj = {
                "class_to_roc": average_class_to_roc,
                "cv_accuracy": round(np.array(test_accuracies).mean(), 4),
                "cv_accuracy_std": round(np.array(test_accuracies).std(), 4)
            }
            return cv_obj

        if cross_validate_set == "full":
            cv_obj = performCrossValidationForAUC(X, metadata_vals, Y)
            return {
                "train_class_to_roc": cv_obj["class_to_roc"],
                "cv_accuracy": cv_obj["cv_accuracy"],
                "cv_accuracy_std": cv_obj["cv_accuracy_std"]
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
                                                                                         train_size=training_proportion,
                                                                                         stratify=Y)

            X_train = normalize(X_train)
            X_test = normalize(X_test)

            classifier = RandomForestClassifier(n_estimators=num_trees, max_depth=max_depth, oob_score=True)

            classifier.fit(X_train, y_train)
            test_probs = classifier.predict_proba(X_test)
            test_accuracy = classifier.score(X_test, y_test)

            class_to_roc = {}
            for i in range(len(classifier.classes_)):
                y_test_binarize = binarize(classifier, y_test)
                fpr, tpr, _ = roc_curve(y_test_binarize[:, i], test_probs[:, i])
                auc = roc_auc_score(y_test_binarize[:, i], test_probs[:, i])

                class_to_roc[classifier.classes_[i]] = {
                    "fpr": [a.item() for a in fpr],
                    "tpr": [a.item() for a in tpr],
                    "auc": auc.item()
                }
                i += 1

            abundances_obj = {
                "oob_error": 1 - classifier.oob_score_,
                "test_accuracy": test_accuracy,
                "test_class_to_roc": class_to_roc,
                "training_indexes": ind_train.tolist()
            }

            return abundances_obj
