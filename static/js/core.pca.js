$(document).ready(function() {
  var abundancesObj = {};
  var boundX = [];
  var boundY = [];
  var boundXLastFire = 0;
  var boundYLastFire = 0;
  var slider1 = null, slider2 = null;

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

    $("#taxonomy").change(function () {
      updateTaxonomicLevel(false, function() {
        updateAnalysis();
      });
    });

    $("#taxonomy-specific").change(function () {
      updateAnalysis();
    });

    $("#catvar").change(function () {
      updateAnalysis();
    });
  }

  function renderPCA(data) {
    $("#analysis-container").empty();

    var margin = {top: 20, right: 20, bottom: 30, left: 40},
        width = 640 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    // setup x 
    var xValue = function(d) { return d.pca1;}, // data -> value
        xScale = d3.scale.linear().range([0, width]), // value -> display
        xMap = function(d) { return xScale(xValue(d));}, // data -> display
        xAxis = d3.svg.axis().scale(xScale).orient("bottom");

    // setup y
    var yValue = function(d) { return d.pca2;}, // data -> value
        yScale = d3.scale.linear().range([height, 0]), // value -> display
        yMap = function(d) { return yScale(yValue(d));}, // data -> display
        yAxis = d3.svg.axis().scale(yScale).orient("left");

    // setup fill color
    var cValue = function(d) { return d.m;},
        color = d3.scale.category10();

    // setup circle size
    var sValue = function(d) { 
      return 1;
      // return d.size; 
    };
    var minSValue = d3.min(data, sValue);
    var maxSValue = d3.max(data, sValue);
    var sScale = d3.scale.linear().domain([minSValue, maxSValue]).range([2, 8]);

    // add the graph canvas to the body of the webpage
    var svg = d3.select("#analysis-container").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    xDomain = [];
    if (boundX.length == 0) {
      xDomain = d3.extent(data, function(d) { return d.pca1; });
    } else {
      xDomain = [boundX[0], boundX[1]];
    }

    yDomain = [];
    if (boundY.length == 0) {
      yDomain = d3.extent(data, function(d) { return d.pca2; });
    } else {
      yDomain = [boundY[0], boundY[1]];
    }

    xScale.domain(xDomain);
    yScale.domain(yDomain);

    // x-axis
    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis)
      .append("text")
        .attr("class", "label")
        .attr("x", width)
        .attr("y", -6)
        .style("text-anchor", "end")
        .text($("#corrval").val())
        .text("Axis 1");

    // y-axis
    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
      .append("text")
        .attr("class", "label")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text("Axis 2");

    // draw dots
    svg.selectAll(".dot")
        .data(data)
      .enter().append("circle")
        .attr("class", "dot")
        .attr("r", function(d) { 
            // if ($("#sizevar").val() != "" && $("#sizevar").val() != "None") {
            //   return sScale(sValue(d)); 
            // } else {
              return 3;
            // }
          })
        .attr("cx", xMap)
        .attr("cy", yMap)
        .style("fill", function(d) { return color(cValue(d));}) ;

    if ($("#colorvar").val() != "" && $("#colorvar").val() != "None") {
      // draw legend
      var legend = svg.selectAll(".legend")
          .data(color.domain())
        .enter().append("g")
          .attr("class", "legend")
          .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

      // draw legend colored rectangles
      legend.append("rect")
          .attr("x", width - 18)
          .attr("width", 18)
          .attr("height", 18)
          .style("fill", color);

      // draw legend text
      legend.append("text")
          .attr("x", width - 24)
          .attr("y", 9)
          .attr("dy", ".35em")
          .style("text-anchor", "end")
          .text(function(d) { return d;})
    }
  }

  function renderPCAVar(data) {
    $("#variance-container").empty();

    var margin = {top: 20, right: 20, bottom: 30, left: 40},
        width = 640 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    // setup x 
    var xValue = function(d, i) { return i;}, // data -> value
        xScale = d3.scale.linear().range([0, width]), // value -> display
        xAxis = d3.svg.axis().scale(xScale).orient("bottom");

    // setup y
    var yValue = function(d) { return d;}, // data -> value
        yScale = d3.scale.linear().range([height, 0]), // value -> display
        yAxis = d3.svg.axis().scale(yScale).orient("left");

    xScale.domain(d3.extent(data, function(d, i) { return i; }));
    yScale.domain(d3.extent(data, function(d) { return d; }));

    // add the graph canvas to the body of the webpage
    var svg = d3.select("#variance-container").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // x-axis
    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis)
      .append("text")
        .attr("class", "label")
        .attr("x", width)
        .attr("y", -6)
        .style("text-anchor", "end")
        .text($("#corrval").val())
        .text("Principal Component #");

    // y-axis
    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
      .append("text")
        .attr("class", "label")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text("Variance (%)");

    var line = d3.svg.line()
      .x(function(d, i) { return xScale(i); })
      .y(function(d) {
        return yScale(d); 
      });

    svg.append("path")
        .datum(data)
        .attr("class", "line")
        .attr("d", line);
  }

  function updateAnalysis() {
    showLoading();

    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var pca1 = $("#pca1").val();
    var pca2 = $("#pca2").val();

    var data = {
      "pid": $("#project").val(),
      "taxonomyFilter": taxonomyFilter,
      "taxonomyFilterVals": taxonomyFilterVals,
      "sampleFilter": sampleFilter,
      "sampleFilterVals": sampleFilterVals,
      "level": level,
      "catvar": catvar,
      "pca1": pca1,
      "pca2": pca2
    };


    $.ajax({
      type: "POST",
      url: "pca",
      data: data,
      success: function(result) {
        hideLoading();
        abundancesObj = JSON.parse(result);
        boundX = [];
        boundY = [];

        // Update sliders

        document.getElementById("pca1-range").setAttribute("data-slider-min", abundancesObj["pca1Min"]);
        document.getElementById("pca1-range").setAttribute("data-slider-max", abundancesObj["pca1Max"]);
        document.getElementById("pca1-range").setAttribute("data-slider-value", "[" + abundancesObj["pca1Min"] + "," + abundancesObj["pca1Max"] + "]");
        
        if (slider1 === null) {
          $("#pca1-range").show();
          slider1 = $("#pca1-range").slider({
            formatter: function(value) {
              if ($.isArray(value)) {
                boundX = value;
                value[0] = Math.round(value[0] * 100) / 100;
                value[1] = Math.round(value[1] * 100) / 100;
              } else {
                value = Math.round(value * 100) / 100;
              }

              var diff = event.timeStamp - boundXLastFire;
              // Prevents the event from firing too often
              if (diff >= 300) {
                boundXLastFire = event.timeStamp;
                renderPCA(abundancesObj["pca"]);
              }

              return value;
            }
          });
        } else {
          slider1.slider('refresh');
        }

        document.getElementById("pca2-range").setAttribute("data-slider-min", abundancesObj["pca2Min"]);
        document.getElementById("pca2-range").setAttribute("data-slider-max", abundancesObj["pca2Max"]);
        document.getElementById("pca2-range").setAttribute("data-slider-value", "[" + abundancesObj["pca2Min"] + "," + abundancesObj["pca2Max"] + "]");
        
        if (slider2 === null) {
          $("#pca2-range").show();
          slider2 = $("#pca2-range").slider({
            formatter: function(value) {
              if ($.isArray(value)) {
                boundY = value;
                value[0] = Math.round(value[0] * 100) / 100;
                value[1] = Math.round(value[1] * 100) / 100;
              } else {
                value = Math.round(value * 100) / 100;
              }

              var diff = event.timeStamp - boundYLastFire;
              // Prevents the event from firing too often
              if (diff >= 300) {
                boundYLastFire = event.timeStamp;
                renderPCA(abundancesObj["pca"]);
              }
              return value;
            }
          });
        } else {
          slider2.slider('refresh');
        }

        renderPCA(abundancesObj["pca"]);
        renderPCAVar(abundancesObj["pcaVar"])
      },
      error: function(err) {
        console.log(err)
      }
    });
  }
});