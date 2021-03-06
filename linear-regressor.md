# Linear Regressor

![](.gitbook/assets/image%20%2819%29.png)



### Used For

* Assess the performance of a linear model on the OTU data in predicting a numeric variable

{% hint style="info" %}
Machine learning models tend to work best with a dataset with a large number of samples
{% endhint %}

### Feature Selection Parameters

#### Taxonomic Level

The OTUs will be grouped together \(by summing the OTU values\) at the selected taxonomic level before the analysis is applied.

#### Experimental Variable

The numeric variable that the model should predict. 

{% hint style="info" %}
If there are no values in the dropdown, this likely means that there were no numeric variables found
{% endhint %}

#### Evaluation Method

Train the model using either by splitting the data into a training and test set or by cross-validating over a specified number of folds.

#### Cross-Validation Folds

Specify the number of folds used in [k-fold Cross Validation](https://scikit-learn.org/0.16/modules/generated/sklearn.cross_validation.KFold.html)

#### Freeze Training Set Between Changes

If set to yes, ensures that the same samples are used as the training set every the model is retrained. This useful to keep the test set untouched. 

#### Training Proportion

Define the proportion of the data that should be randomly picked to form a training dataset. 

#### L1 Regularization Ratio

L1 \([LASSO](https://en.wikipedia.org/wiki/Lasso_%28statistics%29)\) regularization helps encourage sparsity within the selected features, which means that fewer features will be used to predict the experimental variable. 

0.5 is recommended.

#### Max Epochs

The maximum number of passes through the training data. 

{% hint style="info" %}
Note that the training may stop early if the model detects that the training error is no longer going down after five consecutive epochs
{% endhint %}

#### 

### Interactive Elements

* Hover over the training/test error curve generated for the test data

### Additional Features

* **Save Snapshot**: Save the results to the experiment notebook
* **Download**: Downloads the results as a CSV file
* **Share**: Creates a shareable link that allows you to share the results with others

