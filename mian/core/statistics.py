from scipy import stats, math


class Statistics(object):

    @staticmethod
    def getTtest(stats_abundances):
        # Calculate the statistical p-value
        statistics = []
        abundanceKeys = list(stats_abundances.keys())

        i = 0
        while i < len(abundanceKeys):
            j = i + 1
            while j < len(abundanceKeys):
                stat = {}
                stat["c1"] = abundanceKeys[i]
                stat["c2"] = abundanceKeys[j]

                # Check if both are completely zero (otherwise will break ttest)
                allZeros = True
                for x in stats_abundances[abundanceKeys[i]]:
                    if x != 0:
                        allZeros = False
                        break
                for x in stats_abundances[abundanceKeys[j]]:
                    if x != 0:
                        allZeros = False
                        break

                if allZeros == False and len(stats_abundances[abundanceKeys[i]]) > 0 and len(
                        stats_abundances[abundanceKeys[j]]) > 0:
                    t, pvalue = stats.ttest_ind(stats_abundances[abundanceKeys[i]], stats_abundances[abundanceKeys[j]], 0,
                                                False)
                    if not math.isnan(pvalue):
                        stat["pval"] = pvalue
                        statistics.append(stat)
                else:
                    stat["pval"] = 1
                    statistics.append(stat)

                j += 1
            i += 1
        return statistics