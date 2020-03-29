# Taxonomic Tree View

Renders a taxonomic tree up until the specified taxonomic level. At the lowest taxonomic level, the tree shows either the non-zero count or the mean/median/max abundances of all OTU-Samples that fall under the taxonomic group.

Because each taxonomic group can contain one or more OTUs, the OTU-Sample unit is defined as the product of the number of OTUs under the taxonomic group and the number of samples.

![](.gitbook/assets/image%20%2814%29.png)

### Used For

* Comparing taxonomic abundances across the taxonomic tree and between each sample group. For instance, you can tell at a glance which taxonomic families are enriched in the control group across a single phylum

### Visualization Notes

* Renders a taxonomic tree up until the specified taxonomic level. At the lowest taxonomic level, the tree shows either the non-zero count or the mean/median/max abundances of all OTU-Samples that fall under the taxonomic group for a hierarchical comparison.
* The bigger the dot, the more abundant the corresponding taxonomic group

{% hint style="info" %}
The taxonomic tree can be very large. Using the "Data Filtering" options to zoom into a specific taxonomic region of interest.
{% endhint %}

### Visualization Parameters

#### Categorical Variable

Create comparative sample groups based on categorical variables uploaded in the metadata file. 

Optionally create a categorical variable from a quantitative variable by using the Quantile Range feature on the Projects home page. 

Each sample group is assigned its own color.

#### Taxonomic Level

The taxonomic level to aggregate the OTUs at. Due to the possible size of the tree, you should either first filter for the taxonomic groups of interest or choose a less granular taxonomic level.

#### Metric

* **Non-Zero OTU-Sample Counts** The number of OTU-samples with a non-zero count for the indicated taxonomic group. The OTU-sample represents the product of the number of samples and the number of OTUs that fall under the taxonomic group.
* **Non-Zero Sample Counts** The number of samples with a non-zero count for the indicated taxonomic group
* **Mean OTU-Sample Abundance** The mean of the counts across all samples and OTUs that fall under the indicated taxonomic group
* **Median OTU-Sample Abundance** The median of the counts across all samples and OTUs that fall under the indicated taxonomic group
* **Max OTU-Sample Abundance** The max of the counts across all samples and OTUs that fall under the indicated taxonomic group

#### Exclude Unclassified

* **Yes** Ignores all counts coming from OTUs unclassified at the specified taxonomic level
* **No** Include counts from all OTUs

### Interactive Elements

* Hover over each point to determine the sample ID and the following measures:
  * **Non-Zero Count**: Number of OTU-Samples which had a non-zero count \(with respect to a particular sample group\)
  * **Number of OTUs:** The number of OTUs that exist under a particular taxonomic leaf
  * **Number of Samples:** The number of samples that exist under a particular sample group

{% hint style="info" %}
**OTU-Sample**: Because each taxonomic group can contain one or more OTUs, the OTU-Sample unit is defined as the product of the number of OTUs under the taxonomic group and the number of samples.
{% endhint %}

### Additional Features

* **Save Snapshot**: Save the visualization to the experiment notebook
* **Download**: Downloads the visualization as a PNG file
* **Share**: Creates a shareable link that allows you to share the visualization with others

