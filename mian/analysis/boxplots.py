import numpy as np

from mian.analysis.analysis_base import AnalysisBase
from mian.core.statistics import Statistics
from mian.model.otu_table import OTUTable
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


class Boxplots(AnalysisBase):

    def run(self, user_request):
        yvals = user_request.get_custom_attr("yvals")
        if yvals.startswith("mian-"):
            return self.abundance_boxplots(user_request, yvals)
        else:
            return self.metadata_boxplots(user_request, yvals)

    def abundance_boxplots(self, user_request, yvals):
        logger.info("Starting abundance_boxplots")
        table = OTUTable(user_request.user_id, user_request.pid)
        base = table.get_table_after_filtering_and_aggregation(user_request.taxonomy_filter,
                                                               user_request.taxonomy_filter_role,
                                                               user_request.taxonomy_filter_vals,
                                                               user_request.sample_filter,
                                                               user_request.sample_filter_role,
                                                               user_request.sample_filter_vals,
                                                               user_request.level)
        metadata = table.get_sample_metadata().get_as_table()
        return self.process_abundance_boxplots(user_request, yvals, base, metadata)

    def process_abundance_boxplots(self, user_request, yvals, base, metadata):

        statsAbundances = {}
        abundances = {}
        metadataMap = {}

        catCol = -1
        i = 0
        while i < len(metadata):
            if i == 0:
                j = 0
                while j < len(metadata[i]):
                    if metadata[i][j] == user_request.catvar:
                        catCol = j
                    j += 1
            else:
                if catCol > -1:
                    metadataMap[metadata[i][0]] = metadata[i][catCol]
                    if metadata[i][catCol] not in abundances:
                        abundances[metadata[i][catCol]] = []
                        statsAbundances[metadata[i][catCol]] = []
                else:
                    metadataMap[metadata[i][0]] = "All"
                    abundances["All"] = []
                    statsAbundances["All"] = []
            i += 1

        logger.info("Initialized metadata maps")

        i = 0
        while i < len(base):
            if i > 0:
                row = {}
                row["s"] = str(base[i][OTUTable.SAMPLE_ID_COL])

                abunArr = []

                j = OTUTable.OTU_START_COL
                while j < len(base[i]):
                    abunArr.append(float(base[i][j]))
                    j += 1

                if yvals == "mian-min":
                    row["a"] = np.min(abunArr)
                elif yvals == "mian-max":
                    row["a"] = np.max(abunArr)
                elif yvals == "mian-median":
                    row["a"] = np.median(abunArr)
                elif yvals == "mian-mean":
                    row["a"] = np.average(abunArr)
                elif yvals == "mian-abundance":
                    row["a"] = np.sum(abunArr)
                else:
                    row["a"] = 0

                if base[i][OTUTable.SAMPLE_ID_COL] in metadataMap:
                    abundances[metadataMap[base[i][OTUTable.SAMPLE_ID_COL]]].append(row)
                    statsAbundances[metadataMap[base[i][OTUTable.SAMPLE_ID_COL]]].append(row["a"])
            i += 1

        # Calculate the statistical p-value
        statistics = Statistics.getTtest(statsAbundances)

        logger.info("Calculated Ttest")

        abundances_obj = {"abundances": abundances, "stats": statistics}
        return abundances_obj

    def metadata_boxplots(self, user_request, yvals):
        logger.info("Starting metadata_boxplots")

        # This code path is used only when the user wants to draw boxplots from only the metadata data

        table = OTUTable(user_request.user_id, user_request.pid)
        metadata = table.get_sample_metadata().get_as_filtered_table(user_request.sample_filter,
                                                                     user_request.sample_filter_role,
                                                                     user_request.sample_filter_vals)
        return self.process_metadata_boxplots(user_request, yvals, metadata)

    def process_metadata_boxplots(self, user_request, yvals, metadata):
        statsAbundances = {}
        abundances = {}

        # catCol is on the x-axis
        catCol = 1
        # metaCol is on the y-axis
        metaCol = 1
        i = 0
        while i < len(metadata):
            if i == 0:
                j = 0
                while j < len(metadata[i]):
                    if metadata[i][j] == user_request.catvar:
                        catCol = j
                    if metadata[i][j] == yvals:
                        metaCol = j
                    j += 1
                logger.info("Found metadata col of %s and cat col of %s", str(metaCol), str(catCol))
            else:
                row = {}
                try:
                    row["a"] = float(metadata[i][metaCol])
                    row["s"] = str(metadata[i][OTUTable.SAMPLE_ID_COL])
                    if metadata[i][catCol] in abundances:
                        abundances[metadata[i][catCol]].append(row)
                    else:
                        abundances[metadata[i][catCol]] = [row]

                    if metadata[i][catCol] in statsAbundances:
                        statsAbundances[metadata[i][catCol]].append(row["a"])
                    else:
                        statsAbundances[metadata[i][catCol]] = [row["a"]]
                except ValueError:
                    pass

            i += 1

        # Calculate the statistical p-value
        statistics = Statistics.getTtest(statsAbundances)

        abundancesObj = {}
        abundancesObj["abundances"] = abundances
        abundancesObj["stats"] = statistics
        return abundancesObj
