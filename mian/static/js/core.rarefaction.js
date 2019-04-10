// ============================================================
// Rarefaction JS Component
// ============================================================
var abundancesObj = {};
var expectedLoadFactor = 500;

//
// Initialization
//
initializeFields();
checkSubsampleWarning();
initializeComponent({
    hasCatVar: true,
    hasCatVarNoneOption: true
});
createSpecificListeners();

//
// Initializes fields based on the URL params
//
var initialColorVar = getParameterByName("colorvar");
function initializeFields() {
    // Not used
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#project").change(function() {
        checkSubsampleWarning();
    });

    $("#colorvar").change(function() {
        updateAnalysis();
    });

    $("#maxsubsample").change(function() {
        updateAnalysis();
    });

    $("#subsamplestep").change(function() {
        updateAnalysis();
    });

    $("#download-svg").click(function() {
        downloadSVG("rarefaction." + $("#maxsubsample").val() + "." + $("#subsamplestep").val());
    });
}

//
// Analysis Specific Methods
//
function renderRarefactionCurves(abundancesObj) {
    if ($.isEmptyObject(abundancesObj)) {
        return;
    }

    var data = abundancesObj["results"];
    var maxVal = abundancesObj["maxVal"];
    var maxSubsampleVal = abundancesObj["maxHeader"];

    $("#analysis-container").empty();

    var margin = {
            top: 20,
            right: 180,
            bottom: 30,
            left: 56
        },
        width = 1000 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    // setup x
    var xValue = function(d) {
            return d.h;
        },
        xScale = d3.scaleLinear().range([0, width]),
        xMap = function(d, i) {
            return xScale(xValue(d, i));
        },
        xAxis = d3.axisBottom(xScale);

    // setup y
    var yValue = function(d) {
            return d.v;
        },
        yScale = d3.scaleLinear().range([height, 0]),
        yMap = function(d) {
            return yScale(yValue(d));
        },
        yAxis = d3.axisLeft(yScale);

    // setup fill color
    var color = d3.scaleOrdinal(d3.schemeCategory10);

    // add the graph canvas to the body of the webpage
    var svg = d3
        .select("#analysis-container")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var tooltip = d3
        .select("#analysis-container")
        .append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);

    // don't want dots overlapping axis, so add in buffer to data domain
    xScale.domain([0, maxSubsampleVal]);
    yScale.domain([0, maxVal]);

    // x-axis
    svg
        .append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis)
        .append("text")
        .attr("class", "label")
        .attr("x", width)
        .attr("y", -6)
        .style("text-anchor", "end")
        .style("fill", "#333")
        .style("font-weight", "300")
        .style("font-size", "11px")
        .text("Sample Size");

    // y-axis
    svg
        .append("g")
        .attr("class", "y axis")
        .call(yAxis)
        .append("text")
        .attr("class", "label")
        .attr("transform", "rotate(-90)")
        .attr("x", -1 * margin.top)
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .style("fill", "#333")
        .style("font-weight", "300")
        .style("font-size", "11px")
        .text("Number of OTUs (Species Richness)");

    $.each(data, function(index, sample) {
        var colorMeta = sample.color;
        var col = color(colorMeta);
        var sampleID = sample.sampleID;

        // Each sample contains two arrays
        //    "headers": array of actual subsample amounts
        //    "vals": array of actual subsampled values
        var transformedSample = [];
        for (var i = 0; i < sample.headers.length; i++) {
            transformedSample.push({
                h: sample.headers[i],
                v: sample.vals[i]
            });
        }

        // draw dots
        var g1 = svg.append("g");
        g1
            .selectAll(".point")
            .data(transformedSample)
            .enter()
            .append("circle")
            .attr("class", "point")
            .attr("r", 2)
            .attr("cx", xMap)
            .attr("cy", yMap)
            .style("fill", col)
            .on("mouseover", function(d) {
                tooltip
                    .transition()
                    .duration(100)
                    .style("opacity", 1);
                tooltip
                    .html(
                        "<strong>" +
                        sampleID +
                        "</strong><br />Samples: <strong>" +
                        d.h +
                        "</strong><br />Number of OTUs: <strong>" +
                        d.v +
                        "</strong><br />Label: <strong>" +
                        colorMeta +
                        "</strong>"
                    )
                    .style("left", d3.event.pageX - 128 + "px")
                    .style("top", d3.event.pageY + 12 + "px");
            })
            .on("mouseout", function(d) {
                tooltip
                    .transition()
                    .duration(100)
                    .style("opacity", 0);
            });
    });

    if ($("#colorvar").length > 0 && $("#colorvar").val() != "" && $("#colorvar").val() != "None") {
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
            .attr("x", width + 18)
            .attr("width", 18)
            .attr("height", 18)
            .style("fill", color);

        // draw legend text
        legend
            .append("text")
            .attr("x", width + 40)
            .attr("y", 9)
            .attr("dy", ".35em")
            .text(function(d) {
                return d;
            });
    }
}

function checkSubsampleWarning() {
    var data = {
        pid: $("#project").val()
    };

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/isSubsampled" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            if (result == 1) {
                $("#already-subsampled").show();
            }
        },
        error: function(err) {
            console.log(err);
        }
    });
}

function updateAnalysis() {
    showLoading(expectedLoadFactor);

    var colorvar = $("#colorvar").val();
    var data = {
        pid: $("#project").val(),
        colorvar: colorvar
        //"subsamplestep": $("#subsamplestep").val()
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/rarefaction" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            loadSuccess();
            abundancesObj = JSON.parse(result);
            renderRarefactionCurves(abundancesObj);
        },
        error: function(err) {
            loadError();
            console.log(err);
        }
    });

    //    var results = {"results": [{"headers": [1.0, 25479.0, 50957.0, 76435.0, 101913.0, 127391.0, 152869.0, 178347.0, 203825.0, 229303.0, 232449.0], "vals": [1.0, 3774.18, 5167.12, 6120.94, 6854.84, 7451.93, 7954.0, 8385.3, 8761.36, 9092.77, 9131.0]}, {"headers": [1.0, 25479.0, 50957.0, 71148.0], "vals": [1.0, 4419.76, 5967.43, 6794.0]}, {"headers": [1.0, 25479.0, 50957.0, 65463.0], "vals": [1.0, 3853.37, 5259.76, 5825.0]}, {"headers": [1.0, 25479.0, 50957.0, 76435.0, 101913.0, 127391.0, 152869.0, 178347.0, 203825.0, 229303.0, 254781.0, 254782.0], "vals": [1.0, 4397.77, 6521.12, 8024.71, 9195.15, 10151.16, 10955.34, 11645.42, 12246.27, 12775.24, 13244.98, 13245.0]}, {"headers": [1.0, 23919.0], "vals": [1.0, 2178.0]}, {"headers": [1.0, 3192.0], "vals": [1.0, 1186.0]}], "maxHeader": 254782.0, "maxVal": 13245.0}
    //    renderRarefactionCurves(results)
}

function customCatVarCallback(result) {
    var allHeaders = ["None"].concat(result.map(function(obj) { return obj.name; }));

    //
    // Renders the experimental variable
    //
    $("#colorvar").empty();
    allHeaders.forEach(function(obj) {
        $("#colorvar").append(
            '<option value="' + obj + '">' + obj + "</option>"
        );
    });
    if (initialColorVar) {
        $("#colorvar").val(initialColorVar);
        initialColorVar = null;
    }
}
