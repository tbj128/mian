# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#

#
# ======== R specific setup =========
#

from mian.model.otu_table import OTUTable


class EnrichedSelection(object):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table = table.get_table_after_filtering_and_aggregation(user_request.taxonomy_filter,
                                                                    user_request.taxonomy_filter_role,
                                                                    user_request.taxonomy_filter_vals,
                                                                    user_request.sample_filter,
                                                                    user_request.sample_filter_role,
                                                                    user_request.sample_filter_vals,
                                                                    user_request.level)

        sample_metadata = table.get_sample_metadata()
        sample_ids_to_metadata_map = table.get_sample_metadata().get_sample_id_to_metadata_map(user_request.catvar)
        taxonomy_map = table.get_otu_metadata().get_taxonomy_map()

        return self.analyse(user_request, otu_table, sample_metadata, taxonomy_map, sample_ids_to_metadata_map)

    def analyse(self, user_request, base, sample_metadata, taxonomyMap, metaIDs):
        percentAbundanceThreshold = user_request.get_custom_attr("enrichedthreshold")
        catVar1 = user_request.get_custom_attr("pwVar1")
        catVar2 = user_request.get_custom_attr("pwVar2")

        otuTablePercentAbundance = self.__convert_to_percent_abundance(base, float(percentAbundanceThreshold))
        otuTableCat1, otuTableCat2 = self.__separate_into_groups(otuTablePercentAbundance, sample_metadata,
                                                                 user_request.catvar, catVar1, catVar2)

        otuTableCat1 = self.__keep_only_otus(otuTableCat1, metaIDs)
        otuTableCat2 = self.__keep_only_otus(otuTableCat2, metaIDs)

        diff1 = self.__diff_base(otuTableCat1, otuTableCat2)
        diff2 = self.__diff_base(otuTableCat2, otuTableCat1)

        diff1Arr = []
        for d in diff1:
            dObj = {}
            if int(user_request.level) == -1:
                dObj["t"] = d
                dObj["c"] = ', '.join(taxonomyMap[d])
            else:
                dObj["t"] = d
                dObj["c"] = ""
            diff1Arr.append(dObj)

        diff2Arr = []
        for d in diff2:
            dObj = {}
            if int(user_request.level) == -1:
                dObj["t"] = d
                dObj["c"] = ', '.join(taxonomyMap[d])
            else:
                dObj["t"] = d
                dObj["c"] = ""
            diff2Arr.append(dObj)

        abundancesObj = {}
        abundancesObj["diff1"] = diff1Arr
        abundancesObj["diff2"] = diff2Arr

        return abundancesObj

    # Helpers

    def __convert_to_percent_abundance(self, base, perThreshold):
        baseNew = []
        OTU_START = OTUTable.OTU_START_COL

        i = 0
        for row in base:
            if i == 0:
                baseNew.append(row)
            else:
                newRow = []
                colNum = OTU_START
                rowSum = 0
                # Find top OTUs per row
                while colNum < len(row):
                    # Is this an OTU of interest?
                    rowSum = rowSum + float(row[colNum])
                    colNum = colNum + 1

                colNum = 0
                while colNum < len(row):
                    if colNum >= OTU_START and rowSum > 0:
                        # Is this an OTU of interest?
                        per = float(row[colNum]) / float(rowSum)
                        if per > perThreshold:
                            newRow.append(float(per))
                        else:
                            newRow.append(float(0))
                    else:
                        newRow.append(row[colNum])
                    colNum = colNum + 1

                baseNew.append(newRow)

            i = i + 1
        return baseNew

    def __diff_base(self, a, b):
        colNumToOTU = {}
        aOTUs = set()
        bOTUs = set()
        i = 0
        for row in a:
            if i == 0:
                colNum = 0
                while colNum < len(row):
                    colNumToOTU[colNum] = row[colNum]
                    colNum = colNum + 1
            else:
                colNum = 0
                while colNum < len(row):
                    if row[colNum] > 0:
                        if colNumToOTU[colNum] not in aOTUs:
                            aOTUs.add(colNumToOTU[colNum])
                    colNum = colNum + 1
            i = i + 1

        i = 0
        for row in b:
            if i == 0:
                colNum = 0
                while colNum < len(row):
                    colNumToOTU[colNum] = row[colNum]
                    colNum = colNum + 1
            else:
                colNum = 0
                while colNum < len(row):
                    if row[colNum] > 0:
                        if colNumToOTU[colNum] not in bOTUs:
                            bOTUs.add(colNumToOTU[colNum])
                    colNum = colNum + 1
            i = i + 1

        return self.__diff(aOTUs, bOTUs)

    def __diff(self, a, b):
        return [aa for aa in a if aa not in b]

    def __separate_into_groups(self, base, sample_metadata, catvar, catCol1, catCol2):
        catvar_col = sample_metadata.get_metadata_column_number(catvar)
        cat_col1_samples = {}
        cat_col2_samples = {}

        base_metadata = sample_metadata.get_as_table()
        i = 1
        while i < len(base_metadata):
            if base_metadata[i][catvar_col] == catCol1:
                cat_col1_samples[base_metadata[i][0]] = 1
            if base_metadata[i][catvar_col] == catCol2:
                cat_col2_samples[base_metadata[i][0]] = 1
            i += 1

        base_cat1 = []
        base_cat2 = []
        i = 0
        for o in base:
            if i == 0:
                base_cat1.append(o)
                base_cat2.append(o)
            else:
                if o[OTUTable.SAMPLE_ID_COL] in cat_col1_samples:
                    base_cat1.append(o)
                elif o[OTUTable.SAMPLE_ID_COL] in cat_col2_samples:
                    base_cat2.append(o)
            i = i + 1
        return base_cat1, base_cat2

    def __keep_only_otus(self, base, metaIDs):
        newBase = []
        i = 0
        for o in base:
            sampleID = base[i][OTUTable.SAMPLE_ID_COL]
            if i == 0 or sampleID in metaIDs:
                newRow = []
                j = OTUTable.OTU_START_COL
                while j < len(o):
                    newRow.append(o[j])
                    j += 1
                newBase.append(newRow)
            i += 1
        return newBase

    # enrichedSelection("1", "BatchsubOTULevel", 7, "All", "Disease", "IPF", "Control", 0.25)
