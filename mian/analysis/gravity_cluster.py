from mian.analysis.analysis_base import AnalysisBase

from mian.model.otu_table import OTUTable
from mian.model.metadata import Metadata


class GravityCluster(AnalysisBase):

    def run(self, user_request):
        taxonomyGroupingGeneral = user_request.get_custom_attr("taxonomy_group_general")
        taxonomyGroupingSpecific = user_request.get_custom_attr("taxonomy_group_specific")
        if user_request.taxonomy_filter_vals is None or user_request.taxonomy_filter_vals == "" or int(
                taxonomyGroupingGeneral) >= int(taxonomyGroupingSpecific):
            return {}
        #
        # base = DataIO.tsv_to_table(user_request.user_id, user_request.pid, OTU_TABLE_NAME)
        # metadata = DataIO.tsv_to_table(user_request.user_id, user_request.pid, METADATA_NAME)
        # taxonomyMap = Taxonomy.get_taxonomy_map(user_request.user_id, user_request.pid)
        #
        # base = DataProcessor.filter_otu_table_by_metadata(base, metadata, user_request.sample_filter,
        #                                                   user_request.sample_filter_vals)

        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table = table.get_table_after_filtering_and_aggregation(user_request.sample_filter,
                                                                    user_request.sample_filter_vals,
                                                                    user_request.taxonomy_filter_vals,
                                                                    user_request.taxonomy_filter)
        metadata = table.get_sample_metadata().get_as_table()
        taxonomy_map = table.get_otu_metadata().get_taxonomy_map()

        return self.analyse(user_request, otu_table, metadata, taxonomy_map)

    def analyse(self, user_request, base, metadata, taxonomyMap):
        taxonomyGroupingGeneral = user_request.get_custom_attr("taxonomy_group_general")
        taxonomyGroupingSpecific = user_request.get_custom_attr("taxonomy_group_specific")

        # Get map of specific tax grouping to general tax grouping
        otus = {}
        otuToTaxaSpecific = {}
        taxaSpecificToOTU = {}
        taxGroupingMap = {}
        uniqueGeneralTax = []
        for otu, classification in taxonomyMap.items():
            if int(taxonomyGroupingSpecific) >= 0 and len(classification) > int(taxonomyGroupingSpecific) > int(
                    taxonomyGroupingGeneral) and int(taxonomyGroupingGeneral) < len(
                    classification):
                specificTaxa = classification[int(taxonomyGroupingSpecific)]
                generalTaxa = classification[int(taxonomyGroupingGeneral)]

                if specificTaxa not in user_request.taxonomy_filter_vals:
                    taxGroupingMap[specificTaxa] = generalTaxa

                if generalTaxa not in uniqueGeneralTax:
                    uniqueGeneralTax.append(generalTaxa)

                if specificTaxa not in taxaSpecificToOTU:
                    taxaSpecificToOTU[specificTaxa] = [otu]
                else:
                    taxaSpecificToOTU[specificTaxa].append(otu)

                otuToTaxaSpecific[otu] = specificTaxa

            if 0 <= int(user_request.level) < len(classification):
                if classification[int(user_request.level)] in user_request.taxonomy_filter_vals:
                    otus[otu] = 1
            elif int(user_request.level) == -1:
                if otu in user_request.taxonomy_filter_vals:
                    otus[otu] = 1
            else:
                otus[otu] = 1

        # Grouped by user_request.catvar, then by the (eg.) averaged phylum, then by (eg.) averaged family
        idToMetadata = Metadata.map_id_to_metadata(metadata, Metadata.get_cat_col(metadata, user_request.catvar))
        uniqueMetadataVals = Metadata.get_unique_metadata_cat_vals(metadata,
                                                                   Metadata.get_cat_col(metadata, user_request.catvar))

        # Find the OTUs that are relevant and subset the base table
        newBase = []
        i = 0
        while i < len(base):
            newRow = []
            j = OTUTable.OTU_START_COL
            while j < len(base[i]):
                if j == OTUTable.SAMPLE_ID_COL or base[0][j] in otus:
                    newRow.append(base[i][j])
                j += 1
            i += 1
            newBase.append(newRow)
        base = newBase

        # Merge the OTUs at the same taxa user_request.level
        otuToColNum = {}
        uniqueSpecificTax = []

        # base now only has sample ID as the first column
        j = 1
        while j < len(base[0]):
            otuToColNum[base[0][j]] = j
            if otuToTaxaSpecific[base[0][j]] not in uniqueSpecificTax:
                uniqueSpecificTax.append(otuToTaxaSpecific[base[0][j]])
            j += 1

        newBase = []
        i = 0
        while i < len(base):
            newRow = [base[i][0]]
            for specificTaxa in uniqueSpecificTax:
                if i > 0:
                    relevantOTUs = taxaSpecificToOTU[specificTaxa]
                    tot = 0
                    for relevantOTU in relevantOTUs:
                        if relevantOTU in otuToColNum:
                            tot += float(base[i][otuToColNum[relevantOTU]])
                    newRow.append(tot)
                else:
                    newRow.append(specificTaxa)
            i += 1
            newBase.append(newRow)
        base = newBase

        groupingPreAverage = {}

        j = 1
        while j < len(base[0]):
            taxaSpecific = base[0][j]
            taxaGeneral = taxGroupingMap[taxaSpecific]

            i = 1
            while i < len(base):
                id = base[i][0]
                metadata = idToMetadata[id]

                if taxaGeneral not in groupingPreAverage:
                    groupingPreAverage[taxaGeneral] = {}

                if taxaSpecific not in groupingPreAverage[taxaGeneral]:
                    groupingPreAverage[taxaGeneral][taxaSpecific] = {}

                if metadata not in groupingPreAverage[taxaGeneral][taxaSpecific]:
                    groupingPreAverage[taxaGeneral][taxaSpecific][metadata] = {}
                    groupingPreAverage[taxaGeneral][taxaSpecific][metadata]["tc"] = 1
                    if float(base[i][j]) > 0:
                        groupingPreAverage[taxaGeneral][taxaSpecific][metadata]["c"] = 1
                    else:
                        groupingPreAverage[taxaGeneral][taxaSpecific][metadata]["c"] = 0
                else:
                    groupingPreAverage[taxaGeneral][taxaSpecific][metadata]["tc"] += 1
                    if float(base[i][j]) > 0:
                        groupingPreAverage[taxaGeneral][taxaSpecific][metadata]["c"] += 1
                i += 1
            j += 1

        groupingPostProcess = {}
        groupingPostProcess["name"] = ""
        groupingPostProcess["children"] = []
        for taxaGeneral, taxaSpecificObj in groupingPreAverage.items():
            generalObj = {}
            generalObj["name"] = taxaGeneral
            generalObj["children"] = []
            taxaGeneralTotal = 0

            for taxaSpecific, metadataObj in taxaSpecificObj.items():
                taxaSpecificTotal = 0
                for metadata, countObj in metadataObj.items():
                    taxaGeneralTotal += countObj["c"]
                    taxaSpecificTotal += countObj["c"]

                if taxaSpecificTotal > 0:
                    specificObj = metadataObj
                    specificObj["name"] = taxaSpecific
                    generalObj["children"].append(specificObj)

            if taxaGeneralTotal > 0:
                groupingPostProcess["children"].append(generalObj)

        abundancesObj = {}
        abundancesObj["metaUnique"] = uniqueMetadataVals
        abundancesObj["root"] = groupingPostProcess
        return abundancesObj

# getAbundanceForOTUsByGrouping("1", "Test", 0, ["Bacteria"], "Disease", 1, 3)
