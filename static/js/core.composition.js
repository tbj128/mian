$(document).ready(function() {
  // Global variables storing the data
  var uniqueCatvarVals = [];

  // Initialization
  updateCatVar(function() {
    $("#catvar").prepend("<option value='All'>None</option>");
    updateAnalysis();
  });
  createListeners();

  function createListeners() {
    $("#project").change(function () {
      updateCatVar(function() {
        $("#catvar").prepend("<option value='All'>None</option>");
        updateAnalysis();
      });
    });

    $("#taxonomy").change(function () {
      updateCatVar(function() {
        $("#catvar").prepend("<option value='All'>None</option>");
        updateAnalysis();
      });
    });

    $("#catvar").change(function () {
      $("#catvar").prepend("<option value='All'>None</option>");
      updateAnalysis();
    });

    $("#plotType").change(function () {
      updateAnalysis();
    });

    $("#download-svg").click(function() {
      download();
    });
  }

  function getTaxonomicLevel() {
    return $("#taxonomy").val();
  }

  function updateAnalysis() {
    showLoading();
    $("#stats-container").fadeIn(250);

    var level = taxonomyLevels[getTaxonomicLevel()];

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
      "level": level,
      "catvar": catvar
    };

    $.ajax({
      type: "POST",
      url: "composition",
      data: data,
      success: function(result) {
        hideLoading();
        var abundancesObj = JSON.parse(result);
        if ($("#plotType").val() == "bar") {
          renderBarplot(abundancesObj);
        } else {
          renderDonut(abundancesObj);
        }
      },
      error: function(err) {
        console.log(err)
      }
    });
  }

  function renderBarplot(abundancesObj) {
    $('#analysis-container').empty();

    var data = abundancesObj["abundances"];
    uniqueCatvarVals = abundancesObj["metaVals"];
    var uniqueTaxas = data.map(function(d) { return d.t; });

    var margin = {top: 20, right: 20, bottom: 30, left: 56},
        width = Math.max(120, 24 * uniqueCatvarVals.length + 16) * uniqueTaxas.length - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom,
        barWidth = 24;

    var xScaleTax = d3.scale.ordinal()
                    .domain(uniqueTaxas)
                    .rangeRoundBands([0, width]),
        xScaleCatvar = d3.scale.ordinal(),
        xAxis = d3.svg.axis().scale(xScaleTax).orient("bottom");
    xScaleCatvar.domain(uniqueCatvarVals).rangeRoundBands([0, xScaleTax.rangeBand()]);
    var rangeOffset = (xScaleCatvar.rangeBand()*uniqueCatvarVals.length - (barWidth*uniqueCatvarVals.length)) / 2;

    data.forEach(function(d) {
      d.cv = uniqueCatvarVals.map(function(name) { return {name: name, value: +d.o[name]}; });
    });

    var yScale = d3.scale.linear().range([height, 0]),
        yAxis = d3.svg.axis().scale(yScale).orient("left");
    yScale.domain([0, d3.max(data, function(d) { 
      return d3.max(d.cv, function(d) { 
        return d.value; 
      }); 
    })]);

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

      svg.append("g")
          .attr("class", "x axis")
          .attr("transform", "translate(0," + height + ")")
          .call(xAxis);

      svg.append("g")
          .attr("class", "y axis")
          .call(yAxis)
        .append("text")
          .attr("transform", "rotate(-90)")
          .attr("y", 6)
          .attr("dy", ".71em")
          .style("text-anchor", "end")
          .text("Average Relative Abundance");

      var tax = svg.selectAll(".tax")
          .data(data)
        .enter().append("g")
          .attr("class", "tax")
          .attr("transform", function(d) { return "translate(" + xScaleTax(d.t) + ",0)"; });

      tax.selectAll("rect")
          .data(function(d) { return d.cv; })
        .enter().append("rect")
          .attr("width", barWidth) // xScaleCatvar.rangeBand()
          .attr("x", function(d, i) { return rangeOffset + i * barWidth; }) // xScaleCatvar(d.name)
          .attr("y", function(d) { return yScale(d.value); })
          .attr("height", function(d) { return height - yScale(d.value); })
          .style("fill", function(d) { return color(d.name); })
          .attr("class", "bar")
          .on("mouseover", function(d) {
            var meta = d.name;
            tooltip.transition()
                .duration(100)
                .style("opacity", 1);
            tooltip.html("<strong>" + d.name + "</strong><br />Average Relative Abundance: <strong>" + d.value + "</strong>")
                .style("left", (d3.event.pageX - 128) + "px")
                .style("top", (d3.event.pageY + 12) + "px");
          })
          .on("mouseout", function(d) {   
            tooltip.transition()
                .duration(100)
                .style("opacity", 0);
          });



      var legend = svg.selectAll(".legend")
          .data(uniqueCatvarVals.slice())
        .enter().append("g")
          .attr("class", "legend")
          .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

      legend.append("rect")
          .attr("x", width - 18)
          .attr("width", 18)
          .attr("height", 18)
          .style("fill", color);

      legend.append("text")
          .attr("x", width - 24)
          .attr("y", 9)
          .attr("dy", ".35em")
          .style("text-anchor", "end")
          .text(function(d) { return d; });
  }



  function renderDonut(abundancesObj) {
    $('#analysis-container').empty();

    var data = abundancesObj["abundances"];
    uniqueCatvarVals = abundancesObj["metaVals"];
    var uniqueTaxas = [];
    data.forEach(function(d) {
      var pos = false;
      d.cv = uniqueCatvarVals.map(function(name) {
        if (d.o[name] > 0) {
          pos = true;
        }
        return {name: name, value: +d.o[name]}; 
      });

      if (pos) {
        uniqueTaxas.push(d.t);
      } 
    });

    uniqueCatvarVals.forEach(function(cat, index) {
      var margin = {top: 20, right: 20, bottom: 30, left: 56},
          width = 540 - margin.left - margin.right,
          height = 540 - margin.top - margin.bottom,
          radius = Math.min(width, height) / 2;

      var color = d3.scale.category20();
      if (uniqueTaxas.length < 20) {
        color = d3.scale.category10();
      }

      var arc = d3.svg.arc()
          .outerRadius(radius - 10)
          .innerRadius(radius - 90);

      var pie = d3.layout.pie()
          .sort(null)
          .value(function(d) {
            return d.o[cat]; 
          });

      var svg = d3.select("#analysis-container").append("svg")
          .attr("width", width)
          .attr("height", height)
        .append("g")
          .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

      svg.append("text")
          .attr("dy", ".35em")
          .attr("class", "donut-header")
          .attr("text-anchor", "middle")
          .text(cat);

      var tooltip = d3.select("#analysis-container").append("div") 
        .attr("class", "tooltip")       
        .style("opacity", 0);

      var g = svg.selectAll(".arc")
          .data(pie(data))
        .enter().append("g")
          .attr("class", "arc");

      g.append("path")
          .attr("d", arc)
          .style("fill", function(d) { 
            return color(d.data.t); 
          })
          .on("mouseover", function(d) {
            tooltip.transition()
                .duration(100)
                .style("opacity", 1);
            tooltip.html("<strong>" + d.data.t + "</strong><br />" + cat + "<br />Average Relative Abundance: <strong>" + d.value + "</strong>")
                .style("left", (d3.event.pageX - 128) + "px")
                .style("top", (d3.event.pageY + 12) + "px");
          })
          .on("mouseout", function(d) {   
            tooltip.transition()
                .duration(100)
                .style("opacity", 0);
          });

      g.append("text")
          .attr("transform", function(d) { return "translate(" + arc.centroid(d) + ")"; })
          .attr("dy", ".35em")
          .attr("text-anchor", "middle")
          .attr("fill", "#333")
          .text(function(d) {
            if (d.data.o[cat] >= 0.05) {
              return d.data.t; 
            }
          });
    });
  }

  function download() {
    $("#donwload-canvas").empty();
    var svgsElems = $("#analysis-container").children();
    var svgElemWidth = $("#analysis-container svg").width();
    var svgContainerWidth = svgElemWidth;
    if ($("#plotType").val() != "bar") {
      svgContainerWidth = uniqueCatvarVals.length*svgElemWidth
    }

    var $tmpCanvas = $("#donwload-canvas");
    $tmpCanvas.height($("#analysis-container svg").height());
    $tmpCanvas.width(svgContainerWidth);

    var svgContainer = document.createElement("svg");
    $svgContainer = $(svgContainer);
    $svgContainer.attr("id", "analysis-group");
    $svgContainer.attr("width", svgContainerWidth);

    var index = 0;
    var svg = "";
    for (var i = 0; i < svgsElems.length; i++) {
      if (svgsElems[i].tagName === "svg") {
        var e = svgsElems[i];
        e.setAttribute("x", index * svgElemWidth);
        $svgContainer.append($(e).clone());
        index++;
      }
    }

    canvg($tmpCanvas[0], $svgContainer[0].outerHTML, {
      renderCallback: function() {
        var dataURL = $tmpCanvas[0].toDataURL('image/png');
        var ctx = $tmpCanvas[0].getContext("2d");

        var project = $("#project").val();
        var plotType = $("#plotType").val();
        var tax = $("#taxonomy").val();
        var catvar = $("#catvar").val();
        var filename = project + "." + plotType + "." + tax + "." + catvar + ".png";

        $tmpCanvas[0].toBlob(function(blob) {
            saveAs(blob, filename);
        });

        $tmpCanvas.empty();
      }
    });
  }
});