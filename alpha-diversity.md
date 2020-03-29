# Alpha Diversity

Investigate the OTU/Taxonomic richness of the OTU table. This analysis uses the diversity measure from the R 'vegan' package [here](http://cc.oulu.fi/~jarioksa/softhelp/vegan/html/diversity.html)

![](.gitbook/assets/image%20%286%29.png)

### Used For

* Comparisons of alpha diversity measures with one or more sample groups \(boxplot\)
* Comparisons of alpha diversity measures with a quantitative metadata variable \(scatterplot\)

### Visualization Parameters

#### Taxonomic Level

The taxonomic level to aggregate the OTUs at. The OTUs will be grouped together \(by summing the OTU values\) at the selected taxonomic level before the analysis is applied.

#### Experimental Variable

The metadata variable to compare the alpha diversity against.

#### Plot Type

Whether to compare the alpha diversity using a boxplot or scatterplot. Mian tries to automatically determine the correct visualization type basd on the data. 

#### Diversity Context

* **Alpha Diversity** The diversity measure based on the diversity index above
* **Evenness** Pielou's evenness measure as calculated [here](http://cc.oulu.fi/~jarioksa/softhelp/vegan/html/diversity.html)
* **OTU/Taxonomic Richness** The number of unique species within each sample

#### Diversity Index

Indicate the method by which the alpha diversity should be calculated. More information on the different diversity types can be found [here](http://cc.oulu.fi/~jarioksa/softhelp/vegan/html/diversity.html)  
  
Faith's Phylogenetic Diversity is a taxonomic richness analogue based on the phylogenetic tree

#### Statistical Test

The selected test is automatically applied between every sample group. 

* **Wilcoxon Rank-Sum** A non-parametric test to test whether a randomly selected sample from one group will be different from a randomly selected sample from another group
* **Welch's T-Test** A parametric test to test whether two populations have equal means
* **ANOVA** A parametric test to test whether two populations have equal means

### Interactive Elements

* Hover over each point to determine its sample ID and its value
* Zoom or pan on the scatterplot view

### Additional Features

* **Save Snapshot**: Save the visualization to the experiment notebook
* **Download**: Downloads the visualization as a PNG file
* **Share**: Creates a shareable link that allows you to share the visualization with others

