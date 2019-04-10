// ============================================================
// Scatterplot JS Shared Component
// ============================================================

function renderCorrelations(abundancesObj, xAxisText, yAxisText) {
    if ($.isEmptyObject(abundancesObj)) {
        return;
    }

    var data = abundancesObj["corrArr"];

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
        xScale = d3.scaleLinear().range([0, width]), // value -> display
        xMap = function(d) {
            return xScale(xValue(d));
        }, // data -> display
        xAxis = d3.axisBottom(xScale);

    // setup y
    var yValue = function(d) {
            return d.c2;
        }, // data -> value
        yScale = d3.scaleLinear().range([height, 0]), // value -> display
        yMap = function(d) {
            return yScale(yValue(d));
        }, // data -> display
        yAxis = d3.axisLeft(yScale);

    // setup fill color
    var cValue = function(d) {
            return d.color;
        },
        color = d3.scaleOrdinal(d3.schemeCategory10);

    // setup circle size
    var sValue = function(d) {
        return d.size;
    };
    var minSValue = d3.min(data, sValue);
    var maxSValue = d3.max(data, sValue);
    var sScale = d3.scaleLinear()
        .domain([minSValue, maxSValue])
        .range([2, 8]);

    // add the graph canvas to the body of the webpage
    var svgBase = d3
        .select("#analysis-container")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);

    var zoom = d3.zoom()
        .on("zoom", zoomFunction);

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

    // don't want dots overlapping axis, so add in buffer to data domain
    var xBuffer = d3.max(data, xValue) * 0.01;
    var yBuffer = d3.max(data, yValue) * 0.01;
    xScale.domain([
        d3.min(data, xValue) - xBuffer,
        d3.max(data, xValue) + xBuffer
    ]);
    yScale.domain([
        d3.min(data, yValue) - yBuffer,
        d3.max(data, yValue) + yBuffer
    ]);

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
    gX.append("text")
        .attr("x", width)
        .attr("y", -6)
        .style("text-anchor", "end")
        .style("fill", "#999")
        .text(xAxisText);

    // y-axis
    var gY = svg
        .append("g")
        .attr("class", "y axis")
        .call(yAxis);
    gY.append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .style("fill", "#999")
        .text(yAxisText);

    // draw dots
    var dots = svg
        .selectAll(".dot")
        .data(data)
        .enter()
        .append("circle")
        .attr("class", "dot")
        .attr("r", function(d) {
            if ($("#sizevar").length > 0 && $("#sizevar").val() != "" && $("#sizevar").val() != "None") {
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
            tooltip
                .transition()
                .duration(100)
                .style("opacity", 1);
            tooltip
                .html(
                    "Sample ID: <strong>" +
                    d.s +
                    "</strong><br />" +
                    xAxisText +
                    ": <strong>" +
                    d.c1 +
                    "</strong><br />" +
                    yAxisText +
                    ": <strong>" +
                    d.c2 +
                    "</strong><br />" +
                    ($("#colorvar").length === 0 || $("#colorvar :selected").text() === "None" ?
                        "" :
                        $("#colorvar :selected").text() +
                        ": <strong>" +
                        d.color +
                        "</strong><br />") +
                    ($("#sizevar").length === 0 || $("#sizevar :selected").text() === "None" ?
                        "" :
                        $("#sizevar :selected").text() +
                        ": <strong>" +
                        d.size +
                        "</strong>")
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

        dots.attr("r", function(d) {
            if ($("#sizevar").length > 0 && $("#sizevar").val() != "" && $("#sizevar").val() != "None") {
                return sScale(sValue(d)) / d3.event.transform.k;
            } else {
                return 3 / d3.event.transform.k;
            }
        })
        dots.attr("transform", d3.event.transform);
    };
}

function renderCorrelationsTable(abundancesObj) {
    var coef = abundancesObj["coef"];
    var pValue = abundancesObj["pval"];

    $("#stats-container").hide();
    $("#stats-container-scatterplot").show();
    $("#stats-coef").text(coef);
    $("#stats-pval").text(pValue);
}
