# NMDS

Performs non-metric multidimensional scaling at the selected taxonomic level  
  
NMDS tries to represent the original data in a 2D reduced dimensional space. This analysis utilizes the [scikit-learn package](http://scikit-learn.org/stable/modules/generated/sklearn.manifold.MDS.html)

![](.gitbook/assets/image%20%2811%29.png)

### Used For

* Visualizing the similarity between different samples \(collapsing information into two components\)

### Visualization Parameters

#### Taxonomic Level

The taxonomic level to aggregate the OTUs at. The OTUs will be grouped together \(by summing the OTU values\) at the selected taxonomic level before the analysis is applied.

#### Categorical Variable

Create comparative sample groups based on categorical variables uploaded in the metadata file. 

Optionally create a categorical variable from a quantitative variable by using the Quantile Range feature on the Projects home page. 

#### Distance Metric

Choose from one or multiple ways to calculate the distance between samples

### Interactive Elements

* Hover over each point to determine its sample ID and its NMDS component values
* Zoom and pan

### Additional Features

* **Save Snapshot**: Save the visualization to the experiment notebook
* **Download**: Downloads the visualization as a PNG file
* **Share**: Creates a shareable link that allows you to share the visualization with others

