# Beta Diversity

![](.gitbook/assets/image%20%282%29.png)



### Used For

* Measuring the dissimilarity between different sample groups

### Visualization Parameters

#### Taxonomic Level

The taxonomic level to aggregate the OTUs at. 

#### Categorical Variable

Create comparative sample groups based on categorical variables uploaded in the metadata file. 

Optionally create a categorical variable from a quantitative variable by using the Quantile Range feature on the Projects home page. 

#### Color Variable

Choose a categorical variable to color the points in the boxplots. 

For instance, you might want to divide the boxplots by their disease classification and color the points by their sampling location to identify any locality bias. 

#### Strata

Indicate which metadata should be used as the strata variable. Strata is required for PERMANOVA for nested experiment studies \(to control the groups that should be permuted\). [See here for more info](http://cc.oulu.fi/~jarioksa/softhelp/vegan/html/adonis.html)

#### Diversity Type

The beta diversity index measure to use as described in the R 'Vegan' package [here](https://cran.r-project.org/web/packages/vegan/vignettes/diversity-vegan.pdf)

#### Statistical Test

PERMANOVA and ANOVA is automatically calculated.

### Interactive Elements

* Hover over each point to determine its sample ID and its value

### Additional Features

* **Save Snapshot**: Save the visualization to the experiment notebook
* **Download**: Downloads the visualization as a PNG file
* **Share**: Creates a shareable link that allows you to share the visualization with others

