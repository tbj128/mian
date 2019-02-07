$(document).ready(function() {
    // Global variables storing the data
    var otuTableData = [];
    var otuTableDataRow = {};
    var otuTableDataCol = {};

    var otuTaxonomyMappingData = [];
    var otuTaxonomyMappingRow = {};
    var otuTaxonomyMappingCol = {};

    var sampleIDMappingData = [];
    var sampleIDMappingRow = {};
    var sampleIDMappingCol = {};

    // TODO: IS THIS STILL USED?

    // Event listeners to switch tabs
    $("#upload-biom-tab").click(function() {
        $(this)
            .removeClass("btn-primary")
            .addClass("btn-default");
        $("#upload-otu-tab")
            .removeClass("btn-primary")
            .addClass("btn-default");
        $("#otu-upload-container").fadeOut(10);
        $("#biom-upload-container").fadeIn(10);
        $("#projectUploadType").val("biom");
    });
    $("#upload-otu-tab").click(function() {
        $(this)
            .removeClass("btn-primary")
            .addClass("btn-default");
        $("#upload-biom-tab")
            .removeClass("btn-primary")
            .addClass("btn-default");
        $("#otu-upload-container").fadeIn(10);
        $("#biom-upload-container").fadeOut(10);
        $("#projectUploadType").val("otu");
    });

    // The event listener for the file upload
    document
        .getElementById("biomInput")
        .addEventListener("change", uploadBiom, false);
    document
        .getElementById("otuTable")
        .addEventListener("change", uploadOTUTable, false);
    document
        .getElementById("otuTaxonomyMapping")
        .addEventListener("change", uploadTaxonomyMapping, false);
    document
        .getElementById("otuMetadata")
        .addEventListener("change", uploadMetadata, false);

    function uploadBiom() {
        upload("biomForm");
    }

    function uploadOTUTable() {
        upload("otuTableForm");
    }

    function uploadTaxonomyMapping() {
        upload("otuTaxonomyMappingForm");
    }

    function uploadMetadata() {
        upload("otuMetadataForm");
    }

    function processOTUTable(data) {
        var d = [];
        for (var i = 0; i < data.length; i++) {
            if (i == 0) {
                for (var j = 0; j < data[i].length; j++) {
                    otuTableDataCol[j] = data[i][j];
                }
            } else {
                otuTableDataRow[data[i][1]] = i;
                d.push(data[i]);
            }
        }
        otuTableData = d;
    }

    function processOTUTaxonomyMapping(rawotuTaxonomyMappingData) {
        var tax = [
            "Kingdom",
            "Phylum",
            "Class",
            "Order",
            "Family",
            "Genus",
            "Species"
        ];
        var d = [];
        for (var i = 0; i < rawotuTaxonomyMappingData.length; i++) {
            if (i == 0) {
                var fullTax = rawotuTaxonomyMappingData[i + 1][2];
                var fullTaxArr = fullTax.split(";");
                for (var j = 0; j < fullTaxArr.length; j++) {
                    otuTaxonomyMappingCol[tax[j]] = j + 2;
                }
            } else {
                fullTax = rawotuTaxonomyMappingData[i][2];
                fullTaxArr = fullTax.split(";");
                newArr = [];
                newArr.push(rawotuTaxonomyMappingData[i][0]);
                newArr.push(rawotuTaxonomyMappingData[i][1]);
                otuTaxonomyMappingRow[i] = rawotuTaxonomyMappingData[i][0];
                for (var j = 0; j < fullTaxArr.length; j++) {
                    if (fullTaxArr[j] != "") {
                        newArr.push(fullTaxArr[j]);
                    }
                }
                d.push(newArr);
            }
        }
        otuTaxonomyMappingData = d;
    }

    function processSampleIDMapping(data) {
        var d = [];
        for (var i = 0; i < data.length; i++) {
            if (i == 0) {
                for (var j = 0; j < data[i].length; j++) {
                    sampleIDMappingCol[data[i][j]] = j;
                }
            } else {
                sampleIDMappingRow[data[i][0]] = i - 1;
                d.push(data[i]);
            }
        }
        sampleIDMappingData = d;
    }

    // Catch the form submit and upload the files
    function upload(formID) {
        var form = $("#" + formID)[0]; // You need to use standard javascript object here
        var formData = new FormData(form);

        $.ajax({
            url: "/upload",
            type: "POST",
            data: formData,
            cache: false,
            processData: false, // Don't process the files
            contentType: false, // Set content type to false as jQuery will tell the server its a query string request
            success: function(data, textStatus, jqXHR) {
                console.log("Success");
                if (formID == "biomForm") {
                    $("#biomOK").show();
                    $("#biomText").text("Replace");
                }
                if (formID == "otuTableForm") {
                    $("#otuTableOK").show();
                    $("#otuTableText").text("Replace");
                }
                if (formID == "otuTaxonomyMappingForm") {
                    $("#otuTaxonomyMappingOK").show();
                    $("#otuTaxonomyMappingText").text("Replace");
                }
                if (formID == "otuMetadataForm") {
                    $("#otuMetadataOK").show();
                    $("#otuMetadataText").text("Replace");
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log("Error: " + textStatus);
                alert("An error occurred");
            }
        });
    }

    function createListeners() {
        $("#taxonomy").change(function() {
            updateTaxonomicLevel(false);
        });

        $("#taxonomy-specific").change(function() {
            updateAnalysis();
        });

        $("#corrvar").change(function() {
            updateAnalysis();
        });

        $("#colorvar").change(function() {
            updateAnalysis();
        });

        $("#sizevar").change(function() {
            updateAnalysis();
        });
    }

    function updateTaxonomicLevel(firstLoad) {
        var level = getTaxonomicLevel();
        var taxLevelCol = otuTaxonomyMappingCol[level];
        var taxonomies = {};
        for (var i = 0; i < otuTaxonomyMappingData.length; i++) {
            taxonomies[otuTaxonomyMappingData[i][taxLevelCol]] = 1;
        }

        $("#taxonomy-specific").empty();
        var keys = Object.keys(taxonomies);
        for (var i = 0; i < keys.length; i++) {
            $("#taxonomy-specific").append(
                '<option value="' + keys[i] + '">' + keys[i] + "</option>"
            );
        }
        if (firstLoad) {
            var outWidth = $("#project").outerWidth();
            $("#taxonomy-specific").multiselect({
                buttonWidth: outWidth ? outWidth + "px" : "320px",
                enableFiltering: true,
                //filterBehavior: 'value',
                maxHeight: 400
            });
        } else {
            $("#taxonomy-specific").multiselect("rebuild");
        }
        updateAnalysis();
    }

    function getTaxonomicLevel() {
        return $("#taxonomy").val();
    }

    function updateAnalysis() {
        var level = getTaxonomicLevel();
        var taxonomy = $("#taxonomy-specific").val();
        var corrvar = $("#corrvar").val();
        var colorvar = $("#colorvar").val();
        var sizevar = $("#sizevar").val();

        if (
            taxonomy == null ||
            corrvar == null ||
            taxonomy == "" ||
            corrvar == ""
        ) {
            return;
        }

        // TODO: Multiple taxonomies (comma separated)
        // Get all OTUs with taxonomy level and taxonomy
        var taxLevelCol = otuTaxonomyMappingCol[level];
        var relevantOTUs = {};
        for (var i = 0; i < otuTaxonomyMappingData.length; i++) {
            if (otuTaxonomyMappingData[i][taxLevelCol] == taxonomy) {
                relevantOTUs[otuTaxonomyMappingData[i][0]] = 1;
            }
        }

        result = [];
        // Sum across relevant OTUs for each sample
        for (var i = 0; i < otuTableData.length; i++) {
            var otuReadCount = 0;
            for (var j = 0; j < otuTableData[i].length; j++) {
                var otu = otuTableDataCol[j];
                if (relevantOTUs.hasOwnProperty(otu)) {
                    otuReadCount = otuReadCount + parseFloat(otuTableData[i][j]);
                }
            }

            resultObj = {};
            resultObj["reads"] = otuReadCount;

            var sampleMetadataRow = sampleIDMappingRow[otuTableData[i][1]];
            var corrVarCol = sampleIDMappingCol[corrvar];
            var corrVarVal = sampleIDMappingData[sampleMetadataRow][corrVarCol];
            resultObj["corrvar"] = parseFloat(corrVarVal);

            if (colorvar != "" && colorvar != "None") {
                var colorCol = sampleIDMappingCol[colorvar];
                var colorVal = sampleIDMappingData[sampleMetadataRow][colorCol];
                resultObj["color"] = colorVal;
            }

            if (sizevar != "" && sizevar != "None") {
                var sizeCol = sampleIDMappingCol[sizevar];
                var sizeVal = sampleIDMappingData[sampleMetadataRow][sizeCol];
                resultObj["size"] = parseFloat(sizeVal);
            }

            result.push(resultObj);
        }

        plotCorrelation(result);
    }

    function plotCorrelation(data) {
        $("#analysis-container").empty();

        var margin = {
                top: 20,
                right: 20,
                bottom: 30,
                left: 40
            },
            width = 960 - margin.left - margin.right,
            height = 500 - margin.top - margin.bottom;

        // setup x
        var xValue = function(d) {
                return d.corrvar;
            }, // data -> value
            xScale = d3.scale.linear().range([0, width]), // value -> display
            xMap = function(d) {
                return xScale(xValue(d));
            }, // data -> display
            xAxis = d3.svg
            .axis()
            .scale(xScale)
            .orient("bottom");

        // setup y
        var yValue = function(d) {
                return d.reads;
            }, // data -> value
            yScale = d3.scale.linear().range([height, 0]), // value -> display
            yMap = function(d) {
                return yScale(yValue(d));
            }, // data -> display
            yAxis = d3.svg
            .axis()
            .scale(yScale)
            .orient("left");

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
        var sScale = d3.scale
            .linear()
            .domain([minSValue, maxSValue])
            .range([2, 8]);

        // add the graph canvas to the body of the webpage
        var svg = d3
            .select("#analysis-container")
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        // don't want dots overlapping axis, so add in buffer to data domain
        xScale.domain([
            d3.min(data, xValue) - d3.max(data, xValue) * 0.01,
            d3.max(data, xValue) + d3.max(data, xValue) * 0.01
        ]);
        yScale.domain([
            d3.min(data, yValue) - d3.max(data, yValue) * 0.01,
            d3.max(data, yValue) + d3.max(data, yValue) * 0.01
        ]);

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
            .text($("#corrval").val());

        // y-axis
        svg
            .append("g")
            .attr("class", "y axis")
            .call(yAxis)
            .append("text")
            .attr("class", "label")
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "end")
            .text("Reads");

        // draw dots
        svg
            .selectAll(".dot")
            .data(data)
            .enter()
            .append("circle")
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
    }
});
