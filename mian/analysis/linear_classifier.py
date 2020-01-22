# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#
from scipy import interp

import pandas as pd
from sklearn.linear_model import ElasticNet, SGDClassifier
from sklearn.metrics import mean_absolute_error, mean_squared_error, roc_curve, roc_auc_score
from sklearn.model_selection import train_test_split, cross_validate, KFold, cross_val_score, StratifiedKFold
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
        cross_validate_set = user_request.get_custom_attr("crossValidate")
        cross_validate_folds = int(user_request.get_custom_attr("crossValidateFolds"))
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

            classifier = SGDClassifier(loss=loss_function, l1_ratio=mixing_ratio, max_iter=max_iterations)

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

                for i in range(len(classifier.classes_)):
                    actual_class = classifier.classes_[i]
                    Y_cv_binarize = binarize(classifier, Y_cv)

                    fpr, tpr, _ = roc_curve(Y_cv_binarize[test, i], test_probs[:, i])
                    auc = roc_auc_score(Y_cv_binarize[test, i], test_probs[:, i])

                    tpr = interp(base_fpr, fpr, tpr)
                    tpr[0] = 0.0

                    class_to_roc[actual_class]["fprs"].append(base_fpr)
                    class_to_roc[actual_class]["tprs"].append(tpr)
                    class_to_roc[actual_class]["aucs"].append(auc)

                    i += 1

            average_class_to_roc = {}
            for i in range(len(uniq_metadata_vals)):
                actual_class = uniq_metadata_vals[i]
                if len(class_to_roc[actual_class]["tprs"]) > 0:
                    average_class_to_roc[actual_class] = {
                        "fpr": [a.item() for a in np.array(class_to_roc[actual_class]["fprs"]).mean(axis=0)],
                        "tpr": [a.item() for a in np.array(class_to_roc[actual_class]["tprs"]).mean(axis=0)],
                        "auc": np.array(class_to_roc[actual_class]["aucs"]).mean(),
                        "auc_std": np.array(class_to_roc[actual_class]["aucs"]).std()
                    }

            cv_obj = {
                "class_to_roc": average_class_to_roc,
                "cv_accuracy": np.array(test_accuracies).mean(),
                "cv_accuracy_std": np.array(test_accuracies).std()
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
                                                                                         train_size=training_proportion)

            X_train = X_train.reset_index(drop=True)
            X_test = X_test.reset_index(drop=True)
            cv_obj = performCrossValidationForAUC(X_train, np.array(metadata_vals)[ind_train], y_train)

            classifier = SGDClassifier(loss=loss_function, l1_ratio=mixing_ratio, max_iter=max_iterations)
            classifier.fit(X_train, y_train)
            test_probs = classifier.decision_function(X_test)
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
                "train_class_to_roc": cv_obj["class_to_roc"],
                "cv_accuracy": cv_obj["cv_accuracy"],
                "cv_accuracy_std": cv_obj["cv_accuracy_std"],
                "test_accuracy": test_accuracy,
                "test_class_to_roc": class_to_roc,
                "training_indexes": ind_train.tolist()
            }

            return abundances_obj
