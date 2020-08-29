# Scatterplot \(Correlation\)

{% hint style="info" %}
This tool starts out empty until you have added values to both "Correlation Variable 1" and "Correlation Variable 2"
{% endhint %}

![](.gitbook/assets/image%20%2819%29%20%281%29.png)

### Used For

* Correlating between:
  * One or more OTUs or taxonomic groups 
  * Alpha diversity
  * Quantitative metadata
  * Gene expression \(if available\)

### Visualization Parameters

#### Taxonomic Level

The taxonomic level to aggregate the OTUs at. The OTUs will be grouped together \(by summing the OTU values\) at the selected taxonomic level before the analysis is applied.

#### Correlation Variable 1

The quantitative variable to display on the x-axis. If you chose "OTU or Taxonomic Group Abundance", make sure to enter at least one value in the field immediately below.  

#### Correlation Variable 2

The quantitative variable to display on the y-axis. If you chose "OTU or Taxonomic Group Abundance", make sure to enter at least one value in the field immediately below. 

#### Color Variable

Choose a categorical variable to color the points. 

For instance, you might want to correlate the Streptococcus genus against TLR8 expression, but also highlight the disease sample group. 

#### Size Variable

Choose a quantitative variable to resize the points by. This allows you to add a third quantitative variable to explore with. 

#### Samples To Show

Determines which sample types should be displayed in the correlation graph

* **All samples**: Displays all samples
* **Non-zero value samples**: Displays only samples that have a non-zero value for the selected taxonomic group\(s\) or OTU\(s\)
* **Zero value samples**: Displays only samples that have a zero value for the selected taxonomic group\(s\) or OTU\(s\)

### Interactive Elements

* Hover over each point to determine its sample ID and specific variable values.
* Zoom or pan

### Additional Features

* **Save Snapshot**: Save the visualization to the experiment notebook
* **Download**: Downloads the visualization as a PNG file
* **Share**: Creates a shareable link that allows you to share the visualization with others

