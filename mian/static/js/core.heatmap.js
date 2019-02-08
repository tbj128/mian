// ============================================================
// Heatmap JS Component
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
    if (getParameterByName("corrvar1") !== null) {
        $("#corrvar1").val(getParameterByName("corrvar1"));
    }
    if (getParameterByName("corrvar2") !== null) {
        $("#corrvar2").val(getParameterByName("corrvar2"));
    }
    if (getParameterByName("cluster") !== null) {
        $("#cluster").val(getParameterByName("cluster"));
    }
    if (getParameterByName("minSamplesPresent") !== null) {
        $("#minSamplesPresent").val(getParameterByName("minSamplesPresent"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#corrvar1").change(function() {
        updateAnalysis();
    });
    $("#corrvar2").change(function() {
        updateAnalysis();
    });
    $("#cluster").change(function() {
        updateAnalysis();
    });
    $("#minSamplesPresent").change(function() {
        updateAnalysis();
    });
}

//
// Analysis Specific Methods
//
function customLoading() {}

function renderHeatmap(abundancesObj) {
    var corrvar1 = $("#corrvar1").val();
    var corrvar2 = $("#corrvar2").val();

    var rowHeaders = abundancesObj["row_headers"];
    var rowHeadersShort = rowHeaders.map(r => {
        var arr = r.split(";");
        return arr[arr.length - 1];
    });
    var colHeaders = abundancesObj["col_headers"];
    var colHeadersShort = colHeaders.map(r => {
        var arr = r.split(";");
        return arr[arr.length - 1];
    });
    var data = abundancesObj["data"];

    var rowColMax = Math.max(rowHeaders.length, colHeaders.length);

    $("#analysis-container").empty();

    var gridSize = Math.max(3, 30 - Math.round(27 * rowColMax / 1000));

    var margin = {
            top: 90,
            right: 60,
            bottom: 120,
            left: 90
        },
        width = gridSize * colHeaders.length,
        height = gridSize * rowHeaders.length;

    var coloursRainbow = ["#2c7bb6", "#00a6ca", "#00ccbc", "#90eb9d", "#ffff8c", "#f9d057", "#f29e2e", "#e76818", "#d7191c"];
    coloursRainbow.reverse();
    var colourRangeRainbow = d3.range(-1, 1, 2.0 / (coloursRainbow.length - 1));
    colourRangeRainbow.push(1);

    var color = d3.scaleLinear()
        .domain(colourRangeRainbow)
        .range(coloursRainbow)
        .interpolate(d3.interpolateHcl);

    var xScale = d3.scaleBand()
        .domain(colHeadersShort)
        .rangeRound([0, width]);
    var yScale = d3.scaleBand()
        .domain(rowHeadersShort)
        .rangeRound([0, height]);

    var xScaleData = d3.scaleLinear()
        .domain([0, colHeaders.length])
        .range([0, width]);
    var yScaleData = d3.scaleLinear()
        .domain([0, rowHeaders.length])
        .range([0, height]);

    var xAxis = d3.axisTop(xScale),
        yAxis = d3.axisLeft(yScale);
    if (gridSize < 8) {
        xAxis = xAxis.tickValues(xScale.domain().filter(function(d,i){ return !(i % 15)}));
        yAxis = yAxis.tickValues(yScale.domain().filter(function(d,i){ return !(i % 15)}));
    }

    // tooltip that appears when hovering over a dot
    var tooltip = d3
        .select("#analysis-container")
        .append("div")
        .attr("class", "tooltip")
        .style("opacity", 0)
        .style("width", "160px");

    var canvas = d3.select('#analysis-container')
        .append("canvas")
        .attr("id", "canvas")
        .attr("width", width)
        .attr("height", height)
        .style("position", 'absolute')
        .style("left", "110px")
        .style("top", "110px")
        .on("mousemove", function(d) {
            var mouseX = d3.event.layerX || d3.event.offsetX;
            var mouseY = d3.event.layerY || d3.event.offsetY;

            var actualX = Math.floor(mouseX / gridSize);
            var actualY = Math.floor(mouseY / gridSize);

            var xElem = colHeaders[actualX];
            var yElem = rowHeaders[actualY];
            var d = 0;
            if (corrvar1 === corrvar2) {
                d = actualX >= actualY ? data[actualY][actualX - actualY] : data[actualX][actualY - actualX];
            } else {
                d = data[actualY][actualX];
            }

            tooltip
                .transition()
                .duration(100)
                .style("opacity", 1);
            tooltip
                .html(
                    "Row: <strong>" + yElem + "</strong><br />" +
                    "Col: <strong>" + xElem + "</strong><br />" +
                    "Value: <strong>" + d + "</strong><br />"
                )
                .style("left", mouseX + 130 + "px")
                .style("top", mouseY + 12 + "px");
        })
        .on("mouseout", function(d) {
            tooltip
                .transition()
                .duration(100)
                .style("opacity", 0);
        });

    var svg = d3.select('#analysis-container')
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g");

    var context = canvas.node().getContext("2d");

    var step = 2 / (color.range().length - 1);

    color.domain(d3.range(-1, 1, step));

    data.forEach(function(row, i) {
        row.forEach(function(val, j) {
            context.fillStyle = color(val);
            if (corrvar1 !== corrvar2) {
                context.fillRect(xScaleData(j), yScaleData(i), gridSize, gridSize);
            } else {
                context.fillRect(xScaleData(i), yScaleData(i + j), gridSize, gridSize);
                context.fillRect(xScaleData(i + j), yScaleData(i), gridSize, gridSize);
            }
        });
    });

    // x-axis
    var gX = svg
        .append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(" + margin.left + ", " + margin.top + ")")
        .call(xAxis)
        .selectAll("text")
        .attr("transform", "rotate(90)")
        .style("text-anchor", "end")
        .attr("y", 0)
        .attr("x", -8)
        .attr("dy", ".35em")
        .style("font-size", "9px");
    var gXTitle = gX
        .append("text")
        .attr("class", "label")
        .attr("x", "30")
        .attr("y", -6)
        .style("text-anchor", "end")
        .style("fill", "#000")
        .text("x");

    // y-axis
    var gY = svg
        .append("g")
        .attr("class", "y axis")
        .attr("transform", "translate(" + margin.left + ", " + margin.top + ")")
        .call(yAxis)
        .selectAll("text")
        .style("font-size", "9px");
    var gYTitle = gY
        .append("text")
        .attr("class", "label")
        .attr("x", "30")
        .attr("y", -6)
        .style("text-anchor", "end")
        .style("fill", "#000")
        .text("y");



    var legendWidth = Math.min(160, width),
        legendHeight = 10;

    var defs = svg.append("defs");
    defs.append("linearGradient")
        .attr("id", "gradient-rainbow-colors")
        .attr("x1", "0%").attr("y1", "0%")
        .attr("x2", "100%").attr("y2", "0%")
        .selectAll("stop")
        .data(coloursRainbow)
        .enter().append("stop")
        .attr("offset", function(d, i) {
            return i / (coloursRainbow.length - 1);
        })
        .attr("stop-color", function(d) {
            return d;
        });


    var legendsvg = svg.append("g")
        .attr("class", "legendWrapper")
        .attr("transform", "translate(" + margin.left + "," + (height + margin.top) + ")");

    legendsvg.append("rect")
        .attr("class", "legendRect")
        .attr("x", 0)
        .attr("y", 10)
        .attr("width", legendWidth)
        .attr("height", legendHeight)
        .style("fill", "url('#gradient-rainbow-colors')");

    var xScale = d3.scaleLinear()
        .range([0, legendWidth])
        .domain([-1, 1]);

    var xAxis = d3.axisBottom()
        .ticks(5)
        .scale(xScale);

    legendsvg.append("g")
        .attr("class", "axis")
        .attr("transform", "translate(0," + (10 + legendHeight) + ")")
        .call(xAxis)
        .selectAll("text")
        .style("font-size", "9px");;
}

function uncompress(base64data) {
    compressData = atob(base64data);
    compressData = compressData.split('').map(function(e) {
        return e.charCodeAt(0);
    });
    binData = new Uint8Array(compressData);
    data = pako.inflate(binData);

    var bufView = new Uint16Array(data);
    var length = bufView.length;
    var result = '';
    var addition = Math.pow(2, 16) - 1;

    for (var i = 0; i < length; i += addition) {
        if (i + addition > length) {
            addition = length - i;
        }
        result += String.fromCharCode.apply(null, bufView.subarray(i, i + addition));
    }

    return result;
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

    var corrvar1 = $("#corrvar1").val();
    var corrvar2 = $("#corrvar2").val();
    var cluster = $("#cluster").val();
    var minSamplesPresent = $("#minSamplesPresent").val();

    var data = {
        pid: $("#project").val(),
        taxonomyFilter: taxonomyFilter,
        taxonomyFilterRole: taxonomyFilterRole,
        taxonomyFilterVals: taxonomyFilterVals,
        sampleFilter: sampleFilter,
        sampleFilterRole: sampleFilterRole,
        sampleFilterVals: sampleFilterVals,
        level: level,
        corrvar1: corrvar1,
        corrvar2: corrvar2,
        cluster: cluster,
        minSamplesPresent: minSamplesPresent
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/heatmap" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            hideLoading();
            var abundancesObj = JSON.parse(uncompress(result));
            //            var abundancesObj = JSON.parse(result);
            $("#analysis-container").show();
            $("#stats-container").show();
            $("#display-error").hide();
            renderHeatmap(abundancesObj);
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
