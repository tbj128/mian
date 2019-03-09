// ============================================================
// Tree JS Component
// ============================================================

var expectedLoadFactor = 500;

//
// Initialization
//
initializeFields();
initializeComponent({
    hasCatVar: true,
    hasCatVarNoneOption: true
});
createSpecificListeners();

//
// Initializes fields based on the URL params
//
function initializeFields() {
    if (getParameterByName("taxonomy_display_level") !== null) {
        $("#taxonomy_display_level").val(taxonomyLevelsReverseLookup[getParameterByName("taxonomy_display_level")]);
    }
    if (getParameterByName("display_values") !== null) {
        $("#display_values").val(getParameterByName("display_values"));
    }
    if (getParameterByName("exclude_unclassified") !== null) {
        $("#exclude_unclassified").val(getParameterByName("exclude_unclassified"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#catvar").change(function() {
        updateAnalysis();
    });

    $("#taxonomy_display_level").change(function() {
        updateAnalysis();
    });

    $("#display_values").change(function() {
        updateAnalysis();
    });

    $("#exclude_unclassified").change(function() {
        updateAnalysis();
    });

    $("#download-svg").click(function() {
        downloadSVG("tree." + $("#catvar").val() + "." + $("#taxonomy_display_level").val());
    });
}

//
// Analysis Specific Methods
//
function updateAnalysis(abundancesObj) {
    showLoading(expectedLoadFactor);

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
        pid: $("#project").val(),
        taxonomyFilterCount: getLowCountThreshold(),
        taxonomyFilterPrevalence: getPrevalenceThreshold(),
        taxonomyFilter: taxonomyFilter,
        taxonomyFilterRole: taxonomyFilterRole,
        taxonomyFilterVals: taxonomyFilterVals,
        sampleFilter: sampleFilter,
        sampleFilterRole: sampleFilterRole,
        sampleFilterVals: sampleFilterVals,
        catvar: catvar,
        taxonomy_display_level: taxonomyLevels[taxonomy_display_level],
        display_values: display_values,
        exclude_unclassified: exclude_unclassified
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/tree" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            loadSuccess();

            var abundancesObj = JSON.parse(result);
            renderTree(abundancesObj);
        },
        error: function(err) {
            loadError();
            console.log(err);
        }
    });
}

// GPL V3
// http://bl.ocks.org/mbostock/4063570
function renderTree(abundancesObj) {
    $("#analysis-container").empty();

    var root = d3.hierarchy(abundancesObj["root"]);
    var metaUnique = abundancesObj["metaUnique"];
    var numSamples = abundancesObj["numSamples"];
    root = root["children"][0];
    console.log(root);

    var taxonomy_display_level = $("#taxonomy_display_level").val();
    var taxLevelMultiplier = taxonomyLevels[taxonomy_display_level];
    if (taxLevelMultiplier < 0) {
        taxLevelMultiplier = Object.keys(taxonomyLevels).length;
    }
    taxLevelMultiplier++;

    var numLeaves = abundancesObj["numLeaves"];

    var width = 300 * taxLevelMultiplier + 26 * metaUnique.length,
        height = 20 * numLeaves + 40;

    var cluster = d3.cluster()
        .size([height - 40, width - 32 * metaUnique.length - 80]);

//    var diagonal = d3.diagonal().projection(function(d) {
//        return [d.y, d.x];
//    });

    var diagonal = d3.linkHorizontal()
        .x(function(d) { return d.y; })
        .y(function(d) { return d.x; });

    var svgBase = d3
        .select("#analysis-container")
        .append("svg")
        .attr("width", width)
        .attr("height", height);
    var svg = svgBase
        .append("g")
        .attr("transform", "translate(40,40)");

    var tooltip = d3
        .select("#analysis-container")
        .append("div")
        .attr("class", "tooltip")
        .style("opacity", 0)
        .style("width", "160px");

    var nodes = cluster(root),
        links = nodes.links();
    nodes = nodes.descendants();

    var link = svg
        .selectAll(".link")
        .data(links)
        .enter()
        .append("path")
        .attr("class", "link")
        .attr("d", diagonal);

    var node = svg
        .selectAll(".node")
        .data(nodes)
        .enter()
        .append("g")
        .attr("class", "node")
        .attr("transform", function(d) {
            return "translate(" + d.y + "," + d.x + ")";
        });

    node.append("circle").attr("r", 4.5);

    // Use +8 and "start" to align text to the right of the circle
    node
        .append("text")
        .attr("dx", function(d) {
            return d.children ? -8 : -8;
        })
        .attr("dy", 3)
        .style("text-anchor", function(d) {
            return d.children ? "end" : "end";
        })
        .text(function(d) {
            return d.data.name;
        });

    var nodeAbun = node.filter(function(d) {
        if (d.children) {
            return false;
        } else {
            return true;
        }
    });

    var display_values = $("#display_values").val();
    var sValue = function(d) {
        if (d.data.hasOwnProperty("val")) {
            var maxPer = 0;
            for (var i = 0; i < metaUnique.length; i++) {
                if (d.data["val"][metaUnique[i]]) {
                    if (display_values == "nonzero" || display_values == "nonzerosample") {
                        var perAbun =
                            d.data["val"][metaUnique[i]].c / d.data["val"][metaUnique[i]].tc;
                        if (perAbun > maxPer) {
                            maxPer = perAbun;
                        }
                    } else {
                        var perAbun = d.data["val"][metaUnique[i]];
                        if (perAbun > maxPer) {
                            maxPer = perAbun;
                        }
                    }
                }
            }
            return maxPer;
        } else {
            return 0;
        }
    };
    var maxSValue = d3.max(nodes, sValue);
    var sScale = d3.scaleLinear()
        .domain([0, maxSValue])
        .range([0.5, 8]);

    var color = d3.scaleOrdinal(d3.schemeCategory10);

    var a = false;
    for (var i = 0; i < metaUnique.length; i++) {
        nodeAbun
            .append("circle")
            .attr("transform", function(d) {
                return "translate(" + (24 + i * 24) + ",0)";
            })
            .attr("class", "node-abun")
            .attr("meta", metaUnique[i])
            .style("fill", function(d) {
                return color(metaUnique[i]);
            })
            .attr("r", function(d) {
                if (d.data["val"][metaUnique[i]]) {
                    if (display_values === "nonzero" || display_values === "nonzerosample") {
                        var perAbun =
                            d.data["val"][metaUnique[i]].c / d.data["val"][metaUnique[i]].tc;
                        return sScale(perAbun);
                    } else {
                        var perAbun = d.data["val"][metaUnique[i]];
                        return sScale(perAbun);
                    }
                } else {
                    return sScale(0);
                }
            })
            .on("mouseover", function(d) {
                var meta = d3.select(this).attr("meta");
                if (display_values === "nonzero") {
                    var c = d.data["val"][meta].c;
                    var tc = d.data["val"][meta].tc;
                    var numOTUs = d.data["val"].numOTUs;

                    var per = 100 * c / tc;
                    tooltip
                        .transition()
                        .duration(100)
                        .style("opacity", 1);
                    tooltip
                        .html(
                            "<strong>" +
                            meta +
                            "</strong><br /><br />Non-Zero Count: <strong>" +
                            c +
                            " out of " + tc + " OTU-samples (" +
                            per.toFixed(2) +
                            "%)</strong><br /><br />Number of OTUs in this taxonomic group: <strong>" +
                            numOTUs +
                            "</strong><br /><br />Number of Samples: <strong>" +
                            (tc / numOTUs) +
                            "</strong>"
                        )
                        .style("left", d3.event.pageX - 160 + "px")
                        .style("top", d3.event.pageY + 12 + "px");
                } else if (display_values === "nonzerosample") {
                    var c = d.data["val"][meta].c;
                    var tc = d.data["val"][meta].tc;
                    var numOTUs = d.data["val"].numOTUs;

                    var per = 100 * c / tc;
                    tooltip
                        .transition()
                        .duration(100)
                        .style("opacity", 1);
                    tooltip
                        .html(
                            "<strong>" +
                            meta +
                            "</strong><br /><br />Non-Zero Count: <strong>" +
                            c +
                            " out of " + (tc / numOTUs) + " samples (" +
                            per.toFixed(2) +
                            "%)</strong><br /><br />Number of OTUs in this taxonomic group: <strong>" +
                            numOTUs +
                            "</strong>"
                        )
                        .style("left", d3.event.pageX - 160 + "px")
                        .style("top", d3.event.pageY + 12 + "px");
                } else {
                    var metaVal = d.data["val"][meta];
                    var c = d.data["val"]["c"];
                    var tc = d.data["val"]["tc"];
                    var numOTUs = d.data["val"].numOTUs;

                    tooltip
                        .transition()
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

                    tooltip
                        .html(
                            "<strong>" +
                            meta +
                            "</strong><br /><br />" +
                            header +
                            ": <strong>" +
                            metaVal +
                            "</strong><br /><br />Number of Samples: <strong>" +
                            (tc / numOTUs) +
                            "</strong><br /><br />Number of OTUs in this taxonomic group: <strong>" +
                            numOTUs +
                            "</strong>"
                        )
                        .style("left", d3.event.pageX - 160 + "px")
                        .style("top", d3.event.pageY + 12 + "px");
                }
            })
            .on("mouseout", function(d) {
                tooltip
                    .transition()
                    .duration(100)
                    .style("opacity", 0);
            });
    }

    var legend = svgBase
        .selectAll(".legend")
        .data(color.domain())
        .enter()
        .append("g")
        .attr("class", "legend")
        .attr("transform", function(d, i) {
            return "translate(0," + i * 20 + ")";
        });

    // draw legend colored rectangles
    legend
        .append("rect")
        .attr("x", 0)
        .attr("width", 18)
        .attr("height", 18)
        .style("fill", color);

    // draw legend text
    legend
        .append("text")
        .attr("x", 24)
        .attr("y", 9)
        .attr("dy", ".35em")
        .style("text-anchor", "start")
        .text(function(d) {
            return d;
        });

    d3.select(self.frameElement).style("height", height + "px");
}
