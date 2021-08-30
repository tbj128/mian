# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, roc_curve, roc_auc_score
from sklearn.model_selection import train_test_split

from sklearn.utils import shuffle

from mian.model.otu_table import OTUTable
from sklearn.preprocessing import LabelEncoder, normalize, StandardScaler
import pandas as pd

from tensorflow import keras
from tensorflow.keras.utils import to_categorical
import numpy as np
import random

class DeepNeuralNetwork(object):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        metadata_vals = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.get_custom_attr("expvar"))

        return self.analyse(user_request, otu_table, headers, metadata_vals)

    def analyse(self, user_request, otu_table, headers, metadata_vals):
        epochs = user_request.get_custom_attr("epochs")
        lr = float(user_request.get_custom_attr("lr"))
        dnn_model = user_request.get_custom_attr("dnnModel")
        problem_type = user_request.get_custom_attr("problemType")
        fix_training = user_request.get_custom_attr("fixTraining")
        training_proportion = user_request.get_custom_attr("trainingProportion")
        seed = int(user_request.get_custom_attr("seed")) if user_request.get_custom_attr("seed") is not "" else random.randint(0, 100000)

        if int(user_request.level) == -1:
            # OTU tables are returned as a CSR matrix
            X = pd.DataFrame.sparse.from_spmatrix(otu_table, columns=headers, index=range(otu_table.shape[0]))
        else:
            X = otu_table

        le_name_mapping = {}
        if problem_type == "classification":
            le = LabelEncoder()
            le.fit(metadata_vals)
            Y = le.transform(metadata_vals)
            le_name_mapping = dict(zip(le.transform(le.classes_), le.classes_))
            Y = to_categorical(Y)
        else:
            Y = np.array([float(i) for i in metadata_vals])

        if fix_training == "yes":
            if problem_type == "classification":
                X_train, X_test, y_train, y_test = train_test_split(X, Y, train_size=training_proportion, random_state=seed, stratify=Y)
                X_val, X_test, y_val, y_test = train_test_split(X_test, y_test, train_size=0.5, random_state=seed, stratify=y_test)
            else:
                X_train, X_test, y_train, y_test = train_test_split(X, Y, train_size=training_proportion, random_state=seed)
                X_val, X_test, y_val, y_test = train_test_split(X_test, y_test, train_size=0.5, random_state=seed)
        else:
            if problem_type == "classification":
                # Use a random seed each time (not recommended)
                X_train, X_test, y_train, y_test = train_test_split(X, Y, train_size=training_proportion, stratify=Y)
                X_val, X_test, y_val, y_test = train_test_split(X_test, y_test, train_size=0.5, stratify=y_test)
            else:
                # Use a random seed each time (not recommended)
                X_train, X_test, y_train, y_test = train_test_split(X, Y, train_size=training_proportion)
                X_val, X_test, y_val, y_test = train_test_split(X_test, y_test, train_size=0.5)

        imp_mean = SimpleImputer(missing_values=np.nan, strategy='mean')
        X_train = imp_mean.fit_transform(X_train)
        X_val = imp_mean.transform(X_val)
        X_test = imp_mean.transform(X_test)

        # Note: mean is not scaled to support sparse matrices
        scaler = StandardScaler(with_mean=False)
        X_train = scaler.fit_transform(X_train)
        X_val = scaler.transform(X_val)
        X_test = scaler.transform(X_test)

        def get_auc(class_mapping, y_test, test_probs):
            """
            One vs Rest strategy
            :param class_mapping
            :param y_test: (n, c)
            :param test_probs: (n, c)
            """
            class_to_roc = {}
            for i in range(y_test.shape[1]):
                fpr, tpr, _ = roc_curve(y_test[:, i], test_probs[:, i])
                try:
                    auc = roc_auc_score(y_test[:, i], test_probs[:, i])

                    class_to_roc[class_mapping[i]] = {
                        "fpr": [round(a.item(), 4) for a in fpr],
                        "tpr": [round(a.item(), 4) for a in tpr],
                        "auc": round(auc.item(), 4),
                        "num_positives": sum(y_test[:, i])
                    }
                except ValueError:
                    print("ROC could not be calculated")
                    pass
            return class_to_roc

        def build_model(dnn_model, problem_type):
            i = 0
            layers = []
            for layer in dnn_model:
                if layer["type"] == "dense":
                    if i == 0:
                        layers.append(keras.layers.Dense(int(layer["units"]), activation='relu', input_shape=(len(headers),)))
                    else:
                        layers.append(keras.layers.Dense(int(layer["units"]), activation='relu'))
                elif layer["type"] == "dropout":
                    layers.append(keras.layers.Dropout(float(layer["dropoutfrac"])))
                i += 1
            if problem_type == "classification":
                layers.append(keras.layers.Dense(len(set(metadata_vals)), activation='softmax'))
                model = keras.Sequential(layers)
                optimizer = keras.optimizers.Adam(learning_rate=lr)
                model.compile(loss='categorical_crossentropy',
                              optimizer=optimizer)
            else:
                layers.append(keras.layers.Dense(1))
                model = keras.Sequential(layers)
                optimizer = keras.optimizers.Adam(learning_rate=lr)
                model.compile(loss='mse',
                              optimizer=optimizer)

            return model

        model = build_model(dnn_model, problem_type)
        if problem_type == "classification":
            hist = model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=epochs,
                verbose=0
            )

            y_test_prob = model.predict(X_test, verbose=0)
            test_auc = get_auc(le_name_mapping, y_test, y_test_prob)
            y_val_prob = model.predict(X_val, verbose=0)
            val_auc = get_auc(le_name_mapping, y_val, y_val_prob)
            y_train_prob = model.predict(X_train, verbose=0)
            train_auc = get_auc(le_name_mapping, y_train, y_train_prob)

            abundances_obj = {
                "train_loss": [a for a in hist.history['loss']],
                "val_loss": [a for a in hist.history['val_loss']],
                "train_class_to_roc": train_auc,
                "val_class_to_roc": val_auc,
                "test_class_to_roc": test_auc,
                "num_samples": otu_table.shape[0],
                "train_size": X_train.shape,
                "val_size": X_val.shape,
                "test_size": X_test.shape,
                "seed": seed
            }
            return abundances_obj
        else:
            hist = model.fit(
                X_train, y_train,
                epochs=epochs,
                validation_data=(X_val, y_val),
                verbose=0
            )

            train_predictions = model.predict(X_train)
            train_mae = mean_absolute_error(y_train, train_predictions)
            train_mse = mean_squared_error(y_train, train_predictions)

            val_predictions = model.predict(X_val)
            val_mae = mean_absolute_error(y_val, val_predictions)
            val_mse = mean_squared_error(y_val, val_predictions)

            test_predictions = model.predict(X_test)
            test_mae = mean_absolute_error(y_test, test_predictions)
            test_mse = mean_squared_error(y_test, test_predictions)

            abundances_obj = {
                "train_loss": [a for a in hist.history['loss']],
                "val_loss": [a for a in hist.history['val_loss']],
                "train_mae": round(train_mae.item(), 2),
                "train_mse": round(train_mse.item(), 2),
                "val_mae": round(val_mae.item(), 2),
                "val_mse": round(val_mse.item(), 2),
                "test_mae": round(test_mae.item(), 2),
                "test_mse": round(test_mse.item(), 2),
                "num_samples": otu_table.shape[0],
                "train_size": X_train.shape,
                "val_size": X_val.shape,
                "test_size": X_test.shape,
                "seed": seed
            }

            return abundances_obj
