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
            return self.__getStatsAbundanceForOTUs(user_request, yvals)
        else:
            return self.__getMetadataForCategory(user_request, yvals)

    def __getStatsAbundanceForOTUs(self, user_request, statType):
        logger.info("Starting to read OTU table")
        table = OTUTable(user_request.user_id, user_request.pid)
        ## TODO: Should not aggregate
        base = table.get_table_after_filtering_and_aggregation(user_request.sample_filter,
                                                               user_request.sample_filter_vals,
                                                               user_request.taxonomy_filter_vals,
                                                               user_request.taxonomy_filter)

        metadata = table.get_sample_metadata().get_as_table()

        logger.info("Loaded OTU table")

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

                if statType == "mian-min":
                    row["a"] = np.min(abunArr)
                elif statType == "mian-max":
                    row["a"] = np.max(abunArr)
                elif statType == "mian-median":
                    row["a"] = np.median(abunArr)
                elif statType == "mian-mean":
                    row["a"] = np.average(abunArr)
                elif statType == "mian-abundance":
                    row["a"] = np.sum(abunArr)
                else:
                    row["a"] = 0

                if base[i][OTUTable.SAMPLE_ID_COL] in metadataMap:
                    abundances[metadataMap[base[i][OTUTable.SAMPLE_ID_COL]]].append(row)
                    statsAbundances[metadataMap[base[i][OTUTable.SAMPLE_ID_COL]]].append(row["a"])
            i += 1

        logger.info("Processed OTU table")

        # Calculate the statistical p-value
        statistics = Statistics.getTtest(statsAbundances)

        logger.info("Calculated Ttest")

        abundances_obj = {"abundances": abundances, "stats": statistics}
        return abundances_obj

    def __getMetadataForCategory(self, user_request, metavar):
        # This code path is used only when the user wants to draw boxplots from only the metadata data

        table = OTUTable(user_request.user_id, user_request.pid)
        metadata = table.get_sample_metadata().get_as_filtered_table(user_request.sample_filter,
                                                                     user_request.sample_filter_vals)

        logger.info(metadata)

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
                    if metadata[i][j] == metavar:
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
