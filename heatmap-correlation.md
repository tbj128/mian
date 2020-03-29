# Heatmap \(Correlation\)

Generates a heatmap of the Pearson product-moment correlation matrix \(grouped at the indicated taxonomic level\). Correlations are calculated across all samples - apply a sample filter if you wish to correlate only on specific groups of samples.

![](.gitbook/assets/image%20%281%29.png)

### Used For

* Viewing the pair-wise correlations between:
  * All OTUs or taxonomic groups 
  * All quantitative metadata
  * Alpha diversity

{% hint style="info" %}
This tool differs from the scatterplot by determining pair-wise correlations of all possible variables. As such, filtering is automatically applied to reduce the number correlations rendered.
{% endhint %}

### Visualization Parameters

#### Taxonomic Level

The taxonomic level to aggregate the OTUs at. The OTUs will be grouped together \(by summing the OTU values\) at the selected taxonomic level before the analysis is applied.

#### Correlation Variable 1

The quantitative variable to display on the columns:

* **Taxonomic Group or OTU** All taxonomic groups or OTUs after non-zero count and prevalence filtering
* **Sample Metadata** All quantitative metadata will be displayed
* **Alpha Diversity** The alpha diversity will be displayed \(results in a single column\). You can specify the specific diversity measure in the options that will appear.

#### Correlation Variable 2

The quantitative variable to display on the rows:

* **Taxonomic Group or OTU** All taxonomic groups or OTUs after non-zero count and prevalence filtering
* **Sample Metadata** All quantitative metadata will be displayed
* **Alpha Diversity** The alpha diversity will be displayed \(results in a single row\). You can specify the specific diversity measure in the options that will appear.

#### Cluster

Determines whether columns and rows that are highly correlated should be grouped close together in the heatmap.

#### Show Labels

Hiding labels makes the heatmap smaller, useful for large heatmaps.

* **Show All Labels** Show the labels on both the rows and columns
* **Show X-Axis Labels Only** Labels only appear on the columns
* **Show Y-Axis Labels Only** Labels only appear on the rows
* **Hide Labels** No labels will appear

#### Min Number of Non-Zero Samples

This is the minimum number of non-zero samples that the correlation variable needs to have to be included in the correlation matrix. This reduces noise from samples that do not contribute meaningfully because they mostly contain zero-values.

#### Color Scheme

Choose the specific color scheme of the heatmap

### Interactive Elements

* Hover over each cell to determine its row and column label and its specific correlation value.

### Additional Features

* **Save Snapshot**: Save the visualization to the experiment notebook
* **Download**: Downloads the visualization as a PNG file
* **Share**: Creates a shareable link that allows you to share the visualization with others

