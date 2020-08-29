# Tool Parameters and Filters

Every tool has a set of options on the left-hand panel. Switch between your projects using the dropdown at the top.

### Project Switcher

Switch between different projects while keeping the rest of the parameters the same. This can help you compare results between different datasets. 

### Data Filtering

On-demand filters are accessible via a dropdown menu for any tool. These filters allow you to exclude outliers or remove any data you don't want to see in the visualization or feature selection result. 

#### OTU Filtering

{% hint style="info" %}
OTU filtering is automatically applied on feature selection tools to improve performance
{% endhint %}

* Low-expression OTUs can be automatically filtered out using the count and prevalence threshold
  * Count Threshold: OTUs are only kept if their total count across all samples is greater than or equal to this number
  * Prevalence Threshold: OTUs are only kept if they occur with a non-zero count across all samples with this percentage or greater.
* OTU filtering
  * Use this to filter out specific OTUs or taxonomic groups. Supports "include all but this" or "exclude all but this"

#### Sample filtering

* Remove specific sample IDs by choosing the "Sample IDs" option
* Remove entire sample groups by filtering by a categorical metadata variable \(eg. remove the entire control group to assess how the correlation changes\)

![](.gitbook/assets/image%20%2812%29.png)







