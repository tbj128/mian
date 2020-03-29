# Boruta \(Feature Selection\)

Create a random forest to select the taxonomic groups/OTUs that can differentiate the chosen categorical variable. The weights of the taxonomic groups/OTUs the algorithm considers most important according to the [Boruta feature selection algorithm](https://cran.r-project.org/web/packages/Boruta/Boruta.pdf) will be displayed.

![](.gitbook/assets/image%20%284%29.png)

### Used For

* Selecting OTUs or taxonomic groups \("OTU signature"\) that differentiate between two or more sample groups according to a Random Forest classifier

### Feature Selection Parameters

#### Taxonomic Level

The taxonomic level to aggregate the OTUs at. The OTUs will be grouped together \(by summing the OTU values\) at the selected taxonomic level before the analysis is applied.

#### Categorical Variable

Create comparative sample groups based on categorical variables uploaded in the metadata file. 

Optionally create a categorical variable from a quantitative variable by using the Quantile Range feature on the Projects home page. 

#### Fix Training Set Between Changes

Indicate whether the training set should remain the same every time a parameter is changed and the model is retrained.

#### Dataset Training Proportion

Define the proportion of the data that should be randomly picked to form a training dataset. 

{% hint style="info" %}
You can set this value to be 1.0 if you don't plan on evaluating with a test dataset.
{% endhint %}

#### Max Epochs

The maximum number of epochs the Random Forest should train for

#### P-Value Threshold

OTUs or Taxonomic Groups with a p-value below this threshold will be shown in the results

### Interactive Elements

* Link back to boxplots

### Additional Features

* **Save Snapshot**: Save the results to the experiment notebook
* **Download**: Downloads the results as a CSV file
* **Share**: Creates a shareable link that allows you to share the results with others

