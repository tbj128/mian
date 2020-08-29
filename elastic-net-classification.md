---
description: >-
  This tool fits a linear model with elastic-net regularization based on the
  selected numerical experimental variable. This tool will then subsequently
  select the highest weight OTUs or taxonomic groups
---

# Elastic Net Classification

![](.gitbook/assets/image%20%2815%29%20%281%29.png)

### Used For

* Selecting OTUs or taxonomic groups \("OTU signature"\) that differentiate between two or more sample groups according to a generalized linear model with Elastic Net regularization

### Feature Selection Parameters

#### Taxonomic Level

The taxonomic level to aggregate the OTUs at. The OTUs will be grouped together \(by summing the OTU values\) at the selected taxonomic level before the analysis is applied.

#### Categorical Variable

Create comparative sample groups based on categorical variables uploaded in the metadata file. 

Optionally create a categorical variable from a quantitative variable by using the Quantile Range feature on the Projects home page. 

#### Number of Features to Keep

Specify how many features to display in the output. Leave blank to not do any filtering.

#### Loss Function

The type of loss to use when training the model.

#### Fix Training Set Between Changes

Indicate whether the training set should remain the same every time a parameter is changed and the model is retrained.

#### Training Proportion

Define the proportion of the data that should be randomly picked to form a training dataset. 

{% hint style="info" %}
You can set this value to be 1.0 if you don't plan on evaluating with a test dataset.
{% endhint %}

#### L1 Regularization Ratio

L1 \([LASSO](https://en.wikipedia.org/wiki/Lasso_%28statistics%29)\) regularization helps encourage sparsity within the selected features, which means that fewer features will be used to predict the experimental variable. 

0.5 is recommended.

#### Max Iterations

The maximum number of passes through the data during training. 

{% hint style="info" %}
Note that the training may stop early if the model detects that the training error is no longer going down after five consecutive epochs
{% endhint %}

### Interactive Elements

* Link back to boxplots

### Additional Features

* **Save Snapshot**: Save the results to the experiment notebook
* **Download**: Downloads the results as a CSV file
* **Share**: Creates a shareable link that allows you to share the results with others

