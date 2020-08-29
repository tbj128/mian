# Projects

After creating a project, your projects home page will look like the following:

![](.gitbook/assets/image%20%288%29.png)

### Download Files

Click the download icon next to each file name. To re-upload, you must create a new project. 

### Change Subsampling Depth

Note, samples with total OTU counts that fall under the targeted subsampling depth will be removed. 

### Add Quantile Range

Quantitative variables or gene expression can be treated as categorical ones by adding a quantile range. This is useful if, for instance, you wanted to bucket a histological measure into different disease severity thresholds \(eg. mild vs severe\). 

#### Choosing Type of Quantile Range

On the left-panel, you can choose to create a quantile range on a quantitative variable or gene expression. 

{% hint style="info" %}
If you do not see any options in the second dropdown, you either did not upload a gene expression matrix file or you have no quantitative variables.
{% endhint %}

![](.gitbook/assets/image%20%285%29%20%281%29.png)

You can have the system automatically \(and evenly\) bucketize the ranges according to the uploaded data, or you can provide your own custom quantile ranges. 

Saving a quantile range makes this quantile range available in categorical-tools such as boxplots or differential selection. 

### Notebook

The "View Notebook" link allows you to view previously saved visualizations or feature selection results. 

You can "View Original Source" to apply the same experimental settings to recreate the result. 

Note that the experiment title and description are available for editing. 

![](.gitbook/assets/image%20%283%29%20%281%29.png)

To save a visualization or result, click the "Save Snapshot to Notebook" at the top of any tool.

![](.gitbook/assets/image%20%287%29%20%281%29.png)

### Explore Your Data

To begin, you can choose any tool from the top dropdown menu. Each tool is described with its own documentation.



