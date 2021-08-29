# Deep Learning

![](.gitbook/assets/image%20%2845%29.png)

### Used For

* Assess the performance of a deep neural network \(implemented here as a multi-layer perceptron\) on the OTU data in predicting a categorical or numerical variable
* Examples:
  * Predict patient outcome or sampling region based on the lung microbiome composition from COPD patients
  * Predict hospital length-of-stay based on the nasopharyngeal microbiome composition from ICU patients

{% hint style="info" %}
Use deep neural networks \(DNN\) with caution. DNNs are typically best when there are thousands of examples for each categorical class. DNNs are also prone to overfitting - dropout layers can help reduce overfitting.
{% endhint %}

### Feature Selection Parameters

#### Taxonomic Level

The taxonomic level to aggregate the OTUs at. The OTUs will be grouped together \(by summing the OTU values\) at the selected taxonomic level before the analysis is applied.

#### Experimental Variable

The categorical or numeric variable that the model should predict. 

#### Freeze Training Set Between Changes

If set to yes, ensures that the same samples are used as the training set every the model is retrained. This useful to keep the test set untouched. 

#### Training Proportion

Define the proportion of the data that should be randomly picked to form a training dataset. 

#### Training Validation Proportion

Define the proportion of the training data that should be randomly picked to form a validation dataset. 

#### Training Epochs

The maximum number of passes through the training data. 

#### Problem Type

Whether the DNN will be trained as a classifier \(categorical\) or a regressor \(numeric\). This value is automatically set based on the variable selected in the "Experimental Variable" section.

#### Measure

Assess the model by either using the accuracy or cross-entropy loss for classification problems or mean absolute error or mean squared error for regression problems. 

This affects both the training/validation test plot and the final test accuracy or loss. 

#### Layers

![](.gitbook/assets/image%20%2827%29.png)

Customize and build your own deep neural network by setting the number and type of layers you want to use:

* **Dense Layer**: The neurons are fully-connected to the neurons of the next layer. 
* \*\*\*\*[**Dropout Layer**](https://en.wikipedia.org/wiki/Dropout_%28neural_networks%29): The percentage of connections to randomly drop between the current layer and the next layer. Dropout reduces overfitting by preventing co-adaptions between neurons.

### Result Interpretation

* The figure shows you the loss over training epochs. The loss should decrease as the number of epochs increase. Tips:
  * If the loss fluctuates, try decreasing the learning rate.
  * If the loss doesn't plateau, try increasing the learning rate.
  * If the training and validation losses diverge, you have overfitting. In this case, try adding a dropout layer or decreasing the number of layers in the model.
  * If the losses do not decrease, try increasing the number of layers or increasing the number of units in each layer.
* Assess the predictive performance of your model using the test AUC \(area under the [ROC curve](https://en.wikipedia.org/wiki/Receiver_operating_characteristic) shown\). _Note: Whenever possible, it is still recommended to validate a trained model against an independent dataset \(one that is collected outside of your study\)._
* Tune your model for better performance by looking only at the validation AUC. Tuning refers to changing the configurable parameters to try to achieve a better performance for your dataset.  _It is important to not tune against the test AUC to ensure you don't overfit your model to the test set._
* The AUC tells you the probability that a randomly sampled positive patient will have a higher predicted score for the positive class than the negative class. The AUC will be shown in a "one-vs-all" format.

### Interactive Elements

* Hover over the training/validation curve 

### Additional Features

* **Save Snapshot**: Save the results to the experiment notebook
* **Download**: Downloads the results as a CSV file
* **Share**: Creates a shareable link that allows you to share the results with others

