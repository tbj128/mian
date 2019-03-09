// ============================================================
// Fisher Exact JS Component
// ============================================================

//
// Initialization
//
var expectedLoadFactor = 0.1;

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
    if (getParameterByName("type") !== null) {
        $("#type").val(getParameterByName("type"));
    }
    if (getParameterByName("cutoff") !== null) {
        $("#cutoff").val(getParameterByName("cutoff"));
    }
    if ($("#type").val() === "SampleID") {
        $("#catvar-container").show();
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#catvar").change(function() {
        updateAnalysis();
    });
    $("#type").change(function() {
        if ($("#type").val() === "SampleID") {
            $("#catvar-container").show();
        } else {
            $("#catvar-container").hide();
        }
        updateAnalysis();
    });
    $("#cutoff").change(function() {
        updateAnalysis();
    });
    $("#download-svg").click(function() {
        downloadSVG("corrleation.network." + $("#maxFeatures").val() + "." + $("#cutoff").val());
    });
}

//
// Analysis Specific Methods
//
function customLoading() {}

function renderNetwork(abundancesObj) {
    var nodes = abundancesObj["nodes"];
    var links = abundancesObj["links"];
    var cutoffVal = abundancesObj["cutoff_val"];
    var nodesRemoved = abundancesObj["nodes_removed"];
    var uniqueGroups = abundancesObj["unique_groups"];

    $("#heads-up li.transient").hide();
    if (parseFloat(cutoffVal) !== parseFloat($("#cutoff").val())) {
        $("#item-actual-coefficient").show();
        $("#actual-coefficient").html(cutoffVal);
    }
    if (nodesRemoved > 0) {
        if ($("#type").val() === "SampleID") {
            $("#item-removed-samples").show();
            $("#removed-samples").html(nodesRemoved);
        } else {
            $("#item-removed-taxonomic-groups").show();
            $("#removed-taxonomic-groups").html(nodesRemoved);
        }
    }

    $("#analysis-container svg").empty();
    var svg = d3.select("#analysis-container svg");
    var legendWidth = 100,
        legendMargin = 12,
        width = $("#analysis-container svg").width() - legendWidth,
        height = $("#analysis-container svg").height(),
        radius = 5;

    var tooltip = d3
        .select("#analysis-container")
        .append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);

    var color = d3.scaleOrdinal(d3.schemeCategory10);

    var simulation = d3
        .forceSimulation(nodes)
        .force(
            "link",
            d3
            .forceLink()
            .id(function(d) {
                return d.id;
            })
        )
        .force("charge", d3.forceManyBody())
        .force("center", d3.forceCenter(width / 2, height / 2))
        .stop();

    simulation.force("link").links(links);

    for (var i = 0; i < 300; ++i) simulation.tick();

    var g = svg.append("g");
    var link = g
        .append("g")
        .attr("class", "links")
        .selectAll("line")
        .data(links)
        .enter()
        .append("line")
        .attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; })
        .attr("stroke", function(d) {
            if (d.v < 0) {
                return "#9d2424";
            } else if (d.v > 0) {
                return "#249d47";
            } else {
                return "#676767";
            }
        })
        .attr("stroke-width", function(d) {
//            return (1 + Math.abs(d.v)) ^ 2;
            return Math.sqrt(d.v);
        })
        .on("mouseover", function(d) {
            tooltip
                .transition()
                .duration(100)
                .style("opacity", 0.9);
            tooltip
                .html(
                    "Source: " +
                    d.source.id +
                    "<br />Target: " +
                    d.target.id +
                    "<br />Correlation Coefficient: " +
                    d.v
                )
                .style("left", d3.event.pageX + 10 + "px")
                .style("top", d3.event.pageY + "px");
        })
        .on("mouseout", function(d) {
            tooltip
                .transition()
                .duration(100)
                .style("opacity", 0);
        });

    var node = g
        .append("g")
        .attr("class", "nodes")
        .selectAll("circle")
        .data(nodes)
        .enter()
        .append("circle")
        .attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; })
        .attr("r", radius)
        .attr("fill", function(d) {
            return color(d.v);
        })
        .on("mouseover", function(d) {
            var message = "";
            if ($("#type").val() === "SampleID" && $("#catvar").val() !== "none") {
                message = "ID: <strong>" + d.id + "</strong><br />Categorical Variable: <strong>" + d.v + "</strong>";
            } else {
                message = "ID: <strong>" + d.id + "</strong><br />";
            }

            tooltip
                .transition()
                .duration(100)
                .style("opacity", 0.9);
            tooltip
                .html(message)
                .style("left", d3.event.pageX + 10 + "px")
                .style("top", d3.event.pageY + "px");
        })
        .on("mouseout", function(d) {
            tooltip
                .transition()
                .duration(100)
                .style("opacity", 0);
        })
        .call(
            d3
            .drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended)
        );

    node.append("title").text(function(d) {
        return d.id;
    });

    simulation.nodes(nodes).on("tick", ticked);

    simulation.force("link").links(links);

    if (uniqueGroups.length > 0) {
        var legend = svg
            .selectAll(".legend")
            .data(uniqueGroups)
            .enter()
            .append("g")
            .attr("class", "legend")
            .attr("transform", function(d, i) {
                return "translate(0," + i * 20 + ")";
            });

        legend
            .append("rect")
            .attr("x", width + legendMargin)
            .attr("width", 18)
            .attr("height", 18)
            .style("fill", color);

        legend
            .append("text")
            .attr("x", width + legendMargin + 24)
            .attr("y", 9)
            .attr("dy", ".35em")
            .text(function(d) {
                return d;
            });
    }

    //add zoom capabilities
    var zoom_handler = d3.zoom().on("zoom", zoom_actions);
    zoom_handler(svg);

    function zoom_actions() {
        g.attr("transform", d3.event.transform);
    }

    function ticked() {
        link
            .attr("x1", function(d) {
                return d.source.x;
            })
            .attr("y1", function(d) {
                return d.source.y;
            })
            .attr("x2", function(d) {
                return d.target.x;
            })
            .attr("y2", function(d) {
                return d.target.y;
            });

        node
            .attr("cx", function(d) {
                return (d.x = Math.max(radius, Math.min(width - radius, d.x)));
            })
            .attr("cy", function(d) {
                return (d.y = Math.max(radius, Math.min(height - radius, d.y)));
            });
    }

    function dragstarted(d) {
        if (!d3.event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
    }

    function dragended(d) {
        if (!d3.event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

function updateAnalysis() {
    var type = $("#type").val();
    if (type === "SampleID") {
        showLoading();
    } else {
        showLoading(expectedLoadFactor, true);
    }

    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var cutoff = $("#cutoff").val();

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
        level: level,
        catvar: catvar,
        type: type,
        cutoff: cutoff
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/correlation_network" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            var abundancesObj = JSON.parse(result);
            if (abundancesObj["links"].length == 0) {
                loadError();
            } else {
                loadSuccess();
                renderNetwork(abundancesObj);
            }
        },
        error: function(err) {
            loadError();
            console.log(err);
        }
    });
}
