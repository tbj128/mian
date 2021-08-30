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
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_curve, roc_auc_score
from sklearn.model_selection import train_test_split, StratifiedKFold
import random

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
        seed = int(user_request.get_custom_attr("seed")) if user_request.get_custom_attr("seed") is not "" else random.randint(0, 100000)
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
                test_probs = classifier.predict_proba(X_cv[X_cv.index.isin(test)])
                test_accuracy = classifier.score(X_cv[X_cv.index.isin(test)], Y_cv[test])
                test_accuracies.append(test_accuracy)

                Y_cv_binarize = binarize(classifier, Y_cv[test])
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

        def get_auc(classifier, y_test, test_probs):
            class_to_roc = {}
            y_test_binarize = binarize(classifier, y_test)
            for i in range(len(classifier.classes_)):
                fpr, tpr, _ = roc_curve(y_test_binarize[:, i], test_probs[:, i])
                try:
                    auc = roc_auc_score(y_test_binarize[:, i], test_probs[:, i])

                    class_to_roc[classifier.classes_[i]] = {
                        "fpr": [round(a.item(), 4) for a in fpr],
                        "tpr": [round(a.item(), 4) for a in tpr],
                        "auc": round(auc.item(), 4),
                        "num_positives": sum(y_test_binarize[:, i])
                    }
                except ValueError:
                    print("ROC could not be calculated")
                    pass
            return class_to_roc

        if cross_validate_set == "full":
            cv_obj = performCrossValidationForAUC(X, metadata_vals, Y)
            return {
                "train_class_to_roc": cv_obj["class_to_roc"],
                "cv_accuracy": cv_obj["cv_accuracy"],
                "cv_accuracy_std": cv_obj["cv_accuracy_std"]
            }
        else:
            if fix_training == "yes":
                X_train, X_test, y_train, y_test = train_test_split(X, Y, train_size=training_proportion, random_state=seed, stratify=Y)
                X_val, X_test, y_val, y_test = train_test_split(X_test, y_test, train_size=0.5, random_state=seed, stratify=y_test)
            else:
                # Use a random seed each time (not recommended)
                X_train, X_test, y_train, y_test = train_test_split(X, Y, train_size=training_proportion, stratify=Y)
                X_val, X_test, y_val, y_test = train_test_split(X_test, y_test, train_size=0.5, stratify=y_test)

            imp_mean = SimpleImputer(missing_values=np.nan, strategy='mean')
            X_train = imp_mean.fit_transform(X_train)
            X_val = imp_mean.transform(X_val)
            X_test = imp_mean.transform(X_test)

            classifier = RandomForestClassifier(n_estimators=num_trees, max_depth=max_depth, oob_score=True)

            classifier.fit(X_train, y_train)
            train_probs = classifier.predict_proba(X_train)
            val_probs = classifier.predict_proba(X_val)
            test_probs = classifier.predict_proba(X_test)

            train_class_to_roc = get_auc(classifier, y_train, train_probs)
            val_class_to_roc = get_auc(classifier, y_val, val_probs)
            test_class_to_roc = get_auc(classifier, y_test, test_probs)

            abundances_obj = {
                "oob_error": 1 - classifier.oob_score_,
                "train_class_to_roc": train_class_to_roc,
                "val_class_to_roc": val_class_to_roc,
                "test_class_to_roc": test_class_to_roc,
                "train_size": X_train.shape,
                "val_size": X_val.shape,
                "test_size": X_test.shape,
                "seed": seed
            }

            return abundances_obj
