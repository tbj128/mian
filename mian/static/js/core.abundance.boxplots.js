$(document).ready(function() {
  // Global variables storing the data

  // Initialization
  $.when(updateTaxonomicLevel(true, function() {}), updateCatVar()).done(function(a1, a2) {
    updateAnalysis();
  });
  
  createListeners();

  function createListeners() {
    $("#project").change(function () {
      updateTaxonomicLevel(false, function() {
        updateAnalysis();
      });
      updateCatVar();
    });

    $("#filter-sample").change(function() {
      var filterVal = $("#filter-sample").val();
      if (filterVal === "none" || filterVal === "mian-sample-id") {
        updateAnalysis();
      }
    });

    $("#filter-otu").change(function() {
      var filterVal = $("#filter-otu").val();
      if (filterVal === "none") {
        updateAnalysis();
      }
    });

    $("#taxonomy-specific").change(function () {
      updateAnalysis();
    });

    $("#filter-sample-specific").change(function () {
      updateAnalysis();
    });

    $("#catvar").change(function () {
      updateAnalysis();
    });
  }

  function updateAnalysis() {
    showLoading();
    $("#stats-container").fadeIn(250);

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();

    var data = {
      "pid": $("#project").val(),
      "taxonomyFilter": taxonomyFilter,
      "taxonomyFilterVals": taxonomyFilterVals,
      "sampleFilter": sampleFilter,
      "sampleFilterVals": sampleFilterVals,
      "catvar": catvar
    };

    $.ajax({
      type: "POST",
      url: "abundances",
      data: data,
      success: function(result) {
        hideLoading();
        var abundancesObj = JSON.parse(result);
        renderBoxplots(abundancesObj);
        renderPvaluesTable(abundancesObj);
      },
      error: function(err) {
        console.log(err)
      }
    });
  }

  function renderBoxplots(abundancesObj) {
    $('#analysis-container').empty();

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
      if (dataCat.length == 0) {
        continue;
      }

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

});