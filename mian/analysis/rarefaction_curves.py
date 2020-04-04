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

import rpy2.robjects as robjects
import rpy2.rlike.container as rlc
from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage

from mian.model.otu_table import OTUTable


class RarefactionCurves(object):
    r = robjects.r

    rcode = """
    generate_rarefaction_curve <- function(base) {
        raremax <- max(rowSums(base))
        #raremax <- min(rowSums(base))
        step <- round(raremax / 100)
        
        # Writes to a NULL file because we want to suppress the graphics output
        pdf(file = NULL)
        out <- rarecurve(base, step = step, sample = raremax)
        dev.off()
        
        return(out)
    }
    """

    rStats = SignatureTranslatedAnonymousPackage(rcode, "rStats")

    def run(self, user_request):
        # Rarefaction curves are only useful on the original raw data set
        table = OTUTable(user_request.user_id, user_request.pid, True)
        base = table.get_table()
        headers = table.get_headers()
        sample_labels = table.get_sample_labels()

        if user_request.get_custom_attr("colorvar") != "None":
            color_metadata_values = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.get_custom_attr("colorvar"))
        else:
            color_metadata_values = []

        return self.analyse(base, headers, sample_labels, color_metadata_values)

    def analyse(self, base, headers, sample_labels, color_metadata_values):
        # Forms an OTU only table (without IDs)
        all_otus = []
        col = 0
        while col < base.shape[1]:
            colVals = []
            row = 0
            while row < base.shape[0]:
                colVals.append(base[row, col])
                row += 1
            all_otus.append((headers[col], robjects.FloatVector(colVals)))
            col += 1

        od = rlc.OrdDict(all_otus)
        dataf = robjects.DataFrame(od)

        rarefaction_curve_results = self.rStats.generate_rarefaction_curve(dataf)

        abun_obj = {
            "results": [],
            "maxHeader": 0,
            "maxVal": 0,
        }
        curve_index = 0
        for curve in rarefaction_curve_results:
            curve_obj = {}
            headers = []
            vals = []
            for h in curve.slots["Subsample"]:
                headers.append(h)
                if h > abun_obj["maxHeader"]:
                    abun_obj["maxHeader"] = h

            for v in curve:
                vals.append(round(v, 2))
                if v > abun_obj["maxVal"]:
                    abun_obj["maxVal"] = v

            curve_obj["headers"] = headers
            curve_obj["vals"] = vals
            curve_obj["sampleID"] = sample_labels[curve_index]
            curve_obj["color"] = color_metadata_values[curve_index] if len(color_metadata_values) == len(sample_labels) else ""
            abun_obj["results"].append(curve_obj)

            curve_index += 1

        return abun_obj

