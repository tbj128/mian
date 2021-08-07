# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#
from keras.utils import to_categorical
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

from sklearn.utils import shuffle

from mian.model.otu_table import OTUTable
from sklearn.preprocessing import LabelEncoder, normalize
import pandas as pd

from tensorflow import keras
import numpy as np

class DeepNeuralNetwork(object):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        metadata_vals = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.get_custom_attr("expvar"))

        return self.analyse(user_request, otu_table, headers, metadata_vals)

    def analyse(self, user_request, otu_table, headers, metadata_vals):
        epochs = user_request.get_custom_attr("epochs")
        dnn_model = user_request.get_custom_attr("dnnModel")
        problem_type = user_request.get_custom_attr("problemType")
        fix_training = user_request.get_custom_attr("fixTraining")
        training_proportion = user_request.get_custom_attr("trainingProportion")
        validation_proportion = user_request.get_custom_attr("validationProportion")
        existing_training_indexes = np.array(user_request.get_custom_attr("trainingIndexes"))

        if int(user_request.level) == -1:
            # OTU tables are returned as a CSR matrix
            X = pd.DataFrame.sparse.from_spmatrix(otu_table, columns=headers, index=range(otu_table.shape[0]))
        else:
            X = otu_table

        if problem_type == "classification":
            le = LabelEncoder()
            le.fit(metadata_vals)
            Y = le.transform(metadata_vals)
            Y = to_categorical(Y)
        else:
            Y = metadata_vals

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
            X_train, X_test, y_train, y_test, ind_train, ind_test = train_test_split(X, Y, indices, train_size=training_proportion,
                                                                                         stratify=Y)

        X_train = normalize(X_train)
        X_test = normalize(X_test)

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
                layers.append(keras.layers.Dense(len(set(metadata_vals)), activation='sigmoid'))
                model = keras.Sequential(layers)
                optimizer = 'adam'
                model.compile(loss='categorical_crossentropy',
                              optimizer=optimizer,
                              metrics=['accuracy'])
            else:
                layers.append(keras.layers.Dense(1))
                model = keras.Sequential(layers)
                optimizer = 'adam'
                model.compile(loss='mse',
                              optimizer=optimizer,
                              metrics=['mae', 'mse'])

            return model


        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, train_size=training_proportion, stratify=y_train
        )

        model = build_model(dnn_model, problem_type)
        if problem_type == "classification":
            hist = model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=epochs,
                verbose=0
            )

            score = model.evaluate(X_test, y_test, verbose=0)
            print('Test loss:', score[0])
            print('Test accuracy:', score[1])

            abundances_obj = {
                "accuracy": [a for a in hist.history['accuracy']],
                "val_accuracy" : [a for a in hist.history['val_accuracy']],
                "loss": [a for a in hist.history['loss']],
                "val_loss": [a for a in hist.history['val_loss']],
                "test_accuracy": score[1],
                "test_loss": score[0],
                "num_samples": otu_table.shape[0],
                "training_indexes": ind_train.tolist()
            }
            return abundances_obj
        else:
            hist = model.fit(
                X_train, y_train,
                epochs=epochs, validation_split=validation_proportion, verbose=0
            )

            actual_predictions = model.predict(X_test)
            test_mae = mean_absolute_error(y_test, actual_predictions)
            test_mse = mean_squared_error(y_test, actual_predictions)

            abundances_obj = {
                "mae": [a.item() for a in hist.history['mae']],
                "val_mae": [a.item() for a in hist.history['val_mae']],
                "mse": [a.item() for a in hist.history['mse']],
                "val_mse": [a.item() for a in hist.history['val_mse']],
                "test_mae": test_mae.item(),
                "test_mse": test_mse.item(),
                "num_samples": len(otu_table),
                "training_indexes": ind_train.tolist()
            }

            return abundances_obj
