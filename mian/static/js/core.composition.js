// ============================================================
// Composition JS Component
// ============================================================

// Global variables storing the data
var uniqueGroupVals = [];
var idMap = {};

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
    if (getParameterByName("plotType") !== null) {
        $("#plotType").val(getParameterByName("plotType"));
    }
    if (getParameterByName("xaxis") !== null) {
        $("#xaxis").val(getParameterByName("xaxis"));
    }
    if (getParameterByName("showlabels") !== null) {
        $("#showlabels").val(getParameterByName("showlabels"));
    }
    if (getParameterByName("colorscheme") !== null) {
        $("#colorscheme").val(getParameterByName("colorscheme"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#catvar").change(function() {
        updateAnalysis();
    });

    $("#plotType").change(function() {
        updateAnalysis();
    });

    $("#showlabels").change(function() {
        updateAnalysis();
    });

    $("#colorscheme").change(function() {
        updateAnalysis();
    });

    $("#xaxis").change(function() {
        updateAnalysis();
    });

    $("#download-svg").click(function() {
        downloadSVG("composition." + $("#catvar").val());
    });
}

//
// Analysis Specific Methods
//
function customCatVarCallback() {
    $('#catvar option:first').after("<option value='SampleID'>Sample ID</option>");
    if ($("#plotType").val() === "heatmap") {
        $("#catvar").val("SampleID");
    }
}

function getTaxonomicLevel() {
    return $("#taxonomy").val();
}

function updateAnalysis() {
    showLoading();
    $("#stats-container").fadeIn(250);

    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();

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
        plotType: $("#plotType").val(),
        xaxis: $("#xaxis").val()
    };
    if ($("#colorscheme").length) {
        data["colorscheme"] = $("#colorscheme").val();
    }
    if ($("#showlabels").length) {
        data["showlabels"] = $("#showlabels").val();
    }


    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/composition" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            var abundancesObj = JSON.parse(result);
            if ((abundancesObj["abundances"] && abundancesObj["abundances"].length === 0) || (abundancesObj["row_headers"] && abundancesObj["row_headers"].length === 0)) {
                loadNoResults();
            } else {
                loadSuccess();
                if ($("#plotType").val() === "stackedbar") {
                    renderStackedBarplot(abundancesObj);
                } else if ($("#plotType").val() === "heatmap") {
                    renderHeatmap(abundancesObj, abundancesObj["min"], abundancesObj["max"]);
                } else {
                    renderDonut(abundancesObj);
                }
            }
        },
        error: function(err) {
            loadError();
            console.log(err);
        }
    });
}


function renderStackedBarplot(abundancesObj) {
    $("#analysis-container").empty();

    var data = abundancesObj["abundances"];
    uniqueGroupVals = abundancesObj["uniqueVals"].map(tuple => tuple[0]);
    idMap = abundancesObj["idMap"];

    var uniqueTaxas = data.map(function(d) {
        return d.t;
    });
    var uniqueTaxasForLabels = data.map(function(d) {
        var dArr = d.t.split(";");
        return dArr[dArr.length - 1];
    });

    var margin = {
            top: 20,
            right: 20,
            bottom: 160,
            left: 56
        },
        legendMargin = 80,
        legendWidth = 160,
        width = 20 * uniqueTaxas.length,
        height = 500 - margin.top - margin.bottom,
        barWidth = 12;

    var xScaleTax = d3.scale
        .ordinal()
        .domain(uniqueTaxas)
        .rangeRoundBands([0, width], 0),
        xScaleCatvar = d3.scale.ordinal(),
        xAxis = d3.svg
        .axis()
        .scale(xScaleTax)
        .orient("bottom");

    // We don't want the labels to display the fully quantified version of the taxonomic group
    var xScaleTaxForLabels = d3.scale
        .ordinal()
        .domain(uniqueTaxasForLabels)
        .rangeRoundBands([0, width]),
        xAxisForLabels = d3.svg
        .axis()
        .scale(xScaleTaxForLabels)
        .orient("bottom");
    xScaleCatvar
        .domain(uniqueGroupVals)
        .rangeRoundBands([0, xScaleTax.rangeBand()]);

    data.forEach(function(d) {
        var sumSoFar = 0;
        d.cv = uniqueGroupVals.map(function(name, i) {
            var val = d.o.hasOwnProperty(name) ? +d.o[name] : 0;
            var obj = {
                name: name,
                offset: sumSoFar,
                value: val
            };
            sumSoFar += val;
            return obj;
        });
    });

    var yScale = d3.scale.linear().range([height, 0]),
        yAxis = d3.svg
        .axis()
        .scale(yScale)
        .orient("left");
    yScale.domain([
        0,
        d3.max(data, function(d) {
            var sum = 0;
            d.cv.forEach(cv => {
                sum += cv.value;
            });
            return sum;
        })
    ]);

    var color = d3.scale.category20();

    // add the graph canvas to the body of the webpage
    var svg = d3
        .select("#analysis-container")
        .append("svg")
        .attr("width", legendMargin + legendWidth + width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var tooltip = d3
        .select("#analysis-container")
        .append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);

    svg
        .append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxisForLabels)
        .selectAll("text")
        .attr("x", -9)
        .attr("y", -4)
        .attr("transform", "rotate(-90)")
        .style("text-anchor", "end");

    svg
        .append("g")
        .attr("class", "y axis")
        .call(yAxis);

    var tax = svg
        .selectAll(".tax")
        .data(data)
        .enter()
        .append("g")
        .attr("class", "tax")
        .attr("transform", function(d) {
            return "translate(" + xScaleTax(d.t) + ",0)";
        });

    tax
        .selectAll("rect")
        .data(function(d) {
            return d.cv;
        })
        .enter()
        .append("rect")
        .attr("width", barWidth)
        .attr("x", function(d) {
            return xScaleTax.rangeBand() / 2 - barWidth / 2;
        })
        .attr("y", function(d, i) {
            return yScale(d.offset + d.value);
        })
        .attr("height", function(d) {
            return height - yScale(d.value);
        })
        .style("fill", function(d) {
            return color(idMap[d.name]);
        })
        .attr("class", "bar")
        .on("mouseover", function(d) {
            var meta = idMap[d.name];
            tooltip
                .transition()
                .duration(100)
                .style("opacity", 1);
            tooltip
                .html(
                    "<strong>" +
                    idMap[d.name] +
                    "</strong><br />Average Relative Abundance: <strong>" +
                    d.value +
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

    var legend = svg
        .selectAll(".legend")
        .data(uniqueGroupVals.slice(0, 10).map(v => idMap[v]))
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

    svg
        .append("text")
        .attr("x", width + legendMargin)
        .attr("y", -6)
        .style("text-anchor", "start")
        .style("font-weight", "bold")
        .text("Top 10 Colors:");
}

function renderDonut(abundancesObj) {
    $("#analysis-container").empty();

    var data = abundancesObj["abundances"];
    uniqueGroupVals = abundancesObj["uniqueVals"].map(tuple => tuple[0]);
    idMap = abundancesObj["idMap"];

    var uniqueSubGroupVals = data.map(function(d) {
        return d.t;
    });

    var containerWidth = 800;
    var legendMargin = 60;
    var legendWidth = 180;
    var donutDiameter = 200;
    var donutsPerRow = containerWidth / donutDiameter;
    var color = d3.scale.category20();
    var legendOffset = uniqueGroupVals.length > donutsPerRow ? containerWidth : uniqueGroupVals.length * donutDiameter;


    var svgBase = d3
        .select("#analysis-container")
        .append("svg")
        .attr("width", (containerWidth + legendMargin + legendWidth))
        .attr("height", (Math.ceil(uniqueGroupVals.length / donutsPerRow) * donutDiameter));

    var legend = svgBase
        .selectAll(".legend")
        .data(uniqueSubGroupVals.slice(0, 10))
        .enter()
        .append("g")
        .attr("class", "legend")
        .attr("transform", function(d, i) {
            return "translate(0," + (20 + i * 20) + ")";
        });

    legend
        .append("rect")
        .attr("x", legendOffset + legendMargin)
        .attr("width", 18)
        .attr("height", 18)
        .style("fill", color);

    legend
        .append("text")
        .attr("x", legendOffset + legendMargin + 24)
        .attr("y", 9)
        .attr("dy", ".35em")
        .text(function(d) {
            return d;
        });

    svgBase
        .append("text")
        .attr("x", legendOffset + legendMargin)
        .attr("y", 12)
        .style("text-anchor", "start")
        .style("font-weight", "bold")
        .text("Top 10 Colors:");

    uniqueGroupVals.forEach(function(cat, index) {
        var radius = donutDiameter / 2;
        var val = idMap[cat];
        var valArr = val.split(";");
        var varTrim = valArr[valArr.length - 1];

        var arc = d3.svg
            .arc()
            .outerRadius(radius - 10)
            .innerRadius(radius - 30);

        var pie = d3.layout
            .pie()
            .sort(null)
            .value(function(d) {
                return d.o[cat];
            });

        var svg = svgBase
            .append("g")
            .attr("transform", "translate(" + ((index % donutsPerRow) * donutDiameter + radius) + "," + (Math.floor(index / donutsPerRow) * donutDiameter + radius) + ")");

        svg
            .append("text")
            .attr("dy", ".35em")
            .attr("class", "donut-header")
            .attr("text-anchor", "middle")
            .text(varTrim)
            .style("font-size", "11px");

        var tooltip = d3
            .select("#analysis-container")
            .append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);

        var g = svg
            .selectAll(".arc")
            .data(pie(data))
            .enter()
            .append("g")
            .attr("class", "arc");

        g
            .append("path")
            .attr("d", arc)
            .style("fill", function(d) {
                return color(d.data.t);
            })
            .on("mouseover", function(d) {
                tooltip
                    .transition()
                    .duration(100)
                    .style("opacity", 1);
                tooltip
                    .html(
                        "<strong>" +
                        d.data.t +
                        "</strong><br />" +
                        val +
                        "<br />Average Relative Abundance: <strong>" +
                        d.value +
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

        // Uncomment to display text on the pie segments
//        g
//            .append("text")
//            .attr("transform", function(d) {
//                return "translate(" + arc.centroid(d) + ")";
//            })
//            .attr("dy", ".35em")
//            .attr("text-anchor", "middle")
//            .attr("fill", "#333")
//            .text(function(d) {
//                if (d.data.o[cat] >= 0.05) {
//                    var dArr = d.data.t.split(";");
//                    return dArr[dArr.length - 1];
//                }
//            });
    });
}

