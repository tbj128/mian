// ============================================================
// NMDS JS Component
// ============================================================
var abundancesObj = {};
var boundX = [];
var boundY = [];
var boundRenderFire = 0;
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
    if (getParameterByName("type") !== null) {
        $("#type").val(getParameterByName("type"));
    }
    if (getParameterByName("lambdathreshold") !== null) {
        $("#lambdathreshold").val(getParameterByName("lambdathreshold"));
    }
    if (getParameterByName("lambdaval") !== null) {
        $("#lambdaval").val(getParameterByName("lambdaval"));
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
        updateAnalysis();
    });

    $("#nmds1-range").change(function(e) {
        boundX = $("#nmds1-range")
            .val()
            .split(",");
        var diff = e.timeStamp - boundRenderFire;
        // Prevents the event from firing too often
        if (diff >= 300) {
            boundRenderFire = e.timeStamp;
            renderNMDS(abundancesObj["nmds"]);
        }
    });

    $("#nmds2-range").change(function(e) {
        boundY = $("#nmds2-range")
            .val()
            .split(",");
        var diff = e.timeStamp - boundRenderFire;
        // Prevents the event from firing too often
        if (diff >= 300) {
            boundRenderFire = e.timeStamp;
            renderNMDS(abundancesObj["nmds"]);
        }
    });

    $("#download-svg").click(function() {
        downloadSVG("nmds." + $("#catvar").val());
    });
}

//
// Analysis Specific Methods
//

function renderNMDS(data) {
    $("#analysis-container").empty();

    var margin = {
            top: 20,
            right: 20,
            bottom: 30,
            left: 40
        },
        width = 640 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    // setup x
    var xValue = function(d) {
            return d.nmds1;
        }, // data -> value
        xScale = d3.scaleLinear().range([0, width]), // value -> display
        xMap = function(d) {
            return xScale(xValue(d));
        }, // data -> display
        xAxis = d3
        .axisBottom()
        .scale(xScale);

    // setup y
    var yValue = function(d) {
            return d.nmds2;
        }, // data -> value
        yScale = d3.scaleLinear().range([height, 0]), // value -> display
        yMap = function(d) {
            return yScale(yValue(d));
        }, // data -> display
        yAxis = d3
        .axisLeft()
        .scale(yScale);

    // setup fill color
    var cValue = function(d) {
            return d.m;
        },
        color = d3.scaleOrdinal(d3.schemeCategory10);

    var zoom = d3.zoom()
        .on("zoom", zoomFunction);

    // add the graph canvas to the body of the webpage
    var svgBase = d3
        .select("#analysis-container")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);

    var svg = svgBase
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
        .call(zoom);

    var view = svg.append("rect")
        .attr("class", "zoom")
        .attr("width", width)
        .attr("height", height)
        .style("fill", "none")
        .style("pointer-events", "all")
        .call(zoom);

    var xDomain = [];
    if (boundX.length == 0) {
        xDomain = d3.extent(data, function(d) {
            return d.nmds1;
        });
    } else {
        xDomain = [boundX[0], boundX[1]];
    }

    var yDomain = [];
    if (boundY.length == 0) {
        yDomain = d3.extent(data, function(d) {
            return d.nmds2;
        });
    } else {
        yDomain = [boundY[0], boundY[1]];
    }

    xScale.domain(xDomain);
    yScale.domain(yDomain);

    // tooltip that appears when hovering over a dot
    var tooltip = d3
        .select("#analysis-container")
        .append("div")
        .attr("class", "tooltip")
        .style("opacity", 0)
        .style("width", "160px");

    // x-axis
    var gX = svg
        .append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);
    var gXTitle = gX
        .append("text")
        .attr("class", "label")
        .attr("x", width)
        .attr("y", -6)
        .style("text-anchor", "end")
        .text("Axis 1");

    // y-axis
    var gY = svg
        .append("g")
        .attr("class", "y axis")
        .call(yAxis);
    var gYTitle = gY
        .append("text")
        .attr("class", "label")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text("Axis 2");

    // draw dots
    var dots = svg
        .selectAll(".dot")
        .data(data)
        .enter()
        .append("circle")
        .attr("class", "dot")
        .attr("r", function(d) {
            return 3;
        })
        .attr("cx", xMap)
        .attr("cy", yMap)
        .style("fill", function(d) {
            return color(cValue(d));
        })
        .on("mouseover", function(d) {
            tooltip
                .transition()
                .duration(100)
                .style("opacity", 1);
            tooltip
                .html(
                    "<strong>" +
                    d.s +
                    "</strong><br /><strong>" +
                    d.m +
                    "</strong><br />NMDS1: <strong>" +
                    d.nmds1 +
                    "</strong><br />NMDS2: <strong>" +
                    d.nmds2 +
                    "</strong>"
                )
                .style("left", d3.event.pageX - 160 + "px")
                .style("top", d3.event.pageY + 12 + "px");
        })
        .on("mouseout", function(d) {
            tooltip
                .transition()
                .duration(100)
                .style("opacity", 0);
        });

    if ($("#colorvar").val() != "" && $("#colorvar").val() != "None") {
        // draw legend
        var legend = svg
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
            .attr("x", width - 18)
            .attr("width", 18)
            .attr("height", 18)
            .style("fill", color);

        // draw legend text
        legend
            .append("text")
            .attr("x", width - 24)
            .attr("y", 9)
            .attr("dy", ".35em")
            .style("text-anchor", "end")
            .text(function(d) {
                return d;
            });
    }

    function zoomFunction(){
        var newxScale = d3.event.transform.rescaleX(xScale);
        var newyScale = d3.event.transform.rescaleY(yScale);

        gX.call(xAxis.scale(newxScale));
        gY.call(yAxis.scale(newyScale));

        dots.attr("r", 3 / d3.event.transform.k);
        dots.attr("transform", d3.event.transform)
    };
}

function updateAnalysis() {
    showLoading(expectedLoadFactor);

    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var type = $("#type").val();

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
        type: type
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/nmds" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            abundancesObj = JSON.parse(result);

            if (abundancesObj["no_tree"]) {
                loadNoTree();
            } else if (abundancesObj["has_float"]) {
                loadFloatDataWarning();
            } else {
                loadSuccess();

                boundX = [];
                boundY = [];

                renderNMDS(abundancesObj["nmds"]);
            }
        },
        error: function(err) {
            loadError();
            console.log(err);
        }
    });
}
