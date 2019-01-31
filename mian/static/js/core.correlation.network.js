// ============================================================
// Fisher Exact JS Component
// ============================================================

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
    if (getParameterByName("maxFeatures") !== null) {
        $("#maxFeatures").val(getParameterByName("maxFeatures"));
    }
    if (getParameterByName("cutoff") !== null) {
        $("#cutoff").val(getParameterByName("cutoff"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#maxFeatures").change(function() {
        updateAnalysis();
    });
    $("#cutoff").change(function() {
        updateAnalysis();
    });
}

//
// Analysis Specific Methods
//
function customLoading() {}

function renderNetwork(abundancesObj) {
    var nodes = abundancesObj["nodes"];
    var links = abundancesObj["links"];

    $("#analysis-container svg").empty();
    var svg = d3.select("#analysis-container svg");
    var width = $("#analysis-container svg").width(),
        height = $("#analysis-container svg").height(),
        radius = 5;

    var tooltip = d3
        .select("#analysis-container")
        .append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);

    var color = d3.scaleOrdinal(d3.schemeCategory20);

    var simulation = d3
        .forceSimulation()
        .force(
            "link",
            d3
            .forceLink()
            .id(function(d) {
                return d.id;
            })
            .distance(function() {
                return 20;
            })
        )
        .force("charge", d3.forceManyBody())
        .force("center", d3.forceCenter(width / 2, height / 2));

    var g = svg.append("g");
    var link = g
        .append("g")
        .attr("class", "links")
        .selectAll("line")
        .data(links)
        .enter()
        .append("line")
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
            return Math.abs(d.v);
            // return Math.sqrt(Math.abs(d.v));
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
                    "<br />Strength: " +
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
        .attr("r", radius)
        .attr("fill", function(d) {
            return "#242C70";
            //return color(d.c);
        })
        .on("mouseover", function(d) {
            tooltip
                .transition()
                .duration(100)
                .style("opacity", 0.9);
            tooltip
                .html("ID: " + d.id)
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
    showLoading();

    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var maxFeatures = $("#maxFeatures").val();
    var cutoff = $("#cutoff").val();

    var data = {
        pid: $("#project").val(),
        taxonomyFilter: taxonomyFilter,
        taxonomyFilterRole: taxonomyFilterRole,
        taxonomyFilterVals: taxonomyFilterVals,
        sampleFilter: sampleFilter,
        sampleFilterRole: sampleFilterRole,
        sampleFilterVals: sampleFilterVals,
        level: level,
        catvar: catvar,
        maxFeatures: maxFeatures,
        cutoff: cutoff
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: "correlation_network",
        data: data,
        success: function(result) {
            $("#display-error").hide();
            hideLoading();
            $("#analysis-container").show();
            $("#stats-container").show();
            var abundancesObj = JSON.parse(result);
            if (abundancesObj["links"].length == 0) {
                $("#analysis-container").hide();
                $("#stats-container").hide();
                $("#display-error").show();
            } else {
                $("#analysis-container").show();
                $("#stats-container").show();
                $("#display-error").hide();
                renderNetwork(abundancesObj);
            }
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
