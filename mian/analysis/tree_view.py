# ==============================================================================
#
# Utility functions used for data transformation or other common functionality
# @author: tbj128
#
# ==============================================================================

#
# Imports
#
import numpy as np
import logging

from mian.analysis.analysis_base import AnalysisBase

from mian.model.otu_table import OTUTable


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TreeView(AnalysisBase):

    def run(self, user_request):
        logger.info("Starting TreeView analysis")
        table = OTUTable(user_request.user_id, user_request.pid)
        base, headers, sample_labels = table.get_table_after_filtering_and_aggregation(user_request)

        taxonomy_map = table.get_otu_metadata().get_taxonomy_map()

        unique_meta_vals = table.get_sample_metadata().get_metadata_unique_vals(user_request.catvar)
        sample_ids_to_metadata_map = table.get_sample_metadata().get_sample_id_to_metadata_map(user_request.catvar)

        # If the sample_ids_to_metadata_map is empty, the user has not chosen to break down the visualization by
        # any particular category. We will assume that there is just one "default" column
        if len(sample_ids_to_metadata_map.keys()) == 0:
            logger.info("No category breakdown selected - will generate a default column")
            unique_meta_vals = ["Default"]
            for sample_id in sample_labels:
                sample_ids_to_metadata_map[sample_id] = "Default"

        return self.analyse(user_request, base, headers, sample_labels, taxonomy_map, unique_meta_vals, sample_ids_to_metadata_map)

    def analyse(self, user_request, base, headers, sample_labels, taxonomy_map, unique_meta_vals, sample_ids_to_metadata_map):

        otuToColNum = {}
        j = 0
        while j < len(base[0]):
            otuToColNum[headers[j]] = j
            j += 1

        lenOfClassification = 0
        for otu, classification in taxonomy_map.items():
            lenOfClassification = len(classification)
            break

        displayValues = user_request.get_custom_attr("display_values")
        taxonomyDisplayLevel = int(user_request.get_custom_attr("taxonomy_display_level"))
        if taxonomyDisplayLevel >= lenOfClassification:
            taxonomyDisplayLevel = lenOfClassification
        elif taxonomyDisplayLevel < 0:
            taxonomyDisplayLevel = lenOfClassification

        treeObj = {}
        numLeaves = 0

        for otu, classification in taxonomy_map.items():
            # Iterate through each known OTU
            if otu in otuToColNum:
                # This is a known OTU that appears in the OTU table, inspect it further

                # A map of the metadata value to a statistic for a particular OTU
                # (ie. total non-zero counts of samples from X environment)
                otuObj = {}

                col = otuToColNum[otu]

                i = 0
                while i < len(base):
                    # Create a new OTU object, based on either the total counts or the sum of the OTU values
                    sampleID = sample_labels[i]
                    if sampleID in sample_ids_to_metadata_map:
                        metaVal = sample_ids_to_metadata_map[sampleID]
                        otuVal = float(base[i][col])
                        if displayValues == "nonzero":
                            if metaVal in otuObj:
                                if otuVal > 0:
                                    otuObj[metaVal]["c"] += 1
                                otuObj[metaVal]["tc"] += 1
                            else:
                                otuObj[metaVal] = {}
                                if otuVal > 0:
                                    otuObj[metaVal]["c"] = 1
                                else:
                                    otuObj[metaVal]["c"] = 0
                                otuObj[metaVal]["tc"] = 1
                        elif displayValues == "nonzerosample":
                            # We want to count the number of non-zero samples per group so we need to keep track
                            # of what samples had a non-zero count
                            if metaVal in otuObj:
                                if otuVal > 0:
                                    otuObj[metaVal]["c"][sampleID] = True
                                otuObj[metaVal]["tc"][sampleID] = True
                            else:
                                otuObj[metaVal] = {}
                                otuObj[metaVal]["c"] = {}
                                otuObj[metaVal]["tc"] = {}
                                if otuVal > 0:
                                    otuObj[metaVal]["c"][sampleID] = True
                                otuObj[metaVal]["tc"][sampleID] = True
                        else:
                            if metaVal in otuObj:
                                otuObj[metaVal]["v"].append(otuVal)
                            else:
                                otuObj[metaVal] = {}
                                otuObj[metaVal]["v"] = [otuVal]

                    i += 1

                classification.append(otu)

                # The user may want to exclude the unclassified OTUs (unclassified at the taxonomic display level)
                excludeUnclassified = user_request.get_custom_attr("exclude_unclassified")
                if excludeUnclassified == "yes":
                    if classification[taxonomyDisplayLevel].lower() == "unclassified" or classification[taxonomyDisplayLevel].lower() == "":
                        continue

                numLeaves += self.__treeGroupingHelper(treeObj, 0, taxonomyDisplayLevel, classification,
                                                       unique_meta_vals, otuObj, displayValues)

        # print treeObj

        # Convert to D3 readable format
        fTreeObj = {}
        fTreeObj["name"] = "root"
        fTreeObj["children"] = []
        self.__treeFormatterHelper(fTreeObj, treeObj, 0, taxonomyDisplayLevel, displayValues)
        abundancesObj = {}
        abundancesObj["metaUnique"] = unique_meta_vals
        abundancesObj["numLeaves"] = numLeaves
        abundancesObj["numSamples"] = len(sample_ids_to_metadata_map.keys())
        abundancesObj["root"] = fTreeObj
        return abundancesObj


    def __treeGroupingHelper(self, treeObj, taxLevel, taxonomyDisplayLevel, classification, uniqueMetadataVals, otuObj,
                             displayValues):
        """
        Takes a treeObj (which stores the entire tree layout as it is being built) and adds an OTU object to it. An
        OTU object contains a map of the metadata values to the count/value of the OTU. This helper method adds each
        applicable metadata to the corresponding metadata being accumulated in the treeObj.
        :param treeObj:
        :param taxLevel:
        :param taxonomyDisplayLevel:
        :param classification:
        :param uniqueMetadataVals:
        :param otuObj:
        :param displayValues:
        :return:
        """
        levelClassification = classification[taxLevel]
        if levelClassification not in treeObj:
            treeObj[levelClassification] = {}

        numLeaves = 0

        if taxonomyDisplayLevel == taxLevel:
            if "numOTUs" in treeObj[levelClassification]:
                treeObj[levelClassification]["numOTUs"] += 1
            else:
                treeObj[levelClassification]["numOTUs"] = 1

            # Associate the values
            for meta in uniqueMetadataVals:
                if meta in otuObj:
                    if "nonzero" == displayValues:
                        if meta in treeObj[levelClassification]:
                            treeObj[levelClassification][meta]["c"] += otuObj[meta]["c"]
                            treeObj[levelClassification][meta]["tc"] += otuObj[meta]["tc"]
                        else:
                            treeObj[levelClassification][meta] = {}
                            treeObj[levelClassification][meta]["c"] = otuObj[meta]["c"]
                            treeObj[levelClassification][meta]["tc"] = otuObj[meta]["tc"]
                            numLeaves = 1
                    elif "nonzerosample" == displayValues:
                        if meta in treeObj[levelClassification]:
                            # Do nothing because the non-zero samples have already been counted
                            pass
                        else:
                            treeObj[levelClassification][meta] = {}
                            treeObj[levelClassification][meta]["c"] = len(otuObj[meta]["c"].keys())
                            treeObj[levelClassification][meta]["tc"] = len(otuObj[meta]["tc"].keys())
                            numLeaves = 1
                    else:
                        if meta in treeObj[levelClassification]:
                            treeObj[levelClassification][meta]["v"].extend(otuObj[meta]["v"])
                        else:
                            treeObj[levelClassification][meta] = {}
                            treeObj[levelClassification][meta]["v"] = otuObj[meta]["v"]
                            numLeaves = 1
        else:
            return self.__treeGroupingHelper(treeObj[levelClassification], taxLevel + 1, taxonomyDisplayLevel,
                                             classification, uniqueMetadataVals, otuObj, displayValues)

        return numLeaves

    def __treeFormatterHelper(self, fTreeArr, treeObj, level, taxonomyDisplayLevel, displayValues):
        """
        Turns the treeObj (mapping of taxonomy levels to metadata values) into a tree structure that has collapsed
        the arrays of values into a single statistic (ie. the treeObj contains an array of OTU values for each
        metadata value but the output of this method could be to take an average of the array of OTU values)
        :param fTreeArr:
        :param treeObj:
        :param level:
        :param taxonomyDisplayLevel:
        :param displayValues:
        :return:
        """
        for taxa, child in treeObj.items():
            newChildObj = {}
            newChildObj["name"] = taxa
            if level == taxonomyDisplayLevel:
                if "nonzero" == displayValues or "nonzerosample" == displayValues:
                    newChildObj["val"] = child
                else:
                    # Collapse the array into specific values
                    if displayValues == "avgabun":
                        metas = list(child.keys())
                        for meta in metas:
                            if "numOTUs"  == meta:
                                # numOTUs is not an actual metadata and only used to accumulate the number of OTUs
                                continue
                            metaVals = child[meta]
                            avg = np.mean(metaVals["v"])
                            child[meta] = round(avg, 2)
                            child["c"] = len(metaVals["v"])
                            child["tc"] = len(metaVals["v"]) if "tc" not in child else len(metaVals["v"]) + child["tc"]
                    elif displayValues == "medianabun":
                        metas = list(child.keys())
                        for meta in metas:
                            if "numOTUs"  == meta:
                                # numOTUs is not an actual metadata and only used to accumulate the number of OTUs
                                continue
                            metaVals = child[meta]
                            child[meta] = np.median(metaVals["v"])
                            child["c"] = len(metaVals["v"])
                            child["tc"] = len(metaVals["v"]) if "tc" not in child else len(metaVals["v"]) + child["tc"]
                    elif displayValues == "maxabun":
                        metas = list(child.keys())
                        for meta in metas:
                            if "numOTUs"  == meta:
                                # numOTUs is not an actual metadata and only used to accumulate the number of OTUs
                                continue
                            metaVals = child[meta]
                            child[meta] = np.amax(metaVals["v"])
                            child["c"] = len(metaVals["v"])
                            child["tc"] = len(metaVals["v"]) if "tc" not in child else len(metaVals["v"]) + child["tc"]
                    else:
                        print("Unknown display value")
                        child[meta] = 0

                    newChildObj["val"] = child

            else:
                newChildObj["children"] = []
                self.__treeFormatterHelper(newChildObj, child, level + 1, taxonomyDisplayLevel, displayValues)
            fTreeArr["children"].append(newChildObj)

    # getTreeGrouping("1", "Test", 0, ["Bacteria"], "Disease", -1, "avgabun", "yes")
