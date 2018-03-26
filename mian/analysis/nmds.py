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
import os
from rpy2.robjects.packages import importr
import rpy2.robjects as robjects
import rpy2.rlike.container as rlc
from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage

from mian.util import ROOT_DIR
from mian.model.otu_table import OTUTable


class NMDS(object):
    rprint = robjects.globalenv.get("print")
    grdevices = importr('grDevices')
    base = importr('base')
    lattice = importr('lattice')
    vegan = importr('vegan')

    r = robjects.r

    #
    # ======== Main code begins =========
    #

    rcode = """
    library("RColorBrewer")

    plot_NMDS <- function(example_NMDS, groups, colors) {
        cols <- brewer.pal(length(unique(groups)),"Set1")
        names(cols) = levels(groups)
        # ordiplot(example_NMDS,type="points",display="species")
        ordiplot(example_NMDS,type="n")
         legend("topright",legend=unique(groups), cex=.8, col=cols, pch=15, lty=0)
        for(i in unique(groups)) {
            # orditorp(example_NMDS,display="species",pch=".",col="red",air=0.01)
            orditorp(example_NMDS$point[grep(i,groups),],display="sites",col=colors[grep(i,groups)],air=0.01)
              ordihull(example_NMDS$point[grep(i,groups),],draw="polygon", groups=groups[groups==i],col=colors[grep(i,groups)],label=F)
        }
    }

    get_colors <- function(groups) {
        cols <- brewer.pal(length(unique(groups)),"Set1")
        names(cols) = levels(groups)
        colors = c()
        for (g in groups) {
            colors = c(colors, cols[g])
        }
        return(colors)
    }
    """

    rViz = SignatureTranslatedAnonymousPackage(rcode, "rViz")

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table = table.get_table_after_filtering_and_aggregation(user_request.sample_filter,
                                                                    user_request.sample_filter_vals,
                                                                    user_request.taxonomy_filter_vals,
                                                                    user_request.taxonomy_filter)
        metadata_vals = table.get_sample_metadata().get_metadata_in_otu_table_order(user_request.catvar)
        sample_ids_to_metadata_map = table.get_sample_metadata().get_sample_id_to_metadata_map(user_request.catvar)
        return self.analyse(user_request, otu_table, metadata_vals, sample_ids_to_metadata_map)

    def analyse(self, user_request, otuTable, metaVals, metaIDs):
        groups = robjects.FactorVector(robjects.StrVector(metaVals))

        # Forms an OTU only table (without IDs)
        allOTUs = []
        col = OTUTable.OTU_START_COL
        while col < len(otuTable[0]):
            colVals = []
            row = 1
            while row < len(otuTable):
                sampleID = otuTable[row][OTUTable.SAMPLE_ID_COL]
                if sampleID in metaIDs:
                    colVals.append(otuTable[row][col])
                row += 1
            allOTUs.append((otuTable[0][col], robjects.FloatVector(colVals)))
            col += 1

        od = rlc.OrdDict(allOTUs)
        dataf = robjects.DataFrame(od)
        example_NMDS = self.vegan.metaMDS(dataf, k=2)  # The number of reduced dimensions

        # print example_NMDS$points
        # print example_NMDS$species

        colors = self.rViz.get_colors(groups)

        project_dir = ROOT_DIR
        project_dir = os.path.join(project_dir, "static")
        project_dir = os.path.join(project_dir, "tmp")
        project_dir = os.path.join(project_dir, user_request.user_id)
        project_dir = os.path.join(project_dir, user_request.pid)

        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

        fn = os.path.join(project_dir, "nmds.png")

        self.grdevices.png(file=fn, width=640, height=640)
        self.rViz.plot_NMDS(example_NMDS, groups, colors)
        self.grdevices.dev_off()

        abundancesObj = {}
        abundancesObj["fn"] = "static/tmp/" + str(user_request.user_id) + "/" + str(user_request.pid) + "/nmds.png"
        return abundancesObj

    # pca("1", "Test", 0, ["Bacteria"], "Disease", 1, 3)
    # nmds("1", "Test", 0, ["Bacteria"], "Disease", 1, 3)
