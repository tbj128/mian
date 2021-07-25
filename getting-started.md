# Getting Started

## Create Your Account

Signing up is easy. Provide an email and password - your account is used to store your data and associated experiment notebooks. 

You can permanently delete you data at any time. 

Alternatively, try the demo account.

## Starting From dada2 Pipeline \(ASV table\)

If you are following the dada2 tutorial \([https://benjjneb.github.io/dada2/tutorial.html](https://benjjneb.github.io/dada2/tutorial.html)\) to create an ASV table, note the following instructions when creating the input to Mian.

Because, Mian will require a CSV or TSV file input, so we need to save some of the objects that dada2 produces. These steps assume you have completed the tutorial up to the "Assign Taxonomy" step:

* Save the filtered ASV table:  `write.csv(seqtab.nochim, "<some output directory>/seqtab.csv")`
* Save the taxonomy file:  `write.csv(taxa, "<some output directory>/seqtab.csv")`

Note that you will still need to create a sample metadata file following the format below.

## Create a Project

Mian accepts two commonly-used input formats: BIOM and TSV/CSV files - switch between them using the toggle at the top.

Certain metadata files are common to both formats. 

#### BIOM

[BIOM](http://biom-format.org/) is a commonly-used biological matrix file format that contains both the OTU/ASV data file and the taxonomy information. 

You can either include the sample metadata in the BIOM file or upload it in a separate file.

#### OTU or ASV Table \(TSV/CSV\)

{% hint style="info" %}
Sample IDs should be consistent with the metadata files
{% endhint %}

This file must be one of the following formats. The former is a .shared file produced by mothur, the latter is a manually created OTU/ASV file.

Counts should be integers. Headers are required \(OTU/ASV names taken from headers\).

Subsampling is optional \(further subsampling will be an option in the next step\).

```
label	Group	numOtus	Otu01	Otu02	Otu03	Otu04	Otu05	...
0.03	1a	35	0	5	2	3	3	...
0.03	1b	45	7	2	5	1	1	...
```

```text
Sample	Otu01	Otu02	Otu03	Otu04	Otu05	...
1a	0	5	2	3	3	...
1b	7	2	5	1	1	...
```

#### Sample Metadata

{% hint style="info" %}
Ensure that this file contains metadata for each of the samples in the OTU table AND the sample IDs are consistently used, otherwise the pre-processing may fail.
{% endhint %}

This file should contain any categorical or quantitative metadata specific to each sample. TSV or CSV.

The first row is the header. The headers will be converted to filters. 

```
Sample	body_site	disease	CD8	...
1a	gut		Disease	9.352	...
1b	skin		Control	11.242	...
...
```

#### OTU/ASV Taxonomy Mapping

{% hint style="info" %}
OTU names should be consistent with the uploaded OTU file
{% endhint %}

TSV or CSV taxonomy file with each row representing an OTU and its corresponding taxonomy information. Not applicable for BIOM-type uploads. Several taxonomy file contents are accepted:

Example [mothur constaxonomy file](https://www.mothur.org/wiki/Constaxonomy_file):

```text
OTU	Size	Taxonomy
Otu01	35	k__Bacteria;p__Firmicutes;c__Clostridia;o__Halbiales;f__Halbiaceae;g__Halbium;s__conlense
Otu02	45	k__Bacteria;p__Cyanobacteria;c__Nosphycideae;o__Nostocales;f__Nostoceae;g__Dolichospermum
...
```

Example Taxonomy File \(GreenGenes or Silva Taxonomy String\):

```text
OTU	taxonomy
Otu01	k__Bacteria;p__Firmicutes;c__Clostridia;o__Halbiales;f__Halbiaceae;g__Halbium;s__conlense
Otu02	k__Bacteria;p__Cyanobacteria;c__Nosphycideae;o__Nostocales;f__Nostoceae;g__Dolichospermum
...
```

Example Taxonomy File \(decomposed taxonomy\):

```text
OTU	kingdom		phylum		class		order		family		genus		species
Otu01	Bacteria	Firmicutes	Clostridia	Halbiales	Halbiaceae	Halbium		conlense
Otu02	Bacteria	Cyanobacteria	Nosphycideae	Nostocales	Nostoceae	Dolichospermum
...
```

#### Gene Expression Matrix

{% hint style="info" %}
Sample IDs should be consistent with the uploaded OTU file
{% endhint %}

If you have access to gene expression data \(eg. your study involves a human subject and you have access to microarray data\), optionally include a TSV or CSV gene expression matrix file where the rows are the genes and each column is a sample. 

Every sample in the OTU file must be present in this file.

```text
Gene	1a	1b	1c	...
TLR1	1.2891	2.3992	1.2293	...
TLR2	6.2894	9.5196	9.0199	...
IL8R	3.7991	4.1968	2.3449	...
...
```

#### Phylogenetic Tree

Newick-formatted phylogenetic tree, where the leaves are the OTUs from the OTU table. This is only needed if you want to use [Unifrac](https://en.wikipedia.org/wiki/UniFrac) distances in your analysis. Note that not all OTU-picking pipelines will produce a phylogenetic tree.

```text
(((((('sepal_width':1)Streptococcus:1)Streptococcaceae:1)Lactobacillales:1,((('petal_width':1)AAAAA:1)Blah:1,(('petal_length':1)Staphylococcus:1)Staphylococcaceae:1)Bacillales:1)Bacilli:1)Firmicutes:1,((((('sepal_length':1)Prevotella:1)Prevotellaceae:1)Bacteroidales:1)Bacteroidia:1)Bacteroidetes:1)Bacteria:1;
```

## Project Pre-Processing

After uploading the files, you'll be directed to page that looks like the following. 

The left panel previews the OTU count for each sample after applying the selected normalization - ensure this is what you expect. Here, 67 samples are subsampled to 676. 

If auto-subsampling produces a low number, your data might have outliers. Optionally choose to remove these outliers or define your own subsampling threshold.

Subsampling OTU tables is a point of contention in the research community \([1](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003531), [2](https://www.polarmicrobes.org/how-i-learned-to-stop-worrying-and-love-subsampling-rarifying/)\), but is recommended here for comparative analysis. You may choose to proceed without normalization.

![](.gitbook/assets/image%20%281%29%20%281%29.png)



