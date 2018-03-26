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

from mian.analysis.analysis_base import AnalysisBase

from mian.model.otu_table import OTUTable
from mian.model.metadata import Metadata


class TreeView(AnalysisBase):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table = table.get_table_after_filtering_and_aggregation(user_request.sample_filter,
                                                                    user_request.sample_filter_vals,
                                                                    user_request.taxonomy_filter_vals,
                                                                    user_request.taxonomy_filter)
        metadata = table.get_sample_metadata().get_as_table()
        taxonomy_map = table.get_otu_metadata().get_taxonomy_map()

        return self.analyse(user_request, otu_table, metadata, taxonomy_map)

    def analyse(self, user_request, base, metadata, taxonomyMap):

        idToMetadata = Metadata.map_id_to_metadata(metadata, Metadata.get_cat_col(metadata, user_request.catvar))
        uniqueMetadataVals = Metadata.get_unique_metadata_cat_vals(metadata,
                                                                   Metadata.get_cat_col(metadata, user_request.catvar))

        otuToColNum = {}
        j = OTUTable.OTU_START_COL
        while j < len(base[0]):
            otuToColNum[base[0][j]] = j
            j += 1

        lenOfClassification = 0
        for otu, classification in taxonomyMap.items():
            lenOfClassification = len(classification)
            break

        taxonomyDisplayLevel = int(user_request.get_custom_attr("taxonomy_display_level"))
        if taxonomyDisplayLevel >= lenOfClassification:
            taxonomyDisplayLevel = lenOfClassification
        elif taxonomyDisplayLevel < 0:
            taxonomyDisplayLevel = lenOfClassification

        treeObj = {}
        numLeaves = 0

        for otu, classification in taxonomyMap.items():
            if otu in otuToColNum:
                otuObj = {}

                col = otuToColNum[otu]

                i = 1
                while i < len(base):
                    sampleID = base[i][OTUTable.SAMPLE_ID_COL]
                    if sampleID in idToMetadata:
                        metaVal = idToMetadata[sampleID]
                        otuVal = float(base[i][col])
                        displayValues = user_request.get_custom_attr("display_values")
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
                    if classification[taxonomyDisplayLevel].lower() == "unclassified":
                        continue

                numLeaves += self.__treeGroupingHelper(treeObj, 0, taxonomyDisplayLevel, classification,
                                                       uniqueMetadataVals, otuObj, displayValues)

        # print treeObj

        # Convert to D3 readable format
        fTreeObj = {}
        fTreeObj["name"] = "root"
        fTreeObj["children"] = []
        self.__treeFormatterHelper(fTreeObj, treeObj, 0, taxonomyDisplayLevel, displayValues)
        # print fTreeObj
        abundancesObj = {}
        abundancesObj["metaUnique"] = uniqueMetadataVals
        abundancesObj["numLeaves"] = numLeaves
        abundancesObj["root"] = fTreeObj
        return abundancesObj

    def __treeGroupingHelper(self, treeObj, taxLevel, taxonomyDisplayLevel, classification, uniqueMetadataVals, otuObj,
                             displayValues):
        levelClassification = classification[taxLevel]
        if levelClassification not in treeObj:
            treeObj[levelClassification] = {}

        numLeaves = 0

        if taxonomyDisplayLevel == taxLevel:
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
        for taxa, child in treeObj.items():
            newChildObj = {}
            newChildObj["name"] = taxa
            if level == taxonomyDisplayLevel:
                if "nonzero" == displayValues:
                    newChildObj["val"] = child
                else:
                    # Collapse the array into specific values
                    if displayValues == "avgabun":
                        metas = list(child.keys())
                        for meta in metas:
                            metaVals = child[meta]
                            avg = np.mean(metaVals["v"])
                            child[meta] = round(avg, 2)
                            child["tc"] = len(metaVals["v"])
                    elif displayValues == "medianabun":
                        metas = list(child.keys())
                        for meta in metas:
                            metaVals = child[meta]
                            child[meta] = np.median(metaVals["v"])
                            child["tc"] = len(metaVals["v"])
                    elif displayValues == "maxabun":
                        metas = list(child.keys())
                        for meta in metas:
                            metaVals = child[meta]
                            child[meta] = np.amax(metaVals["v"])
                            child["tc"] = len(metaVals["v"])
                    else:
                        print("Unknown display value")
                        child[meta] = 0

                    newChildObj["val"] = child

            else:
                newChildObj["children"] = []
                self.__treeFormatterHelper(newChildObj, child, level + 1, taxonomyDisplayLevel, displayValues)
            fTreeArr["children"].append(newChildObj)

    # getTreeGrouping("1", "Test", 0, ["Bacteria"], "Disease", -1, "avgabun", "yes")
