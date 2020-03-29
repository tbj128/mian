# Differential Selection

Performs differential analysis of OTU data based on pairwise categorical metadata.

Taxonomic groups/OTUs that are statistically different between the two sample groupings will be displayed.

![](.gitbook/assets/image%20%2832%29.png)

### Used For

* Selecting OTUs or taxonomic groups \("OTU signature"\) that have a significant difference between two or more sample groups according to a differential analysis

### Feature Selection Parameters

#### Taxonomic Level

The taxonomic level to aggregate the OTUs at. The OTUs will be grouped together \(by summing the OTU values\) at the selected taxonomic level before the analysis is applied.

#### Categorical Variable

Create comparative sample groups based on categorical variables uploaded in the metadata file. 

Optionally create a categorical variable from a quantitative variable by using the Quantile Range feature on the Projects home page. 

#### Pairwise Comparison Variable

The two unique values for the selected Categorical Variable field that will be used to build a contingency table.

#### Analysis Type

* **ANCOM** Differential abundance testing using pairwise log ratios and applying a parametric one-way ANOVA statistical test. Recommended if using unsampled data sets
* **Wilcoxon Rank-Sum** A non-parametric test to test whether a randomly selected sample from one group will be different from a randomly selected sample from another group
* **Welch's T-Test** A parametric test to test whether two populations have equal means

#### P-Value Threshold

Only OTUs or taxonomic groups whose resultant p-value was less than this threshold will be displayed

#### Fix Training Set Between Changes

Indicate whether the training set should remain the same every time a parameter is changed and the model is retrained.

#### Dataset Training Proportion

Define the proportion of the data that should be randomly picked to form a training dataset. 

{% hint style="info" %}
You can set this value to be 1.0 if you don't plan on evaluating with a test dataset.
{% endhint %}

#### 

### Interactive Elements

* Link back to boxplots

### Additional Features

* **Save Snapshot**: Save the results to the experiment notebook
* **Download**: Downloads the results as a CSV file
* **Share**: Creates a shareable link that allows you to share the results with others

