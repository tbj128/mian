// ============================================================
// PCA JS Component
// ============================================================


var abundancesObj = {};
var boundX = [];
var boundY = [];
var boundRenderFire = 0;
var slider1 = null, slider2 = null;

//
// Initialization
//
initializeComponent({
    hasCatVar: true,
    hasCatVarNoneOption: true,
});
createSpecificListeners();

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#catvar").change(function () {
        updateAnalysis();
    });

    $("#pca1").change(function () {
        updateAnalysis();
    });

    $("#pca2").change(function () {
        updateAnalysis();
    });
    
    $("#pca1-range").change(function(e) {
        boundX = $("#pca1-range").val().split(",");
        var diff = e.timeStamp - boundRenderFire;
        // Prevents the event from firing too often
        if (diff >= 300) {
            boundRenderFire = e.timeStamp;
            renderPCA(abundancesObj["pca"]);
            renderPCAVar(abundancesObj["pcaVar"])
        }
    });

    $("#pca2-range").change(function(e) {
        boundY = $("#pca2-range").val().split(",");
        var diff = e.timeStamp - boundRenderFire;
        // Prevents the event from firing too often
        if (diff >= 300) {
            boundRenderFire = e.timeStamp;
            renderPCA(abundancesObj["pca"]);
            renderPCAVar(abundancesObj["pcaVar"]);
        }
    });
}

//
// Analysis Specific Methods
//
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

    // tooltip that appears when hovering over a dot
    var tooltip = d3.select("#analysis-container").append("div")
        .attr("class", "tooltip")
        .style("opacity", 0)
        .style("width", "160px");

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
            return 3;
        })
        .attr("cx", xMap)
        .attr("cy", yMap)
        .style("fill", function(d) { return color(cValue(d));})
        .on("mouseover", function(d) {
            tooltip.transition()
              .duration(100)
              .style("opacity", 1);
            tooltip.html("<strong>" + d.s + "</strong><br /><strong>" + d.m + "</strong><br />" + $("#pca1").val() + ": <strong>" + d.pca1 + "</strong><br />" + $("#pca2").val() + ": <strong>" + d.pca2 + "</strong>")
              .style("left", (d3.event.pageX - 160) + "px")
              .style("top", (d3.event.pageY + 12) + "px");
        })
        .on("mouseout", function(d) {
            tooltip.transition()
                .duration(100)
                .style("opacity", 0);
        });

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
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var pca1 = $("#pca1").val();
    var pca2 = $("#pca2").val();

    var data = {
      "pid": $("#project").val(),
      "taxonomyFilter": taxonomyFilter,
      "taxonomyFilterRole": taxonomyFilterRole,
      "taxonomyFilterVals": taxonomyFilterVals,
      "sampleFilter": sampleFilter,
      "sampleFilterRole": sampleFilterRole,
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
        $("#display-error").hide();
        hideLoading();
        $("#analysis-container").show();
        $("#stats-container").show();

        abundancesObj = JSON.parse(result);
        boundX = [];
        boundY = [];

        // Update sliders

        if (slider1 === null) {
          $("#pca1-range").show();
          slider1 = new Slider("#pca1-range", {
            min: abundancesObj["pca1Min"],
            max: abundancesObj["pca1Max"],
            step: 0.1,
            value: [abundancesObj["pca1Min"], abundancesObj["pca1Max"]],
          });
        } else {
          slider1.setAttribute("min", abundancesObj["pca1Min"]);
          slider1.setAttribute("max", abundancesObj["pca1Max"]);
          slider1.setAttribute("value", [abundancesObj["pca1Min"], abundancesObj["pca1Max"]]);
          slider1.refresh();
        }

        if (slider2 === null) {
          $("#pca2-range").show();
          slider2 = new Slider("#pca2-range", {
            min: abundancesObj["pca2Min"],
            max: abundancesObj["pca2Max"],
            step: 0.1,
            value: [abundancesObj["pca2Min"], abundancesObj["pca2Max"]],
          });
        } else {
          slider2.setAttribute("min", abundancesObj["pca2Min"]);
          slider2.setAttribute("max", abundancesObj["pca2Max"]);
          slider2.setAttribute("value", [abundancesObj["pca2Min"], abundancesObj["pca2Max"]]);
          slider2.refresh();
        }

        renderPCA(abundancesObj["pca"]);
        renderPCAVar(abundancesObj["pcaVar"]);
      },
      error: function(err) {
        hideLoading();
        $("#analysis-container").hide();
        $("#stats-container").hide();
        $("#display-error").show();
        console.log(err);
      }
    });
}