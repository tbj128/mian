$(document).ready(function() {
  var abundancesObj = {};

  // Initialization

  updateAnalysis();

  createListeners();

  function createListeners() {
    $("#project").change(function() {
      updateAnalysis();
    });
  }

  function renderRarefactionCurves(abundancesObj) {
    if ($.isEmptyObject(abundancesObj)) {
      return;
    }

    var data = abundancesObj["result"];
    var subsampleVals = abundancesObj["subsampleVals"];
    var minVal = 0;
    var maxVal = abundancesObj["max"];
    var maxSubsampleVal = abundancesObj["maxSubsampleVal"];


    $("#analysis-container").empty();

    var margin = {top: 20, right: 20, bottom: 30, left: 56},
        width = 960 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    // setup x 
    var xValue = function(d, i) { 
                  return subsampleVals[i];
                }, // data -> value
        xScale = d3.scale.linear().range([0, width]), // value -> display
        xMap = function(d, i) { return xScale(xValue(d, i));}, // data -> display
        xAxis = d3.svg.axis().scale(xScale).orient("bottom");

    // setup y
    var yValue = function(d) { return d;}, // data -> value
        yScale = d3.scale.linear().range([height, 0]), // value -> display
        yMap = function(d) { return yScale(yValue(d));}, // data -> display
        yAxis = d3.svg.axis().scale(yScale).orient("left");

    // setup fill color
    var color = d3.scale.category10();

    // add the graph canvas to the body of the webpage
    var svg = d3.select("#analysis-container").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var tooltip = d3.select("#analysis-container").append("div") 
      .attr("class", "tooltip")       
      .style("opacity", 0);

    // don't want dots overlapping axis, so add in buffer to data domain
    xScale.domain([0, maxSubsampleVal]);
    yScale.domain([0, maxVal]);

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
        .text("Subsample");

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
        .text("Number of OTUs");

    $.each(data, function(key,val) {
      var col = color(key);
      // draw dots
      var g1 = svg.append("g")
      g1.selectAll(".point")
          .data(val)
        .enter().append("circle")
          .attr("class", "point")
          .attr("r", 2)
          .attr("cx", xMap)
          .attr("cy", yMap)
          .style("fill", col)
          .style("display", function(d) { return d < 0 ? "none" : null; })
          .on("mouseover", function(d, i) {
            var meta = key;
            tooltip.transition()
                .duration(100)
                .style("opacity", 1);
            tooltip.html("<strong>" + meta + "</strong><br />Subsample: <strong>" + subsampleVals[i] + "</strong><br />Value: <strong>" + d + "</strong>")
                .style("left", (d3.event.pageX - 128) + "px")
                .style("top", (d3.event.pageY + 12) + "px");
          })
          .on("mouseout", function(d) {   
            tooltip.transition()
                .duration(100)
                .style("opacity", 0);
          });

    });

    // if ($("#colorvar").val() != "" && $("#colorvar").val() != "None") {
    //   // draw legend
    //   var legend = svg.selectAll(".legend")
    //       .data(color.domain())
    //     .enter().append("g")
    //       .attr("class", "legend")
    //       .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

    //   // draw legend colored rectangles
    //   legend.append("rect")
    //       .attr("x", width - 18)
    //       .attr("width", 18)
    //       .attr("height", 18)
    //       .style("fill", color);

    //   // draw legend text
    //   legend.append("text")
    //       .attr("x", width - 24)
    //       .attr("y", 9)
    //       .attr("dy", ".35em")
    //       .style("text-anchor", "end")
    //       .text(function(d) { return d;})
    // }
  }

  function updateAnalysis() {
    showLoading();

    var data = {
      "pid": $("#project").val(),
      "subsamplestep": $("#subsamplestep").val()
    };

    $.ajax({
      type: "POST",
      url: "rarefaction",
      data: data,
      success: function(result) {
        $("#display-error").hide();
        hideLoading();
        $("#analysis-container").show();
        $("#stats-container").show();
        abundancesObj = JSON.parse(result);
        renderRarefactionCurves(abundancesObj);
      },
      error: function(err) {
        hideLoading();
        $("#analysis-container").hide();
        $("#display-error").show();
        console.log(err)
      }
    });
  }
});