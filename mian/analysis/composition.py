import logging

from mian.analysis.analysis_base import AnalysisBase

from mian.model.otu_table import OTUTable


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Composition(AnalysisBase):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        base, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        metadata_values = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.catvar)

        return self.analyse(user_request, base, headers, sample_labels, metadata_values)

    def analyse(self, user_request, base, headers, sample_labels, metadata_values):
        plotType = user_request.get_custom_attr("plotType")
        xaxis = user_request.get_custom_attr("xaxis")
        if xaxis == "Taxonomic":
            return self.analyse_taxonomic_groups(user_request, base, headers, sample_labels, metadata_values)
        else:
            return self.analyse_metadata(user_request, base, headers, sample_labels, metadata_values)

    def analyse_metadata(self, user_request, base, headers, sample_labels, metadata_values):
        """
        Return the composition such that the selected metadata or sample ID are on the X-axis
        """

        # Populate the xAxisVals, which contains all the unique metadata variables that will
        # be displayed on the x-axis
        xAxisVals = {}
        if user_request.catvar == "none":
            # Add all of the sample IDs to the column "All"
            xAxisVals["All"] = sample_labels
        elif user_request.catvar == "SampleID":
            for s in sample_labels:
                xAxisVals[s] = [s]
        else:
            # Column 0 in metadata is the desired column
            i = 0
            while i < len(metadata_values):
                if metadata_values[i] not in xAxisVals:
                    xAxisVals[metadata_values[i]] = []
                xAxisVals[metadata_values[i]].append(sample_labels[i])
                i += 1

        # Make a sample ID to OTU table row
        sampleIDToRowIndex = {}
        i = 0
        while i < len(sample_labels):
            sampleIDToRowIndex[sample_labels[i]] = i
            i += 1

        headerToId = {}
        i = 0
        for header in headers:
            headerToId[header] = i
            i += 1

        headerToTotalVal = {}
        output = []

        for key, samples in xAxisVals.items():
            # Display the average abundance of each taxonomic group across all samples in this metadata grouping
            headerToVal = {}
            j = 0
            for header in headers:
                headerIndex = headerToId[header]

                valsSum = 0
                valsTot = 0
                for sample in samples:
                    if sample not in sampleIDToRowIndex:
                        logger.warning("Sample is missing from the OTU table: " + str(sample))
                        continue
                    rowIndex = sampleIDToRowIndex[sample]
                    valsSum += base[rowIndex, j].item()
                    valsTot += 1

                avgVal = 0
                if valsTot > 0:
                    avgVal = round(valsSum / float(valsTot), 3)

                headerToVal[headerIndex] = {
                    "sum": valsSum,
                    "tot": valsTot,
                    "avgVal": avgVal
                }

                if header not in headerToTotalVal:
                    headerToTotalVal[headerIndex] = 0
                headerToTotalVal[headerIndex] += avgVal

                j += 1

            output.append({
                "t": key,
                "o": headerToVal
            })

        sortedVals = sorted(headerToTotalVal.items(), key=lambda kv: kv[1], reverse=True)
        i = 0
        while i < len(sortedVals):
            sortedVals[i] = list(sortedVals[i])
            i += 1

        return create_abundance_obj(output, sortedVals, headerToId)


    def analyse_taxonomic_groups(self, user_request, base, headers, sample_labels, metadata_values):
        """
        Return the composition such that the taxonomic groups are on the X-axis
        """
        # Maps the ID to the metadata value
        metadataMap = {}
        uniqueMetadataVals = {}
        metadataToId = {}

        # Extracts the unique metadata values
        i = 0
        while i < len(sample_labels):
            sample = sample_labels[i]
            if len(metadata_values) == 0:
                metadataMap[sample] = "All"
                uniqueMetadataVals["All"] = True
                metadataToId["All"] = 0
            else:
                metadata_val = metadata_values[i]
                metadataMap[sample] = metadata_val
                uniqueMetadataVals[metadata_val] = True
                if metadata_val not in metadataToId:
                    metadataToId[metadata_val] = len(metadataToId.keys())

            i += 1

        # Get a map of OTUs to their sum by group
        sumByOTU = {}

        j = 0
        while j < len(headers):
            i = 0
            otuSumsByGroup = {}
            for k,v in uniqueMetadataVals.items():
                otuSumsByGroup[k] = 0

            while i < base.shape[0]:
                sampleID = sample_labels[i]
                otuSumsByGroup[metadataMap[sampleID]] += base[i, j].item()
                i += 1
            otu = headers[j]
            sumByOTU[otu] = otuSumsByGroup
            j += 1

        totalByGroup = {}
        for k,v in uniqueMetadataVals.items():
            totalByGroup[k] = 0
            for otu,otuSumsByGroup in sumByOTU.items():
                # Adds up all the OTUs (by group)
                totalByGroup[k] += otuSumsByGroup[k]

        metadataToTotalVal = {}
        formattedCompositionAbun = []
        for otu,otuSumsByGroup in sumByOTU.items():
            relativeAbunObj = {}
            for k,v in uniqueMetadataVals.items():
                id = metadataToId[k] # Use ID to reduce space during transmission
                if totalByGroup[k] != 0:
                    relativeAbun = round(otuSumsByGroup[k] / float(totalByGroup[k]), 3)
                else:
                    relativeAbun = 0

                # Calculate the total val for each metadata (just so we can return the top metadata in each category)
                if k not in metadataToTotalVal:
                    metadataToTotalVal[id] = 0
                metadataToTotalVal[id] += relativeAbun

                relativeAbunObj[id] = {
                    "sum": otuSumsByGroup[k],
                    "tot": totalByGroup[k],
                    "avgVal": relativeAbun
                }

            newObj = {"t": otu, "o": relativeAbunObj}
            formattedCompositionAbun.append(newObj)

        sortedVals = sorted(metadataToTotalVal.items(), key=lambda kv: kv[1], reverse=True)
        i = 0
        while i < len(sortedVals):
            sortedVals[i] = list(sortedVals[i])
            i += 1

        return create_abundance_obj(formattedCompositionAbun, sortedVals, metadataToId)


def create_abundance_obj(abundances, unique_vals, metadata_to_id):
    ids_to_remove = {}
    # First assume we will remove all of the IDs.
    for id, v in metadata_to_id.items():
        ids_to_remove[v] = True

    # Remove any IDs from the above 'to-remove' map if it has a non-zero value
    for abundance in abundances:
        for id, val in abundance["o"].items():
            if val["avgVal"] > 0 and id in ids_to_remove:
                del ids_to_remove[id]

    # Apply the 'to-remove' map to remove noise from the ids that do not contribute meaningfully to the actual bar graph

    i = len(abundances) - 1
    while i >= 0:
        abundance = abundances[i]
        keys = list(abundance["o"].keys())
        total_val = 0
        j = 0
        while j < len(keys):
            id = keys[j]
            if id in ids_to_remove:
                del abundance["o"][id]
            else:
                total_val += abundance["o"][id]["avgVal"]
            j += 1
        if total_val == 0:
            del abundances[i]

        i -= 1

    i = len(unique_vals) - 1
    while i >= 0:
        if unique_vals[i][0] in ids_to_remove:
            del unique_vals[i]
        i -= 1

    id_to_metadata = reverse_map(metadata_to_id)
    for id,v in ids_to_remove.items():
        del id_to_metadata[id]

    abundances_obj = {
        "abundances": abundances,
        "uniqueVals": unique_vals,
        "idMap": id_to_metadata
    }
    return abundances_obj


def reverse_map(map):
    new_map = {}
    for k,v in map.items():
        new_map[v] = k
    return new_map

