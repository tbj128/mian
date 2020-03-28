# Deep Learning

![](.gitbook/assets/image%20%2815%29.png)

### Used For

* Assess the performance of a deep neural network on the OTU data in predicting a categorical or numerical variable

{% hint style="info" %}
Use deep neural networks \(DNN\) with caution. DNNs are typically best when there are thousands of examples for each categorical class. DNNs are also prone to overfitting.
{% endhint %}

### Result Interpretation

* The graph shows either the accuracy or cross-entropy loss over epochs for the training and validation data only
* The test accuracy or loss is calculated once after the training is complete

### Feature Selection Parameters

#### Taxonomic Level

The taxonomic level to aggregate the OTUs at. 

#### Experimental Variable

The categorical or numeric variable that the model should predict. 

#### Freeze Training Set Between Changes

If set to yes, ensures that the same samples are used as the training set every the model is retrained. This useful to keep the test set untouched. 

#### Training Proportion

Define the proportion of the data that should be randomly picked to form a training dataset. 

#### Training Epochs

The maximum number of passes through the training data. 

#### Problem Type

Whether the DNN will be trained as a classifier \(categorical\) or a regressor \(numeric\). This value is automatically set based on the variable selected in the "Experimental Variable" section.

#### Measure

Assess the model by either using the accuracy or cross-entropy loss. This affects both the training/validation test plot and the final test accuracy or loss. 

#### Layers

![](.gitbook/assets/image%20%2827%29.png)

Customize and build your own deep neural network by setting the number and type of layers you want to use:

* **Dense Layer**: The neurons are fully-connected to the neurons of the next layer. 
* **Dropout Layer**: The percentage of connections to randomly drop between the current layer and the next layer

### Interactive Elements

* Hover over the training/validation curve 

### Additional Features

* **Save Snapshot**: Save the results to the experiment notebook
* **Download**: Downloads the results as a CSV file
* **Share**: Creates a shareable link that allows you to share the results with others

