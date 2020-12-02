---
description: >-
  Here we will analyze a lung microbiome OTU dataset from a Sze et al. COPD
  study using some of Mian's basic features.
---

# Tutorial

## Login 

Log into the demo account to access sample datasets: [https://mian.hli.ubc.ca/login](https://mian.hli.ubc.ca/login)

![](.gitbook/assets/image%20%2840%29.png)

## Explore the Projects Dashboard 

Here we will analyze a lung microbiome data from a COPD study from Sze et al.

![](.gitbook/assets/image%20%2839%29.png)

## Composition

Let's start by examining the average phylum composition between the control and COPD samples. Go to Visualize &gt; Barplot \(Composition\) and set the parameters as shown. 

![](.gitbook/assets/image%20%2831%29.png)

Notice that the Bacteroidetes look more enriched in the control samples so let's build a boxplot to examine this in more detail. 

![](.gitbook/assets/image%20%2842%29.png)

The boxplot shows that this difference is significant under the Wilcoxon Rank-Sum test. 

## Diversity

Next, let's look at the alpha diversity measures. Here, we'll compare species richness to the surface area measure, as proposed in the original paper.  

![](.gitbook/assets/image%20%2818%29.png)

Decreasing surface area appears to be correlated with decreasing species richness. 

What about beta diversity? Note that this tool might take a little bit longer to run because of the permutations. On especially large datasets, the tool might timeout due to resource sharing. If this happens, consider deploying a local instance using a larger host type.

![](.gitbook/assets/image%20%2834%29.png)

Here, we see that there are significant differences between the COPD and control lung bacteria communities.

Because we can, let's also build a 3D PCA plot to visually see the population groupings between the COPD and control samples. Go ahead and rotate it!

![](.gitbook/assets/image%20%2835%29.png)

## Saving and Sharing Your Work

Maybe you think the above PCA is a cool finding - we can take a snapshot of this view and save to our notebook. Just press the "Save Snapshot to Notebook" button at the top right. If we go to our notebook \(accessible from our home dashboard\), we'll see the following:

![](.gitbook/assets/image%20%2838%29.png)

Your notebook keeps track of all the parameters you used so if you click "View Original Source", you'll get back to the original plot. 

You can also download or share your work. Try clicking on the "Share" button. 

![](.gitbook/assets/image%20%2833%29.png)

You can share this unique link with others and they can open the exact same view and start exploring the data. You can disable access at any time.

## Selecting Important Features

Maybe now we want to look for important OTUs. Let's try to use Boruta feature selection to see what OTUs are picked up.

![](.gitbook/assets/image%20%2826%29.png)

Clicking on any of the OTUs leads to the boxplot for further visualization. For instance, here, let's click on Otu0009.

![](.gitbook/assets/image%20%2837%29.png)

Here, indeed we see that Otu0009 is important as the control samples are highly enriched for Otu0009.

## Machine Learning

Could we build a classifier to predict COPD status? Let's find out by training a simple logistic regression model on the COPD data.

![](.gitbook/assets/image%20%2832%29.png)

We see that the model achieves 0.9375 test accuracy which indicates that the two groups can be distinguished quite easily by the model.

We can also try a deep learning model. However, the COPD data was quite small so it might be difficult to generalize - for this, let's try using the larger Coral dataset.

![](.gitbook/assets/image%20%2841%29.png)

With a two-layer feed-forward neural network with dropout, we can achieve a 0.9711 test accuracy over about 30 epochs. 

## Conclusions

We explored our dataset from top to bottom. We visualized composition differences, analyzed intra- and inter-community diversity, automatically selected the important OTUs, and trained a few promising machine learning models. 

There are many other tools not covered here but are ready for you to use - happy exploring!



