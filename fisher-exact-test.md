# Fisher Exact Test

![](.gitbook/assets/image%20%2830%29.png)



### Used For

* Selecting OTUs or taxonomic groups \("OTU signature"\) that have a significant difference between two or more sample groups according to a presence/absence Fisher Exact test

### Feature Selection Parameters

#### Taxonomic Level

The taxonomic level to aggregate the OTUs at. 

#### Categorical Variable

Create comparative sample groups based on categorical variables uploaded in the metadata file. 

Optionally create a categorical variable from a quantitative variable by using the Quantile Range feature on the Projects home page. 

#### Pairwise Comparison Variable

The two unique values for the selected Categorical Variable field that will be used to build a contingency table.

#### Min Presence Threshold

In the Fisher Exact test, this parameter controls what constitutes whether a taxonomic item is 'present' in a given sample. 

By default, this is zero which means that a taxonomic item is present for a sample if it has a non-zero value for the sample. If this value was 10, this means that a taxonomic item must have a count of at least 10 for it to be considered present.

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

