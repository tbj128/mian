// ============================================================
// Boxplot JS Shared Component
// ============================================================
function renderBoxplots(abundancesObj, xAxisText, yAxisText) {
    $("#analysis-container").empty();

    var dataObj = abundancesObj["abundances"];

    var categories = [];
    var minVal = null;
    var maxVal = 0;
    $.each(dataObj, function(k, v) {
        categories.push(k);
        for (var i = 0; i < dataObj[k].length; i++) {
            if (dataObj[k][i]["a"] > maxVal) {
                maxVal = dataObj[k][i]["a"];
            }
            if (minVal === null || minVal > dataObj[k][i]["a"]) {
                minVal = dataObj[k][i]["a"];
            }
        }
    });

    if (maxVal == 0) {
        maxVal = 1;
    }

    // Initialize the dimensions
    var boxplotWidth = 128;
    var margin = {
            top: 36,
            right: ($("#colorvar").length > 0 && $("#colorvar").val() != "" && $("#colorvar").val() != "None") ? 180 : 36,
            bottom: 36,
            left: 72
        },
        padding = 48,
        width = (boxplotWidth + padding * 2) * categories.length,
        height = 520 - margin.top - margin.bottom;

    // Initialize the y axis scale
    var yScale = d3.scaleLinear().range([height + margin.top, 0 + margin.top]);
    var pad = (maxVal - minVal) * 0.3;
    yScale.domain([minVal - pad, maxVal + pad]);

    // Initialize the x axis scale
    var xScale = d3.scaleBand()
        .domain(categories)
        .rangeRound([0, width]);

    // Initialize the y axis
    var yAxis = d3.axisLeft(yScale);

    // Initialize the x axis
    var xAxis = d3.axisBottom(xScale);

    // Append the axis onto the figure
    var svgContainer = d3
        .select("#analysis-container")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);

    svgContainer
        .append("g")
        .attr("class", "box")
        .attr("transform", "translate(0, 0)");

    svgContainer
        .append("g")
        .attr("class", "axis")
        .attr("transform", "translate(" + margin.left + ", 0)")
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
        .text(yAxisText);

    svgContainer
        .append("g")
        .attr("class", "axis")
        .attr(
            "transform",
            "translate(" + margin.left + ", " + (height + margin.top + 10) + ")"
        )
        .call(xAxis)
        .append("text")
        .attr("class", "label")
        .attr("x", width)
        .attr("y", -6)
        .style("text-anchor", "end")
        .style("fill", "#333")
        .style("font-weight", "300")
        .style("font-size", "11px")
        .text(xAxisText);

    var svg = svgContainer.selectAll(".box");
    var color = d3.scaleOrdinal(d3.schemeCategory20);

    for (var i = 0; i < categories.length; i++) {
        var dataCat = dataObj[categories[i]];
        if (dataCat.length == 0) {
            continue;
        }

        // Calculate offset of this particular boxplot
        var midline =
            margin.left +
            (boxplotWidth + 2 * padding) / 2 +
            i * (boxplotWidth + 2 * padding);

        // Initialize each boxplot
        var data = [],
            outliers = [],
            minVal = Infinity,
            lowerWhisker = Infinity,
            q1Val = Infinity,
            medianVal = 0,
            q3Val = -Infinity,
            iqr = 0,
            upperWhisker = -Infinity,
            maxVal = -Infinity;

        data = dataCat.map(function(d) {
            return d.a;
        });

        data = data.sort(d3.ascending);

        //calculate the boxplot statistics
        (minVal = data[0]),
        (q1Val = d3.quantile(data, 0.25)),
        (medianVal = d3.quantile(data, 0.5)),
        (q3Val = d3.quantile(data, 0.75)),
        (iqr = q3Val - q1Val),
        (maxVal = data[data.length - 1]);
        // lowerWhisker = d3.max([minVal, q1Val - iqr])
        // upperWhisker = d3.min([maxVal, q3Val + iqr]);

        var index = 0;

        //search for the lower whisker, the mininmum value within q1Val - 1.5*iqr
        while (index < data.length && lowerWhisker == Infinity) {
            if (data[index] >= q1Val - 1.5 * iqr) lowerWhisker = data[index];
            else outliers.push(data[index]);
            index++;
        }

        index = data.length - 1; // reset index to end of array

        //search for the upper whisker, the maximum value within q1Val + 1.5*iqr
        while (index >= 0 && upperWhisker == -Infinity) {
            if (data[index] <= q3Val + 1.5 * iqr) upperWhisker = data[index];
            else outliers.push(data[index]);
            index--;
        }

        //draw verical line for lowerWhisker
        svg
            .append("line")
            .attr("class", "whisker")
            .attr("y1", yScale(lowerWhisker))
            .attr("y2", yScale(lowerWhisker))
            .attr("stroke", "black")
            .attr("x1", midline - boxplotWidth / 2)
            .attr("x2", midline + boxplotWidth / 2);

        //draw vertical line for upperWhisker
        svg
            .append("line")
            .attr("class", "whisker")
            .attr("y1", yScale(upperWhisker))
            .attr("y2", yScale(upperWhisker))
            .attr("stroke", "black")
            .attr("x1", midline - boxplotWidth / 2)
            .attr("x2", midline + boxplotWidth / 2);

        //draw horizontal line from lowerWhisker to upperWhisker
        svg
            .append("line")
            .attr("class", "whisker")
            .attr("y1", yScale(lowerWhisker))
            .attr("y2", yScale(upperWhisker))
            .attr("stroke", "black")
            .attr("x1", midline)
            .attr("x2", midline);

        //draw rect for iqr
        svg
            .append("rect")
            .attr("class", "box")
            .attr("stroke", "black")
            .attr("fill", "white")
            .attr("y", yScale(q3Val))
            .attr("x", midline - boxplotWidth / 2)
            .attr("height", yScale(q1Val) - yScale(q3Val))
            .attr("width", boxplotWidth);

        //draw vertical line at median
        svg
            .append("line")
            .attr("class", "median")
            .attr("stroke", "black")
            .attr("y1", yScale(medianVal))
            .attr("y2", yScale(medianVal))
            .attr("x1", midline - boxplotWidth / 2)
            .attr("x2", midline + boxplotWidth / 2);

        // tooltip that appears when hovering over a dot
        var tooltip = d3
            .select("#analysis-container")
            .append("div")
            .attr("class", "tooltip")
            .style("opacity", 0)
            .style("width", "160px");

        // Draw data as points
        svg
            .selectAll("circle.new")
            .data(dataCat)
            .enter()
            .append("circle")
            .attr("r", 2.5)
            .attr("class", function(d) {
                if (d.a < lowerWhisker || d.a > upperWhisker) return "dot outlier";
                else return "dot point";
            })
            .attr("cx", function() {
                return random_jitter(midline);
            })
            .attr("cy", function(d) {
                return yScale(d.a);
            })
            .style("fill", function(d) {
                if (!d.hasOwnProperty("color") || d.color === "") {
                    return "#242C70";
                } else {
                    return color(d.color);
                }
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
                        "</strong><br />Value: <strong>" +
                        d.a +
                        "</strong><br />"
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

        function random_jitter(m) {
            if (Math.round(Math.random() * 1) == 0) var seed = -10;
            else var seed = 10;
            return m + Math.floor(Math.random() * seed + 1);
        }
    }

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
            .attr("x", (margin.left + width + 28))
            .attr("width", 18)
            .attr("height", 18)
            .style("fill", color);

        // draw legend text
        legend
            .append("text")
            .attr("x", (margin.left + width + 52))
            .attr("y", 9)
            .attr("dy", ".35em")
            .text(function(d) {
                return d;
            });
    }
}
