// ============================================================
// Boxplot JS Component
// ============================================================
var tagsInput;
var abundancesObj = {};

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
    $('#corrvar2 option:eq(1)').attr('selected', 'selected');

    $("#corrvar1").change(function() {
        showTaxLevelIfNeeded($("#corrvar1").val());
        if ($("#corrvar1").val() === "mian-taxonomy-abundance") {
            $("#specific-taxonomy-container-1").show();
            $("#taxonomic-level-container").show();
            $.when(loadOTUTableHeaders("corrvar1")).done(function() {
                updateAnalysis();
            });
        } else {
            $("#specific-taxonomy-container-1").hide();
            updateAnalysis();
        }
    });

    $("#corrvar2").change(function() {
        showTaxLevelIfNeeded($("#corrvar2").val());
        if ($("#corrvar2").val() === "mian-taxonomy-abundance") {
            $("#specific-taxonomy-container-2").show();
            $("#taxonomic-level-container").show();
            $.when(loadOTUTableHeaders("corrvar2")).done(function() {
                updateAnalysis();
            });
        } else {
            $("#specific-taxonomy-container-1").hide();
            updateAnalysis();
        }
    });

    $("#colorvar").change(function() {
        showTaxLevelIfNeeded($("#colorvar").val());
        updateAnalysis();
    });

    $("#sizevar").change(function() {
        showTaxLevelIfNeeded($("#sizevar").val());
        updateAnalysis();
    });

    $("#samplestoshow").change(function() {
        updateAnalysis();
    });

    $("#specific-taxonomy-typeahead-1").change(function() {
        updateAnalysis();
    });

    $("#specific-taxonomy-typeahead-2").change(function() {
        updateAnalysis();
    });

    $("#taxonomy-level").change(function() {
        if (($("#corrvar1").val() === "mian-taxonomy-abundance") || ($("#corrvar2").val() === "mian-taxonomy-abundance")) {
            $.when(loadOTUTableHeaders()).done(function() {
                updateAnalysis();
            });
        } else {
            updateAnalysis();
        }
    });
}


//
// Analysis Specific Methods
//

function customCatVarCallback(json) {
    updateCorrVar(json);
}

function customCatVarValueLoading() {
    return loadOTUTableHeaders();
}

function loadOTUTableHeaders(corrvarType) {
    if ($("#corrvar1").val() === "mian-taxonomy-abundance" || $("#corrvar2").val() === "mian-taxonomy-abundance") {
        $("#specific-taxonomy-typeahead-1").empty();
        $("#specific-taxonomy-typeahead-2").empty();
        var level = taxonomyLevels[$("#taxonomy-level").val()];
        var headersPromise = $.ajax({
            url: "otu_table_headers_at_level?pid=" + $("#project").val() + "&level=" + level,
            success: function(result) {
                var typeAheadSource = JSON.parse(result);
                if (!corrvarType || corrvarType === "corrvar1") {
                    if (tagsInput) {
                        $('#specific-taxonomy-typeahead-1').tagsinput('removeAll');
                        $('#specific-taxonomy-typeahead-1').tagsinput('destroy');
                    }

                    tagsInput = $('#specific-taxonomy-typeahead-1').tagsinput({
                        typeahead: {
                            source: typeAheadSource,
                            afterSelect: () => {
                                $('#specific-taxonomy-typeahead-1').tagsinput('input').val('');
                            }
                        },
                        freeInput: false
                    });
                    $("#taxonomy-specific-typeahead-wrapper-1 .bootstrap-tagsinput").css("width", "320px");
                }
                if (!corrvarType || corrvarType === "corrvar2") {
                    if (tagsInput) {
                        $('#specific-taxonomy-typeahead-2').tagsinput('removeAll');
                        $('#specific-taxonomy-typeahead-2').tagsinput('destroy');
                    }

                    tagsInput = $('#specific-taxonomy-typeahead-2').tagsinput({
                        typeahead: {
                            source: typeAheadSource,
                            afterSelect: () => {
                                $('#specific-taxonomy-typeahead-2').tagsinput('input').val('');
                            }
                        },
                        freeInput: false
                    });
                    $("#taxonomy-specific-typeahead-wrapper-2 .bootstrap-tagsinput").css("width", "320px");
                }

            }
        });
        return headersPromise;
    }
    return null;
}

function showTaxLevelIfNeeded(val) {
    if (val === "mian-taxonomy-abundance" || val === "mian-max" || val === "mian-min" || val === "mian-abundance") {
        $("#taxonomic-level").show();
    } else {
        $("#taxonomic-level").hide();
    }
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

    var margin = {
            top: 20,
            right: 20,
            bottom: 20,
            left: 56
        },
        width = 960 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    // setup x
    var xValue = function(d) {
            return d.c1;
        }, // data -> value
        xScale = d3.scale.linear().range([0, width]), // value -> display
        xMap = function(d) {
            return xScale(xValue(d));
        }, // data -> display
        xAxis = d3.svg.axis().scale(xScale).orient("bottom");

    // setup y
    var yValue = function(d) {
            return d.c2;
        }, // data -> value
        yScale = d3.scale.linear().range([height, 0]), // value -> display
        yMap = function(d) {
            return yScale(yValue(d));
        }, // data -> display
        yAxis = d3.svg.axis().scale(yScale).orient("left");

    // setup fill color
    var cValue = function(d) {
            return d.color;
        },
        color = d3.scale.category10();

    // setup circle size
    var sValue = function(d) {
        return d.size;
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

    // don't want dots overlapping axis, so add in buffer to data domain
    var xBuffer = d3.max(data, xValue) * 0.01;
    var yBuffer = d3.max(data, yValue) * 0.01;
    xScale.domain([d3.min(data, xValue) - xBuffer, d3.max(data, xValue) + xBuffer]);
    yScale.domain([d3.min(data, yValue) - yBuffer, d3.max(data, yValue) + yBuffer]);

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
        .text("Correlation Variable 1");

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
        .text("Correlation Variable 2");

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
        .style("fill", function(d) {
            return color(cValue(d));
        })
        .on("mouseover", function(d) {
            console.log(d);
            tooltip.transition()
                .duration(100)
                .style("opacity", 1);
            tooltip.html("Sample ID: <strong>" + d.s + "</strong><br />" + $("#corrvar1").val() + ": <strong>" + d.c1 + "</strong><br />" + $("#corrvar2").val() + ": <strong>" + d.c2 + "</strong><br />" + ($("#colorvar :selected").text() === "None" ? "" : ($("#colorvar :selected").text() + ": <strong>" + d.color + "</strong><br />")) + ($("#sizevar :selected").text() === "None" ? "" : ($("#sizevar :selected").text() + ": <strong>" + d.size + "</strong>")))
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
            .attr("transform", function(d, i) {
                return "translate(0," + i * 20 + ")";
            });

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
            .text(function(d) {
                return d;
            })
    }
}

function updateAnalysis() {
    showLoading();

    var level = taxonomyLevels[$("#taxonomy-level").val()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var corrvar1 = $("#corrvar1").val();
    var corrvar2 = $("#corrvar2").val();
    var colorvar = $("#colorvar").val();
    var sizevar = $("#sizevar").val();
    var samplestoshow = $("#samplestoshow").val();
    var corrvar1SpecificTaxonomies = $("#specific-taxonomy-typeahead-1").val();
    var corrvar2SpecificTaxonomies = $("#specific-taxonomy-typeahead-2").val();

    if (corrvar1SpecificTaxonomies === "") {
        corrvar1SpecificTaxonomies = JSON.stringify([]);
    } else {
        corrvar1SpecificTaxonomies = JSON.stringify(corrvar1SpecificTaxonomies.split(","));
    }

    if (corrvar2SpecificTaxonomies === "") {
        corrvar2SpecificTaxonomies = JSON.stringify([]);
    } else {
        corrvar2SpecificTaxonomies = JSON.stringify(corrvar2SpecificTaxonomies.split(","));
    }

    var data = {
        "pid": $("#project").val(),
        "taxonomyFilter": taxonomyFilter,
        "taxonomyFilterRole": taxonomyFilterRole,
        "taxonomyFilterVals": taxonomyFilterVals,
        "sampleFilter": sampleFilter,
        "sampleFilterRole": sampleFilterRole,
        "sampleFilterVals": sampleFilterVals,
        "level": level,
        "corrvar1": corrvar1,
        "corrvar2": corrvar2,
        "colorvar": colorvar,
        "sizevar": sizevar,
        "samplestoshow": samplestoshow,
        "corrvar1SpecificTaxonomies": corrvar1SpecificTaxonomies,
        "corrvar2SpecificTaxonomies": corrvar2SpecificTaxonomies,
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
            console.log(err);
        }
    });
}

function updateCorrVar(result) {
    var allHeaders = ["None", ...result.map(obj => obj.name)];
    var numericHeaders = ["None", ...result.filter(obj => obj.type === "numeric").map(obj => obj.name)];
    var categoricalHeaders = ["None", ...result.filter(obj => obj.type === "categorical").map(obj => obj.name)];

    addCorrGroup("mian-none", "None Selected");

    $("#corrvar1").empty();
    $("#corrvar2").empty();
    $("#sizevar").empty();
    $("#colorvar").empty();

    addCorrOption("corrvar1", "mian-taxonomy-abundance", "Taxonomy Abundance");
    addCorrOption("corrvar2", "mian-taxonomy-abundance", "Taxonomy Abundance");

    for (var i = 0; i < numericHeaders.length; i++) {
        if (i != 0) {
            addCorrOption("corrvar1", numericHeaders[i], numericHeaders[i]);
            addCorrOption("corrvar2", numericHeaders[i], numericHeaders[i]);
        }
        addCorrOption("sizevar", numericHeaders[i], numericHeaders[i]); // Optional field so includes the "None"
    }

    for (var i = 0; i < allHeaders.length; i++) {
        addCorrOption("colorvar", allHeaders[i], allHeaders[i]);
    }

    addCorrGroup("mian-abundance", "Aggregate Abundance");
    addCorrGroup("mian-max", "Max Abundance");

    // Make sure the second option is selected if possible
    // $('#corrvar2 option:eq(1)').attr('selected', 'selected');
}

function addCorrGroup(val, text) {
    addCorrOption("corrvar1", val, text);
    addCorrOption("corrvar2", val, text);
    addCorrOption("sizevar", val, text);
    addCorrOption("colorvar", val, text);
}

function addCorrOption(elemID, val, text) {
    var o = document.createElement("option");
    o.setAttribute("value", val);
    var t = document.createTextNode(text);
    if (val == "Abundances") {
        t = document.createTextNode("Aggregate Abundances");
    }
    o.appendChild(t);
    document.getElementById(elemID).appendChild(o);
}