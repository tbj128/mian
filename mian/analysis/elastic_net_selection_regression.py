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
from sklearn.model_selection import train_test_split

from mian.model.otu_table import OTUTable
import numpy as np


class ElasticNetSelectionRegression(object):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        metadata_vals = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.get_custom_attr("expvar"))
        taxonomy_map = table.get_otu_metadata().get_taxonomy_map()

        return self.analyse(user_request, otu_table, headers, metadata_vals, taxonomy_map)

    def analyse(self, user_request, otu_table, headers, metadata_vals, taxonomy_map):
        fix_training = user_request.get_custom_attr("fixTraining") == "yes"
        existing_training_indexes = user_request.get_custom_attr("trainingIndexes")
        training_proportion = float(user_request.get_custom_attr("trainingProportion"))
        mixing_ratio = float(user_request.get_custom_attr("mixingRatio"))
        max_iterations = int(user_request.get_custom_attr("maxIterations"))
        keep = -1 if user_request.get_custom_attr("keep") == "" else int(user_request.get_custom_attr("keep"))

        otu_to_genus = {}
        if int(user_request.level) == -1:
            # We want to display a short hint for the OTU using the genus (column 5)
            for header in headers:
                if header in taxonomy_map and len(taxonomy_map[header]) > 5:
                    otu_to_genus[header] = taxonomy_map[header][5]
                else:
                    otu_to_genus[header] = ""

        if fix_training and len(existing_training_indexes) > 0:
            existing_training_indexes = [int(i) for i in existing_training_indexes]
            training_indexes = np.array(existing_training_indexes)
        else:
            if training_proportion == 1:
                training_indexes = np.array(range(len(otu_table)))
            else:
                _, training_indexes = train_test_split(range(len(otu_table)), test_size=(1 - training_proportion))
        training_indexes = np.array(training_indexes)
        otu_table = otu_table[training_indexes, :]

        # NORMALIZE THE DATASET
        df = pd.DataFrame(data=otu_table, columns=headers, index=range(len(otu_table)))
        stats = df.describe()
        stats = stats.transpose()

        def norm(x):
            return (x - stats['mean']) / stats['std']

        X = norm(df)
        Y = np.array(metadata_vals)
        Y = Y[training_indexes]

        # https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0188475
        classifier = ElasticNet(l1_ratio=mixing_ratio, max_iter=max_iterations)
        classifier.fit(X, Y)
        columns = np.array(headers)

        hints = {}
        coef = pd.Series(classifier.coef_, index=columns)
        if keep == -1:
            features = columns[coef != 0]
            weights = coef[coef != 0].abs().sort_values(ascending=False).values
        else:
            features = coef.abs().sort_values(ascending=False).head(keep).index
            weights = coef.abs().sort_values(ascending=False).head(keep).values

        if int(user_request.level) == -1:
            for f in features:
                hints[f] = otu_to_genus[f]

        feature_map = {
            "features": features.tolist(),
            "weights": weights.tolist()
        }

        abundances_obj = {}
        abundances_obj["feature_map"] = feature_map
        abundances_obj["hints"] = hints
        abundances_obj["training_indexes"] = training_indexes.tolist()

        return abundances_obj
