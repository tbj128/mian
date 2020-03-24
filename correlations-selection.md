# Correlations Selection

![](.gitbook/assets/image%20%283%29.png)



### Used For

* Selecting OTUs or taxonomic groups \("OTU signature"\), gene expression, or quantitative metadata that significantly correlate with other OTUs or taxonomic groups, gene expression, alpha diversity, or quantitative metadata
* Answers questions such as:
  * What genes are upregulated in response to disease severity?
  * What histological features are correlated with Staphylococcus expansion?
  * What OTUs are correlated with T-cell infiltration?

### Feature Selection Parameters

#### Taxonomic Level

The taxonomic level to aggregate the OTUs at. 

#### Select...

Specify which variable you want to select for:

* OTUs or taxonomic groups \("OTU signature"\)
* Gene expression
* Quantitative metadata

#### By Correlating Against...

Specify which variable you want to correlate the selected variable against:

* OTUs or taxonomic groups \(you must pick the specific OTU or taxonomic group\)
* Gene expression \(you must pick the specific gene\)
* Alpha Diversity
* Quantitative metadata \(you must pick the specific metadata\)

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

* Link back to scatterplots

### Additional Features

* **Save Snapshot**: Save the results to the experiment notebook
* **Download**: Downloads the results as a CSV file
* **Share**: Creates a shareable link that allows you to share the results with others

