
// ============================================================
// Tree JS Component
// ============================================================

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

    $("#taxonomy_display_level").change(function () {
      updateAnalysis();
    });

    $("#display_values").change(function () {
      updateAnalysis();
    });

    $("#exclude_unclassified").change(function () {
      updateAnalysis();
    });
}

//
// Analysis Specific Methods
//
function updateAnalysis(abundancesObj) {
    showLoading();

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var taxonomy_display_level = $("#taxonomy_display_level").val();
    var display_values = $("#display_values").val();
    var exclude_unclassified = $("#exclude_unclassified").val();

    var data = {
      "pid": $("#project").val(),
      "taxonomyFilter": taxonomyFilter,
      "taxonomyFilterRole": taxonomyFilterRole,
      "taxonomyFilterVals": taxonomyFilterVals,
      "sampleFilter": sampleFilter,
      "sampleFilterRole": sampleFilterRole,
      "sampleFilterVals": sampleFilterVals,
      "catvar": catvar,
      "taxonomy_display_level": taxonomyLevels[taxonomy_display_level],
      "display_values": display_values,
      "exclude_unclassified": exclude_unclassified
    };

    $.ajax({
      type: "POST",
      url: "tree",
      data: data,
      success: function(result) {
        $("#display-error").hide();
        hideLoading();
        $("#analysis-container").show();
        $("#stats-container").show();

        var abundancesObj = JSON.parse(result);
        renderTree(abundancesObj);
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

// GPL V3
// http://bl.ocks.org/mbostock/4063570
function renderTree(abundancesObj) {
    $("#analysis-container").empty();

    var root = abundancesObj["root"];
    var metaUnique = abundancesObj["metaUnique"];
    var numSamples = abundancesObj["numSamples"];
    root = root["children"][0]
    console.log(root)

    var taxonomy_display_level = $("#taxonomy_display_level").val();
    var taxLevelMultiplier = taxonomyLevels[taxonomy_display_level];
    if (taxLevelMultiplier < 0) {
      taxLevelMultiplier = Object.keys(taxonomyLevels).length;
    }
    taxLevelMultiplier++;

    var numLeaves = abundancesObj["numLeaves"];

    var width = 300 * taxLevelMultiplier + 26 * metaUnique.length,
        height = 20 * numLeaves;

    var cluster = d3.layout.cluster()
        .size([height, width - 32 * metaUnique.length - 80]);

    var diagonal = d3.svg.diagonal()
        .projection(function(d) { return [d.y, d.x]; });

    var svg = d3.select("#analysis-container").append("svg")
        .attr("width", width)
        .attr("height", height)
      .append("g")
        .attr("transform", "translate(40,0)");

    var tooltip = d3.select("#analysis-container").append("div") 
        .attr("class", "tooltip")       
        .style("opacity", 0)
        .style("width", "160px");

    var nodes = cluster.nodes(root),
        links = cluster.links(nodes);

    var link = svg.selectAll(".link")
        .data(links)
      .enter().append("path")
        .attr("class", "link")
        .attr("d", diagonal);

    var node = svg.selectAll(".node")
        .data(nodes)
      .enter().append("g")
        .attr("class", "node")
        .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; })

    node.append("circle")
        .attr("r", 4.5);

    // Use +8 and "start" to align text to the right of the circle
    node.append("text")
        .attr("dx", function(d) { return d.children ? -8 : -8; })
        .attr("dy", 3)
        .style("text-anchor", function(d) { return d.children ? "end" : "end"; })
        .text(function(d) { return d.name; });

    var nodeAbun = node.filter(function(d) {
      if (d.children) {
        return false;
      } else {
        return true;
      }
    });

    var display_values = $("#display_values").val();
    //   var maxSValue = abundancesObj["maxPerAbun"];
    var sValue = function(d) {
      if (d.hasOwnProperty("val")) {
        var maxPer = 0;
        for (var i = 0; i < metaUnique.length; i++) {
          if (display_values == "nonzero") {
            var perAbun = d["val"][metaUnique[i]].c / d["val"][metaUnique[i]].tc;
            if (perAbun > maxPer) {
              maxPer = perAbun;
            }
          } else {
            var perAbun = d["val"][metaUnique[i]];
            if (perAbun > maxPer) {
              maxPer = perAbun;
            }
          }
        }
        return maxPer; 
      } else {
        return 0;
      }
    };
    var maxSValue = d3.max(nodes, sValue);
    var sScale = d3.scale.linear().domain([0, maxSValue]).range([0.5, 8]);

    var color = d3.scale.category10();

    var a = false;
    for (var i = 0; i < metaUnique.length; i++) {
      nodeAbun.append("circle")
          .attr("transform", function(d) { return "translate(" + (24 + i * 24) + ",0)"; })
          .attr("class", "node-abun")
          .attr("meta", metaUnique[i])
          .style("fill", function(d) { return color(metaUnique[i]) })
          .attr("r", function(d) {
            if (display_values == "nonzero") {
              var perAbun = d["val"][metaUnique[i]].c / d["val"][metaUnique[i]].tc;
              return sScale(perAbun); 
            } else {
              var perAbun = d["val"][metaUnique[i]];
              return sScale(perAbun); 
            }
          })
          .on("mouseover", function(d) {
            var meta = d3.select(this).attr("meta");
            if (display_values == "nonzero") {
              var c = d["val"][meta].c;
              var tc = d["val"][meta].tc;

              var allMeta = Object.keys(d["val"]);
              var totalOTUCountsAllMeta = 0;
              allMeta.forEach(m => totalOTUCountsAllMeta += d["val"][m].tc);

              var numOTUs = totalOTUCountsAllMeta / numSamples;
              var per = 100 * c / tc;
              tooltip.transition()
                  .duration(100)
                  .style("opacity", 1);
              tooltip.html("<strong>" + meta + "</strong><br />Non-Zero Count: <strong>" + c + " / " + tc + " (" + per.toFixed(2) + "%)</strong><br />Number of OTUs: <strong>" + numOTUs + "</strong>")
                  .style("left", (d3.event.pageX - 160) + "px")
                  .style("top", (d3.event.pageY + 12) + "px");
            } else {
              var metaVal = d["val"][meta];
              var c = d["val"]["c"];
              var tc = d["val"]["tc"];

              var allMeta = Object.keys(d["val"]);
              var totalOTUCountsAllMeta = 0;
              allMeta.forEach(m => totalOTUCountsAllMeta += d["val"][m].tc);
              var numOTUs = tc / numSamples;
              var numSamplesForCat = c / numOTUs;

              tooltip.transition()
                  .duration(100)
                  .style("opacity", 1);

              var header = "";
              if (display_values == "avgabun") {
                header = "Average Abundance";
              } else if (display_values == "medianabun") {
                header = "Median Abundance";
              } else if (display_values == "maxabun") {
                header = "Max Abundance";
              }

              tooltip.html("<strong>" + meta + "</strong><br />" + header + ": <strong>" + metaVal + "</strong><br />Number of OTUs: <strong>" + numOTUs + "</strong><br />Number of Samples: <strong>" + numSamplesForCat + "</strong>")
                  .style("left", (d3.event.pageX - 160) + "px")
                  .style("top", (d3.event.pageY + 12) + "px");
            }
          })
          .on("mouseout", function(d) {   
            tooltip.transition()
                .duration(100)
                .style("opacity", 0);
          });
    }

    var legend = svg.selectAll(".legend")
          .data(color.domain())
        .enter().append("g")
          .attr("class", "legend")
          .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

      // draw legend colored rectangles
      legend.append("rect")
          .attr("x", 0)
          .attr("width", 18)
          .attr("height", 18)
          .style("fill", color);

      // draw legend text
      legend.append("text")
          .attr("x", 24)
          .attr("y", 9)
          .attr("dy", ".35em")
          .style("text-anchor", "start")
          .text(function(d) { return d;})

    d3.select(self.frameElement).style("height", height + "px");
}