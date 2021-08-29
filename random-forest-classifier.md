# Random Forest Classifier

![](.gitbook/assets/image%20%2816%29.png)

### Used For

* Assess the performance of a random forest classifier on the OTU data in predicting a categorical variable

{% hint style="info" %}
Machine learning models tend to work best with a dataset with a large number of samples
{% endhint %}

### Feature Selection Parameters

#### Taxonomic Level

The taxonomic level to aggregate the OTUs at. The OTUs will be grouped together \(by summing the OTU values\) at the selected taxonomic level before the analysis is applied.

#### Categorical Variable

Create comparative sample groups based on categorical variables uploaded in the metadata file. 

Optionally create a categorical variable from a quantitative variable by using the Quantile Range feature on the Projects home page. 

#### Evaluation Method

Train the model using either by splitting the data into a training and test set or by cross-validating over a specified number of folds.

#### Cross-Validation Folds

Specify the number of folds used in [k-fold Cross Validation](https://scikit-learn.org/0.16/modules/generated/sklearn.cross_validation.KFold.html)

#### Freeze Training Set Between Changes

If set to yes, ensures that the same samples are used as the training set every the model is retrained. This useful to keep the test set untouched. 

#### Training Proportion

Define the proportion of the data that should be randomly picked to form a training dataset. 

#### Number of Trees

The maximum number of trees to generate for the [random forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)

#### Max Tree Depth

The max depth of each tree in the [random forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html). If empty, it will expand each tree to its fullest extent

### Interpreting Your Results

* Assess the predictive performance of your model using the test AUC \(area under the [ROC curve](https://en.wikipedia.org/wiki/Receiver_operating_characteristic) shown\). _Note: Whenever possible, it is still recommended to validate a trained model against an independent dataset \(one that is collected outside of your study\)._
* Tune your model for better performance by looking only at the validation AUC. Tuning refers to changing the configurable parameters to try to achieve a better performance for your dataset.  _It is important to not tune against the test AUC to ensure you don't overfit your model to the test set._
* The training error is also available as the [out-of-bag training error ](https://en.wikipedia.org/wiki/Out-of-bag_error)
* The AUC tells you the probability that a randomly sampled positive patient will have a higher predicted score for the positive class than the negative class. The AUC will be shown in a "one-vs-all" format.

### Interactive Elements

* Hover over the ROC curve generated for the test data

### Additional Features

* **Save Snapshot**: Save the results to the experiment notebook
* **Download**: Downloads the results as a CSV file
* **Share**: Creates a shareable link that allows you to share the results with others

