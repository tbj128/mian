$(document).ready(function() {
  var abundancesObj = {};

  // Initialization
  updateTaxonomicLevel(true, function() {
    updateAnalysis();
  });
  createListeners();

  function createListeners() {
    $('#corrvar2 option:eq(1)').attr('selected', 'selected');

    $("#project").change(function() {
      updateTaxonomicLevel(false, function() {
        updateCorrVar(function() {
          updateAnalysis();
        });
      });
    });

    $("#taxonomy").change(function () {
      updateTaxonomicLevel(false, function() {
        updateAnalysis();
      });
    });

    $("#taxonomy-specific").change(function () {
      updateAnalysis();
    });

    $("#corrvar1").change(function () {
      updateAnalysis();
    });

    $("#corrvar2").change(function () {
      updateAnalysis();
    });

    $("#colorvar").change(function () {
      updateAnalysis();
    });

    $("#sizevar").change(function () {
      updateAnalysis();
    });

    $("#samplestoshow").change(function () {
      updateAnalysis();
    });
  }

  function renderCorrelations(abundancesObj) {
    if ($.isEmptyObject(abundancesObj)) {
      return;
    }

    var data = abundancesObj["corrArr"];
    var coef = abundancesObj["coef"];
    var pValue = abundancesObj["pval"];

    $("#stats-coef").text(coef);
    $("#stats-pval").text(pValue);

    $("#analysis-container").empty();

    var margin = {top: 20, right: 20, bottom: 30, left: 56},
        width = 960 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    // setup x 
    var xValue = function(d) { return d.c1;}, // data -> value
        xScale = d3.scale.linear().range([0, width]), // value -> display
        xMap = function(d) { return xScale(xValue(d));}, // data -> display
        xAxis = d3.svg.axis().scale(xScale).orient("bottom");

    // setup y
    var yValue = function(d) { return d.c2;}, // data -> value
        yScale = d3.scale.linear().range([height, 0]), // value -> display
        yMap = function(d) { return yScale(yValue(d));}, // data -> display
        yAxis = d3.svg.axis().scale(yScale).orient("left");

    // setup fill color
    var cValue = function(d) { return d.color;},
        color = d3.scale.category10();

    // setup circle size
    var sValue = function(d) { return d.size; };
    var minSValue = d3.min(data, sValue);
    var maxSValue = d3.max(data, sValue);
    var sScale = d3.scale.linear().domain([minSValue, maxSValue]).range([2, 8]);

    // add the graph canvas to the body of the webpage
    var svg = d3.select("#analysis-container").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // don't want dots overlapping axis, so add in buffer to data domain
    xScale.domain([d3.min(data, xValue)-d3.max(data, xValue)*0.01, d3.max(data, xValue)+d3.max(data, xValue)*0.01]);
    yScale.domain([d3.min(data, yValue)-d3.max(data, yValue)*0.01, d3.max(data, yValue)+d3.max(data, yValue)*0.01]);

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
        .text($("#corrvar1").val());

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
        .text($("#corrvar2").val());

    // draw dots
    svg.selectAll(".dot")
        .data(data)
      .enter().append("circle")
        .attr("class", "dot")
        .attr("r", function(d) { 
            if ($("#sizevar").val() != "" && $("#sizevar").val() != "None") {
              return sScale(sValue(d)); 
            } else {
              return 3;
            }
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

  function updateAnalysis() {
    showLoading();
    
    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var corrvar1 = $("#corrvar1").val();
    var corrvar2 = $("#corrvar2").val();
    var colorvar = $("#colorvar").val();
    var sizevar = $("#sizevar").val();
    var samplestoshow = $("#samplestoshow").val();

    var data = {
      "pid": $("#project").val(),
      "taxonomyFilter": taxonomyFilter,
      "taxonomyFilterVals": taxonomyFilterVals,
      "sampleFilter": sampleFilter,
      "sampleFilterVals": sampleFilterVals,
      "level": level,
      "corrvar1": corrvar1,
      "corrvar2": corrvar2,
      "colorvar": colorvar,
      "sizevar": sizevar,
      "samplestoshow": samplestoshow
    };

    $.ajax({
      type: "POST",
      url: "correlations",
      data: data,
      success: function(result) {
        $("#display-error").hide();
        hideLoading();
        $("#analysis-container").show();
        $("#stats-container").show();
        abundancesObj = JSON.parse(result);
        renderCorrelations(abundancesObj);
      },
      error: function(err) {
        hideLoading();
        $("#analysis-container").hide();
        $("#stats-container").hide();
        $("#display-error").show();
        console.log(err)
      }
    });
  }

  function updateCorrVar(callback) {
    $.ajax({
      url: "metadata_headers?pid=" + $("#project").val(), 
      success: function(result) {
        var json = ["None"];
        json.push.apply(json, JSON.parse(result));
        json.push("Abundances");
        $("#corrvar1").empty();
        $("#corrvar2").empty();
        $("#sizevar").empty();
        $("#colorvar").empty();
        for (var i = 0; i < json.length; i++) {
          if (i != 0) {
            addCorrOption("corrvar1", json[i]);
            addCorrOption("corrvar2", json[i]);
          }
          addCorrOption("sizevar", json[i]);
          addCorrOption("colorvar", json[i]);
        }
        $('#corrvar2 option:eq(1)').attr('selected', 'selected');
        callback();
      }
    });
  }

  function addCorrOption(elemID, val) {
    var o = document.createElement("option");
    o.setAttribute("value", val);
    var t = document.createTextNode(val);
    if (val == "Abundances") {
      t = document.createTextNode("Aggregate Abundances");
    }
    o.appendChild(t);
    document.getElementById(elemID).appendChild(o);
  }
});