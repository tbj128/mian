# Boxplots

{% hint style="info" %}
This tool starts out empty until you have added at least one OTU or taxonomic group under the "OTUs or Taxonomic Groups to Show" field OR you have selected another option under "Y-Axis Values"
{% endhint %}

![](.gitbook/assets/image%20%2820%29.png)

### Used For

* Comparisons of specific OTU or taxonomic group counts between one or more sample groups
* Comparisons of gene expression between one or more sample groups
* Comparisons of quantitative metadata between one or more sample groups

### Visualization Parameters

#### Categorical Variable

Create comparative sample groups based on categorical variables uploaded in the metadata file. 

Optionally create a categorical variable from a quantitative variable by using the Quantile Range feature on the Projects home page. 

#### Y-Axis Values

The numeric value that should be represented on the Y-axis:  
Note the special parameters below:

* **Taxonomy Abundance** The sum of the specified OTU or taxonomic group abundance in each sample.
* **Aggregate Abundance** The total abundance of all OTUs within a sample
* **Max/Min/Mean/Median** The max/min/mean/median of all OTUs within a sample

#### Taxonomic Level

The taxonomic level to aggregate the OTUs at. 

#### OTUs or Taxonomic Groups to Show

Choose the OTUs or taxonomic groups whose summed abundances should be displayed on the boxplots. 

Begin typing to see a list of options appear. 

#### Color Variable

Choose a categorical variable to color the points in the boxplots. 

For instance, you might want to divide the boxplots by their disease classification and color the points by their sampling location to identify any locality bias. 

#### Statistical Test

The selected test is automatically applied between every sample group. 

* **Wilcoxon Rank-Sum** A non-parametric test to test whether a randomly selected sample from one group will be different from a randomly selected sample from another group
* **Welch's T-Test** A parametric test to test whether two populations have equal means
* **ANOVA** A parametric test to test whether two populations have equal means

### Interactive Elements

* Hover over each point to determine its sample ID and its value

### Additional Features

* **Save Snapshot**: Save the visualization to the experiment notebook
* **Download**: Downloads the visualization as a PNG file
* **Share**: Creates a shareable link that allows you to share the visualization with others









