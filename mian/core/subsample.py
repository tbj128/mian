
from mian.core.data_io import DataIO


class Subsample(object):


    @staticmethod
    def get_rarefaction(userID, projectID):
        rarefactionBase = DataIO.tsv_to_table(userID, projectID, "otuTable.groups.rarefaction")
        retVal = {}
        subsampleVals = []
        maxVal = 0
        maxSubsampleVal = 0
        maxSubsample = 10000
        j = 1
        while j < len(rarefactionBase[0]):
            if rarefactionBase[0][j].find("lci") != -1 or rarefactionBase[0][j].find("hci") != -1:
                j += 1
                continue

            newArr = []
            numNA = 0
            i = 1
            while i < len(rarefactionBase):
                if float(rarefactionBase[i][0]) > maxSubsample:
                    break

                if j == 1:
                    subsampleVals.append(float(rarefactionBase[i][0]))
                    if float(rarefactionBase[i][0]) > maxSubsampleVal:
                        maxSubsampleVal = float(rarefactionBase[i][0])

                if (rarefactionBase[i][j] == "NA"):
                    newArr.append(-1)
                    numNA += 1
                else:
                    newArr.append(float(rarefactionBase[i][j]))
                    if float(rarefactionBase[i][j]) > maxVal:
                        maxVal = float(rarefactionBase[i][j])
                i += 1

            retVal[rarefactionBase[0][j]] = newArr

            j += 1

        abundancesObj = {}
        abundancesObj["result"] = retVal
        abundancesObj["subsampleVals"] = subsampleVals
        abundancesObj["max"] = maxVal
        abundancesObj["maxSubsampleVal"] = maxSubsampleVal
        return abundancesObj

    # print getRarefaction("1", "BatchsubSequenceLevel")