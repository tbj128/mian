var taxonomyLevels = {
  "Kingdom": 0,
  "Phylum": 1,
  "Class": 2,
  "Order": 3,
  "Family": 4,
  "Genus": 5,
  "Species": 6,
  "OTU": -1
};
var taxonomiesMap = [];


function showLoading() {
  $("#loading").show();
}

function hideLoading() {
  $("#loading").hide();
}

function setExtraNavLinks(attr) {
  $(".nav-link").each(function() {
    var currHref = $(this).attr("href");
    var currHrefArr = currHref.split("?");
    if (currHrefArr.length > 1) {
      currHref = currHrefArr[0];
    }
    $(this).attr("href", currHref + "?pid=" + attr);
  });
}

function getTaxonomicLevel() {
  return $("#taxonomy").val();
}

function getSelectedTaxFilter() {
  var taxLevel = $("#filter-otu").val();
  if (taxLevel === "none") {
    return -2;
  }
  return taxonomyLevels[taxLevel];
}

function getSelectedTaxFilterVals() {
  var taxonomy = $("#taxonomy-specific").val();
  if (taxonomy == null) {
    taxonomy = [];
  }

  var taxLevel = $("#filter-otu").val();
  if (taxLevel === "none") {
    taxonomy = [];
  }

  if ($("#taxonomy-specific option").size() === taxonomy.length) {
    // Select all is enabled
    return "mian-select-all";
  }

  return taxonomy.join(",");
}

function getSelectedSampleFilter() {
  var filter = $("#filter-sample").val();
  return filter;
}

function getSelectedSampleFilterVals() {
  var samples = $("#filter-sample-specific").val();
  if (samples == null) {
    samples = []
  }
  return samples.join(",");
}

$(document).ready(function() {
  var params = decodeURIComponent(window.location.search.substring(1));
  if (params != undefined && params != "") {
    var paramsArr = params.split("&");
    for (var i = 0; i < paramsArr.length; i++) {
      var param = paramsArr[i];
      var paramSplit = param.split("=");
      if (paramSplit.length == 2 && paramSplit[0] === "pid") {
        setExtraNavLinks(paramSplit[1]);
      }
    }
  }

  $("#project").change(function() {
    setExtraNavLinks($("#project").val());
  });

  $("#filter-sample").change(function() {
    var filterVal = $("#filter-sample").val();
    if (filterVal === "none") {
      $("#filter-sample-wrapper").hide();
    } else {
      $("#filter-sample-wrapper").show();
      getSampleFilteringOptions();
    }
  });

  $("#filter-otu").change(function() {
    var filterVal = $("#filter-otu").val();
    if (filterVal === "none") {
      $("#filter-otu-wrapper").hide();
    } else {
      $("#filter-otu-wrapper").show();
      updateTaxonomicLevel(false);
    }
  });

  function getSampleFilteringOptions() {
    $.ajax({
      url: "metadata_vals?pid=" + $("#project").val() + "&catvar=" + $("#filter-sample").val(), 
      success: function(result) {
        var json = JSON.parse(result);

        var $filterSampleSpecific = $("#filter-sample-specific");

        var options = [];
//        for (var i = 0; i < json.length; i++) {
//          var option = {
//            "label": json[i],
//            "title": json[i],
//            "value": json[i],
//            // "selected": true
//          };
//          options.push(option);
//        }
        for (var i = 0; i < 100; i++) {
          var option = {
            "label": i,
            "title": i,
            "value": i,
            // "selected": true
          };
          options.push(option);
        }

        var outWidth = $("#project").outerWidth();
        $filterSampleSpecific.multiselect({
          buttonWidth: outWidth ? outWidth + 'px' : '320px',
          includeSelectAllOption: true,
          enableFiltering: true,
          maxHeight: 400
        });

        $filterSampleSpecific.multiselect('dataprovider', options);
      }
    });

  }

    console.log("blah");

    $('input').tagsinput({
      typeahead: {
        source: ['Amsterdam', 'Washington', 'Sydney', 'Beijing', 'Cairo']
      }
    });


//    $('#test').tagsinput({
//      typeaheadjs: {
//        name: 'citynames',
//        displayKey: 'name',
//        valueKey: 'name',
//        source: function(query, callback) {
//            console.log(query);
//            callback(["apple"]);
//        }
//      }
//    });
});





// 
// Sidebar Shared
// 

function updateCatVar(callback) {
  return $.ajax({
    url: "metadata_headers?pid=" + $("#project").val(), 
    success: function(result) {
      var json = JSON.parse(result);

      var $catvar = $("#catvar");
      var $filterSample = $("#filter-sample");

      $catvar.empty();
      $catvar.append("<option value='none'>None</option>");

      $filterSample.empty();
      $filterSample.append("<option value='none'>Don't Filter</option>");
      $filterSample.append("<option value='mian-sample-id'>Sample ID</option>");

      var options = [];
      for (var i = 0; i < json.length; i++) {
        var option = {
          "label": json[i],
          "title": json[i],
          "value": json[i]
        };
        options.push(option);
      }

      for (var i = 0; i < json.length; i++) {
        $catvar.append("<option value='" + json[i] + "'>" + json[i] + "</option>");
        $filterSample.append("<option value='" + json[i] + "'>" + json[i] + "</option>");
      }

      if (callback !== undefined) {
        callback(json);
      }
    }
  });
}

function updateTaxonomicLevel(firstLoad, callback) {
  console.log("Updating taxonomic level")
  if (taxonomiesMap.length == 0) {
    // Load taxonomy map
    return $.ajax({
      url: "taxonomies?pid=" + $("#project").val(), 
      success: function(result) {
        var json = JSON.parse(result);
        taxonomiesMap = json;
        renderTaxonomicLevel(firstLoad);
        if (callback != null && callback != undefined) {
          callback();
        }
      }
    });
  } else {
    renderTaxonomicLevel(firstLoad);
    if (callback != null && callback != undefined) {
      callback();
    }
    return null;
  }
}


function renderTaxonomicLevel(firstLoad) {
  console.log("Rendering taxonomic level");
  var taxas = {};

  var level = getSelectedTaxFilter();

  if (getSelectedTaxFilter() < 0) {
    $.each(taxonomiesMap, function(otu, classification) {
      taxas[otu] = true;
    });
  } else {
  
    $.each(taxonomiesMap, function(otu, classification) {
      if (!taxas.hasOwnProperty(classification[level])) {
        taxas[classification[level]] = true;
      }
    });
  }

  var taxasArr = Object.keys(taxas);
  taxasArr = taxasArr.sort();
  
  var $filterOTUSpecific = $("#taxonomy-specific");
  var options = [];
  for (var i = 0; i < taxasArr.length; i++) {
    var option = {
      "label": taxasArr[i],
      "title": taxasArr[i],
      "value": taxasArr[i],
      // "selected": true
    };
    options.push(option);
  }

//  var outWidth = $("#project").outerWidth();
//  $filterOTUSpecific.multiselect({
//    buttonWidth: outWidth ? outWidth + 'px' : '320px',
//    includeSelectAllOption: true,
//    enableFiltering: true,
//    maxHeight: 400
//  });
//
//  $filterOTUSpecific.multiselect('dataprovider', options);

  console.log("Finished rendering taxonomic level");
}


function updateSamples(firstLoad) {
  return $.ajax({
    url: "samples?pid=" + $("#project").val(), 
    success: function(result) {
      var json = JSON.parse(result);
      renderSamples(json, firstLoad);
    }
  });
}

function renderSamples(json, firstLoad) {
  $("#samples").empty();
  options = ""
  for (var i = 0; i < json.length; i++) {
    options += "<option value='" + json[i] + "'>" + json[i] + "</option>";
  }
  $("#samples").append(options)

  if (firstLoad) {
    var outWidth = $("#project").outerWidth();
    $('#samples').multiselect({
      buttonWidth: outWidth ? outWidth + 'px' : '320px',
      enableFiltering: true,
      includeSelectAllOption: true,
      maxHeight: 200
    });
  } else {
    $('#samples').multiselect('rebuild');
  }
  $('#samples').multiselect('selectAll', false);
  $('#samples').multiselect('updateButtonText');
}



// 
// Statistics Container Shared
// 

function renderPvaluesTable(abundancesObj) {
  $("#stats-container").hide();

  if ($.isEmptyObject(abundancesObj)) {
    return;
  }

  $('#stats-rows').empty();
  var statsArr = abundancesObj["stats"];
  if (statsArr.length == 0) {
    $('#stats-rows').append('<tr><td colspan=3>No p-values could be generated. Try adjusting the search parameters. <br /><i style="color:#999">Try changing the Category Breakdown on the left.</i></td></tr>');
  } else {
    for (var i = 0; i < statsArr.length; i++) {
       $('#stats-rows').append('<tr><td>' + statsArr[i]["c1"] + '</td> <td>' + statsArr[i]["c2"] + '</td> <td>' + statsArr[i]["pval"] + '</td> </tr>');
    }
  }
  
  $("#stats-container").fadeIn(250);
}


// 
// Visualization Shared
// 

function renderBoxplots(abundancesObj) {
  $('#analysis-container').empty();

  if ($.isEmptyObject(abundancesObj)) {
    return;
  }

  var dataObj = abundancesObj["abundances"];

  var categories = [];
  var maxVal = 0;
  $.each(dataObj, function(k, v) {
    categories.push(k);
    for (var i = 0; i < dataObj[k].length; i++) {
      if (dataObj[k][i]["a"] > maxVal) {
        maxVal = dataObj[k][i]["a"];
      }
    }
  });

  if (maxVal == 0) {
    maxVal = 1;
  }

  // Initialize the dimensions
  var boxplotWidth = 128;
  var margin = {top: 36, right: 36, bottom: 36, left: 72},
      padding = 48,
      width = (boxplotWidth + padding*2) * categories.length,
      height = 520 - margin.top - margin.bottom;

  // Initialize the y axis scale
  var yScale = d3.scale.linear().range([height + margin.top, 0 + margin.top]);  
  yScale.domain([0, maxVal*1.10]);

  // Initialize the x axis scale
  var xScale = d3.scale.ordinal()
              .domain(categories)
              .rangeRoundBands([0, width]); 

  // Initialize the y axis
  var yAxis = d3.svg.axis()
                .scale(yScale)
                .orient("left");

  // Initialize the x axis
  var xAxis = d3.svg.axis()
                .scale(xScale)
                .orient("bottom");

  // Append the axis onto the figure
  var svgContainer = d3.select("#analysis-container")
              .append("svg")
              .attr("width", width + margin.left + margin.right)
              .attr("height", height + margin.top + margin.bottom);

  svgContainer.append("g")
      .attr("class", "box")
      .attr("transform", "translate(0, 0)");

  svgContainer.append("g")
     .attr("class", "axis")
     .attr("transform", "translate(" + margin.left + ", 0)")
     .call(yAxis);

  svgContainer.append("g")
     .attr("class", "axis")
     .attr("transform", "translate(" + margin.left + ", " + (height + margin.top + 10) + ")")
     .call(xAxis);

  var svg = svgContainer.selectAll(".box");

  for (var i = 0; i < categories.length; i++) {
    var dataCat = dataObj[categories[i]];

    // Calculate offset of this particular boxplot
    var midline = margin.left + (boxplotWidth + 2*padding)/2 + i*(boxplotWidth + 2*padding);

    // Initialize each boxplot
    var data = [],
        outliers = [],
        minVal = Infinity,
        lowerWhisker = Infinity,
        q1Val = Infinity,
        medianVal = 0,
        q3Val = -Infinity,
        iqr = 0,
        upperWhisker = -Infinity,
        maxVal = -Infinity;

    data = dataCat.map(function(d) {
      return d.a;
    });

    data = data.sort(d3.ascending);

    //calculate the boxplot statistics
    minVal = data[0],
    q1Val = d3.quantile(data, .25),
    medianVal = d3.quantile(data, .5),
    q3Val = d3.quantile(data, .75),
    iqr = q3Val - q1Val,
    maxVal = data[data.length - 1];
    // lowerWhisker = d3.max([minVal, q1Val - iqr])
    // upperWhisker = d3.min([maxVal, q3Val + iqr]);

    var index = 0;

    //search for the lower whisker, the mininmum value within q1Val - 1.5*iqr
    while (index < data.length && lowerWhisker == Infinity) {

      if (data[index] >= (q1Val - 1.5*iqr))
        lowerWhisker = data[index];
      else
        outliers.push(data[index]);
      index++;
    }

    index = data.length-1; // reset index to end of array

    //search for the upper whisker, the maximum value within q1Val + 1.5*iqr
    while (index >= 0 && upperWhisker == -Infinity) {

      if (data[index] <= (q3Val + 1.5*iqr))
        upperWhisker = data[index];
      else
        outliers.push(data[index]);
      index--;
    }

    //draw verical line for lowerWhisker
    svg.append("line")
       .attr("class", "whisker")
       .attr("y1", yScale(lowerWhisker))
       .attr("y2", yScale(lowerWhisker))
       .attr("stroke", "black")
       .attr("x1", midline - boxplotWidth/2)
       .attr("x2", midline + boxplotWidth/2);

    //draw vertical line for upperWhisker
    svg.append("line")  
       .attr("class", "whisker")
       .attr("y1", yScale(upperWhisker))
       .attr("y2", yScale(upperWhisker))
       .attr("stroke", "black")
       .attr("x1", midline - boxplotWidth/2)
       .attr("x2", midline + boxplotWidth/2);

    //draw horizontal line from lowerWhisker to upperWhisker
    svg.append("line")
       .attr("class", "whisker")
       .attr("y1",  yScale(lowerWhisker))
       .attr("y2",  yScale(upperWhisker))
       .attr("stroke", "black")
       .attr("x1", midline)
       .attr("x2", midline);

    //draw rect for iqr
    svg.append("rect")    
       .attr("class", "box")
       .attr("stroke", "black")
       .attr("fill", "white")
       .attr("y", yScale(q3Val))
       .attr("x", midline - boxplotWidth/2)
       .attr("height", yScale(q1Val) - yScale(q3Val))
       .attr("width", boxplotWidth);

    //draw vertical line at median
    svg.append("line")
       .attr("class", "median")
       .attr("stroke", "black")
       .attr("y1", yScale(medianVal))
       .attr("y2", yScale(medianVal))
       .attr("x1", midline - boxplotWidth/2)
       .attr("x2", midline + boxplotWidth/2);

    for (var k = 0; k < dataCat.length; k++) {
      var d = dataCat[k];
      // Draw data as points
      svg.append("circle")
         .attr("r", 2.5)
         .attr("class", function() {
          if (d.a < lowerWhisker || d.a > upperWhisker)
            return "outlier";
          else 
            return "point";
         })     
         .attr("cx", function() {
          return random_jitter(midline);
         }) 
         .attr("cy", function() {
          return yScale(d.a);   
         })
         .append("title")
         .text(function() {
          return "Sample: " + d.s + ", Abundance: " + d.a;
         }); 
    }


    function random_jitter(m) {
      if (Math.round(Math.random() * 1) == 0)
        var seed = -10;
      else
        var seed = 10; 
      return m + Math.floor((Math.random() * seed) + 1);
    }
  }
}