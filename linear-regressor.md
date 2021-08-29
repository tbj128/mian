# Linear Regressor

![](.gitbook/assets/image%20%2843%29.png)

### Used For

* Assessing the performance of a linear model on the OTU data in predicting a numeric Experiment Variable.
* Note that this tool uses the [Elastic Net](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.ElasticNet.html#sklearn.linear_model.ElasticNet) method with a configurable regularization penalty and fit intercept, meaning that the data will not be scaled prior to fitting. 

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

Train the model using either by splitting the data into training/val/test sets or by cross-validating over a specified number of folds. We recommend using train/val/test sets to ensure that you have a test set that is independent of all your training. Cross-validation may be an option if you have a small overall dataset. 

#### Cross-Validation Folds

Specify the number of folds used in [k-fold Cross Validation](https://scikit-learn.org/0.16/modules/generated/sklearn.cross_validation.KFold.html)

#### Freeze Training Set Between Changes

If set to yes, ensures that the same samples are used as the training set every the model is retrained. This recommended to keep the test set untouched. 

Under the hood, this sets a fixed random seed value which will make sure the same train/val/test splits are created when you are trying out different machine learning models.

#### Training Proportion

Define the proportion of the data that should be randomly picked to form a training dataset. The remaining samples are split equally into the validation and test datasets. 

For instance, if the training proportion is 0.7 and you have 1000 total samples, the system will build a training set of 700 samples, a validation set of 150 samples, and a test set of 150 samples. 

#### L1 Regularization Ratio

L1 \([LASSO](https://en.wikipedia.org/wiki/Lasso_%28statistics%29)\) regularization helps encourage sparsity within the selected features, which means that fewer features will be used to predict the experimental variable. 

0.5 is recommended.

#### Max Epochs

The maximum number of passes through the training data. 

{% hint style="info" %}
Note that the training may stop early if the model detects that the training error is no longer going down after five consecutive epochs
{% endhint %}

### Interpreting Your Results

* Assess the predictive performance of your model using the test error.  _Note: Whenever possible, it is still recommended to validate a trained model against an independent dataset \(one that is collected outside of your study\)._
* Tune your model for better performance by looking only at the validation error. Tuning refers to  _This is important to ensure you don't overfit your model to the test set._
* The mean absolute/squared error is the error that your model experiences when predicting for the Experiment Variable.
  * **Mean Absolute Error**: The error is calculated by taking the absolute difference between the predicted value and the actual value. The errors of all test samples are then averaged.
  * **Mean Squared Error**: The error is calculated by taking the squared difference between the predicted value and the actual value. The errors of all test samples are then averaged.

### Interactive Elements

* Hover over the training/test error curve generated for the test data

### Additional Features

* **Save Snapshot**: Save the results to the experiment notebook
* **Download**: Downloads the results as a CSV file
* **Share**: Creates a shareable link that allows you to share the results with others

