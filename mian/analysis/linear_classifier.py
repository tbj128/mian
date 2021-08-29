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
from sklearn.experimental import enable_iterative_imputer
from sklearn.linear_model import SGDClassifier, LogisticRegression, Perceptron
from sklearn.metrics import roc_curve, roc_auc_score
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.impute import IterativeImputer, SimpleImputer
from sklearn.svm import LinearSVC

from mian.model.otu_table import OTUTable
import random

class LinearClassifier(object):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        metadata_vals = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.catvar)

        return self.analyse(user_request, otu_table, headers, metadata_vals)

    def analyse(self, user_request, otu_table, headers, metadata_vals):
        cross_validate_set = user_request.get_custom_attr("crossValidate")
        cross_validate_folds = int(user_request.get_custom_attr("crossValidateFolds"))
        loss_function = user_request.get_custom_attr("lossFunction")
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
            for i in range(len(uniq_metadata_vals)):
                class_to_roc[uniq_metadata_vals[i]] = {
                    "fprs": [],
                    "tprs": [],
                    "aucs": []
                }

            for i, (train, test) in enumerate(cv.split(X_cv, metadata_vals_cv)):
                classifier.fit(X_cv[X_cv.index.isin(train)], Y_cv[train])
                test_probs = classifier.decision_function(X_cv[X_cv.index.isin(test)])

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
                "class_to_roc": average_class_to_roc
            }
            return cv_obj

        def get_auc(classifier, y_test, test_probs):
            class_to_roc = {}
            y_test_binarize = binarize(classifier, y_test)
            if len(classifier.classes_) == 2:
                fpr, tpr, _ = roc_curve(y_test_binarize[:, 1], test_probs[:])
                auc = roc_auc_score(y_test_binarize[:, 1], test_probs[:])

                label = classifier.classes_[0] + " vs " + classifier.classes_[1]
                class_to_roc[label] = {
                    "fpr": [round(a.item(), 4) for a in fpr],
                    "tpr": [round(a.item(), 4) for a in tpr],
                    "auc": round(auc.item(), 4)
                }
            else:
                for i in range(len(classifier.classes_)):
                    fpr, tpr, _ = roc_curve(y_test_binarize[:, i], test_probs[:, i])
                    try:
                        auc = roc_auc_score(y_test_binarize[:, i], test_probs[:, i])

                        class_to_roc[classifier.classes_[i]] = {
                            "fpr": [round(a.item(), 4) for a in fpr],
                            "tpr": [round(a.item(), 4) for a in tpr],
                            "auc": round(auc.item(), 4)
                        }
                    except ValueError:
                        print("ROC could not be calculated")
                        pass
            return class_to_roc

        if cross_validate_set == "full":
            cv_obj = performCrossValidationForAUC(X, metadata_vals, Y)
            return {
                "train_class_to_roc": cv_obj["class_to_roc"]
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

            classifier = SGDClassifier(penalty="elasticnet", loss=loss_function, l1_ratio=mixing_ratio, max_iter=max_iterations)

            classifier.fit(X_train, y_train)
            train_probs = classifier.decision_function(X_train)
            val_probs = classifier.decision_function(X_val)
            test_probs = classifier.decision_function(X_test)

            print(f"X_train: {X_train.shape}")
            print(f"X_val: {X_val.shape}")
            print(f"X_test: {X_test.shape}")

            train_class_to_roc = get_auc(classifier, y_train, train_probs)
            val_class_to_roc = get_auc(classifier, y_val, val_probs)
            test_class_to_roc = get_auc(classifier, y_test, test_probs)

            abundances_obj = {
                "train_class_to_roc": train_class_to_roc,
                "val_class_to_roc": val_class_to_roc,
                "test_class_to_roc": test_class_to_roc,
                "seed": seed
            }

            return abundances_obj
