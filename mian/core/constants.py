#
# Global Attributes
#

SUBSAMPLE_TYPE_AUTO = "auto"
SUBSAMPLE_TYPE_MANUAL = "manual"
SUBSAMPLE_TYPE_TSS = "tss"
SUBSAMPLE_TYPE_UQ = "uq"
SUBSAMPLE_TYPE_CSS = "css"
SUBSAMPLE_TYPE_DISABLED = "no"

# The raw uploaded .biom file (if applicable)
BIOM_FILENAME = "table.biom"

# The raw table reads (numerical values only)
RAW_OTU_TABLE_FILENAME = "table.raw.npz"

# The table header and the row labels (by separating the OTU table
# and the labels, we get to take advantage of matrix transformations)
RAW_OTU_TABLE_LABELS_FILENAME = "table.raw.labels.tsv"

# The raw table after having been subsampled (numerical values only)
SUBSAMPLED_OTU_TABLE_FILENAME = "table.subsampled.npz"

# The table header and the row labels (by separating the OTU table
# and the labels, we get to take advantage of matrix transformations)
SUBSAMPLED_OTU_TABLE_LABELS_FILENAME = "table.subsampled.labels.tsv"

# The taxonomy file to explain the OTU table columns
TAXONOMY_FILENAME = "taxonomy.tsv"

# The sample metadata file
SAMPLE_METADATA_FILENAME = "sample_metadata.tsv"

# The gene expression file ordered in the same order as the OTU table (optional)
# Rows are samples, columns are genes
GENE_FILENAME = "gene.txt"

# The gene expression labels file containing the genes (optional)
# First row is the headers (genes), second row is the sample labels
GENE_LABELS_FILENAME = "gene.labels.txt"

# The phylogenetic tree file (optional)
PHYLOGENETIC_FILENAME = "phylogenetic.tre"

