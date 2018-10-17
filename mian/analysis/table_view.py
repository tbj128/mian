# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#

from mian.analysis.analysis_base import AnalysisBase

from mian.model.otu_table import OTUTable

class TableView(AnalysisBase):
    """
    Returns the data in a table format
    """

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        base, headers, sample_labels = table.get_table_after_filtering(user_request)

        return self.analyse(base, headers, sample_labels)

    def analyse(self, base, headers, sample_labels):
        new_headers = ["Sample"]
        new_headers.extend(headers)
        otu_table = [new_headers]

        i = 0
        while i < len(base):
            new_row = [sample_labels[i]]
            j = 0
            while j < len(base[i]):
                new_row.append(float(base[i][j]))
                j += 1
            otu_table.append(new_row)
            i += 1
        return otu_table
