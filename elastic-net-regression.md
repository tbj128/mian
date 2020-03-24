# Elastic Net Regression



### Used For

* Selecting OTUs or taxonomic groups \("OTU signature"\) that are important \(more heavily weighted\) when predicting a quantitative metadata variable

### Feature Selection Parameters

#### Taxonomic Level

The taxonomic level to aggregate the OTUs at. 

#### Experimental Variable

Create comparative sample groups based on categorical variables uploaded in the metadata file. 

Optionally create a categorical variable from a quantitative variable by using the Quantile Range feature on the Projects home page. 

#### Number of Features to Keep

Specify how many features to display in the output. Leave blank to not do any filtering.

#### Loss Function

The type of loss to use when training the model.

#### Fix Training Set Between Changes

Indicate whether the training set should remain the same every time a parameter is changed and the model is retrained.

#### Dataset Training Proportion

Define the proportion of the data that should be randomly picked to form a training dataset. 

{% hint style="info" %}
You can set this value to be 1.0 if you don't plan on evaluating with a test dataset.
{% endhint %}

#### L1 Regularization Ratio

Specify the proportion of L1 regularization the model should use. 0.5 is recommended. 

#### Max Iterations

The maximum number of iterations the model should train for

### Interactive Elements

* Link back to boxplots

### Additional Features

* **Save Snapshot**: Save the results to the experiment notebook
* **Download**: Downloads the results as a CSV file
* **Share**: Creates a shareable link that allows you to share the results with others

