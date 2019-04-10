// ============================================================
// PCA JS Component
// ============================================================
var abundancesObj = {};
var boundX = [];
var boundY = [];
var pcaOverrideScale = null;
var pcaOverrideAlpha = null;
var pcaOverrideBeta = null;
var pcaOverrideRangeMin = null;
var pcaOverrideRangeMax = null;
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
    if (getParameterByName("numberAxes") !== null) {
        $("#numberAxes").val(getParameterByName("numberAxes"));
    }
    if (getParameterByName("type") !== null) {
        $("#type").val(getParameterByName("type"));
    }
    if (getParameterByName("pca1") !== null) {
        $("#pca1").val(getParameterByName("pca1"));
    }
    if (getParameterByName("pca2") !== null) {
        $("#pca2").val(getParameterByName("pca2"));
    }
    if (getParameterByName("pca3") !== null) {
        $("#pca3").val(getParameterByName("pca3"));
    }
    if (getParameterByName("rangeMin") !== null) {
        pcaOverrideRangeMin = getParameterByName("rangeMin");
    }
    if (getParameterByName("rangeMax") !== null) {
        pcaOverrideRangeMax = getParameterByName("rangeMax");
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

    $("#pca1").change(function() {
        updateAnalysis();
    });

    $("#pca2").change(function() {
        updateAnalysis();
    });

    $("#pca3").change(function() {
        updateAnalysis();
    });

    $("#numberAxes").change(function() {
        updateAnalysis();
        setGetParameters({
            "numberAxes": $("#numberAxes").val(),
        });
    });

    $("#download-svg").click(function() {
        downloadSVG("pca." + $("#catvar").val());
    });
}

//
// Analysis Specific Methods
//

function render3dPCA(args) {
    $("#analysis-container").empty();
    $("#analysis-container").html('<svg width="880" height="500"></svg>');

    var origin = [440, 250],
        j = 10,
        scale = 20,
        scatter = [],
        xLine = [],
        yLine = [],
        zLine = [],
        xGrid = [],
        xg = [],
        yg = [],
        zg = [],
        beta = 0,
        alpha = 0,
        key = function(d) {
            return d.id;
        },
        startAngle = 7 * Math.PI / 4;
    var xRange = [Math.floor(args["pca1Min"]), Math.ceil(args["pca1Max"])];
    var yRange = [Math.floor(args["pca2Min"]), Math.ceil(args["pca2Max"])];
    var zRange = [Math.floor(args["pca3Min"]), Math.ceil(args["pca3Max"])];
    var maxRange = [Math.floor(Math.min(args["pca1Min"], args["pca2Min"], args["pca3Min"])), Math.ceil(Math.max(args["pca1Max"], args["pca2Max"], args["pca3Max"]))]
    if (args["overrideMin"] && args["overrideMax"]) {
        maxRange = [Math.floor(args["overrideMin"]), Math.ceil(args["overrideMax"])];
    }

    var xGap = Math.ceil((xRange[1] - xRange[0]) / j);
    var yGap = Math.ceil((yRange[1] - yRange[0]) / j);
    var zGap = Math.ceil((zRange[1] - zRange[0]) / j);
    var maxGap = (maxRange[1] - maxRange[0]) > 0 ? Math.ceil((maxRange[1] - maxRange[0]) / j) : Math.round(10 * (maxRange[1] - maxRange[0]) / j) / 10;

    var color = d3.scaleOrdinal(d3.schemeCategory20);
    var mx, my, mouseX, mouseY;

    var xgrid3d = d3._3d()
        .shape('GRID', j)
        .origin(origin)
        .rotateY(pcaOverrideBeta ? (pcaOverrideBeta + startAngle) : startAngle)
        .rotateX(pcaOverrideAlpha ? (pcaOverrideAlpha - startAngle) : -startAngle)
        .scale(pcaOverrideScale ? pcaOverrideScale : scale);

    var ygrid3d = d3._3d()
        .shape('GRID', j)
        .origin(origin)
        .rotateY(pcaOverrideBeta ? (pcaOverrideBeta + startAngle) : startAngle)
        .rotateX(pcaOverrideAlpha ? (pcaOverrideAlpha - startAngle) : -startAngle)
        .scale(pcaOverrideScale ? pcaOverrideScale : scale);

    var zgrid3d = d3._3d()
        .shape('GRID', j)
        .origin(origin)
        .rotateY(pcaOverrideBeta ? (pcaOverrideBeta + startAngle) : startAngle)
        .rotateX(pcaOverrideAlpha ? (pcaOverrideAlpha - startAngle) : -startAngle)
        .scale(pcaOverrideScale ? pcaOverrideScale : scale);

    var point3d = d3._3d()
        .x(function(d) {
            return d.x;
        })
        .y(function(d) {
            return d.y;
        })
        .z(function(d) {
            return d.z;
        })
        .origin(origin)
        .rotateY(pcaOverrideBeta ? (pcaOverrideBeta + startAngle) : startAngle)
        .rotateX(pcaOverrideAlpha ? (pcaOverrideAlpha - startAngle) : -startAngle)
        .scale(pcaOverrideScale ? pcaOverrideScale : scale);

    var xScale3d = d3._3d()
        .shape('LINE_STRIP')
        .origin(origin)
        .rotateY(pcaOverrideBeta ? (pcaOverrideBeta + startAngle) : startAngle)
        .rotateX(pcaOverrideAlpha ? (pcaOverrideAlpha - startAngle) : -startAngle)
        .scale(pcaOverrideScale ? pcaOverrideScale : scale);

    var yScale3d = d3._3d()
        .shape('LINE_STRIP')
        .origin(origin)
        .rotateY(pcaOverrideBeta ? (pcaOverrideBeta + startAngle) : startAngle)
        .rotateX(pcaOverrideAlpha ? (pcaOverrideAlpha - startAngle) : -startAngle)
        .scale(pcaOverrideScale ? pcaOverrideScale : scale);

    var zScale3d = d3._3d()
        .shape('LINE_STRIP')
        .origin(origin)
        .rotateY(pcaOverrideBeta ? (pcaOverrideBeta + startAngle) : startAngle)
        .rotateX(pcaOverrideAlpha ? (pcaOverrideAlpha - startAngle) : -startAngle)
        .scale(pcaOverrideScale ? pcaOverrideScale : scale);

    var tooltip = d3
        .select("#analysis-container")
        .append("div")
        .attr("class", "tooltip")
        .style("opacity", 0)
        .style("width", "160px");

    var zoom = d3.zoom()
        .on("zoom", zoomed);

    var svgBase = d3.select('#analysis-container svg')
        .call(
            d3.drag().on('drag', dragged).on('start', dragStart).on('end', dragEnd)
        )
        .call(
            zoom
        );

    var svg = svgBase
        .append('g');

    function processData(data, tt) {

        /* ----------- X-GRID ----------- */

        var xGrid = svg.selectAll('path.xgrid').data(data.xGrid, key);

        xGrid
            .enter()
            .append('path')
            .attr('class', '_3d xgrid')
            .merge(xGrid)
            .attr('stroke', '#999')
            .attr('stroke-width', 0.3)
            .attr('fill-opacity', 0.05)
            .attr('d', xgrid3d.draw);

        xGrid.exit().remove();

        /* ----------- Y-GRID ----------- */

        var yGrid = svg.selectAll('path.ygrid').data(data.yGrid, key);

        yGrid
            .enter()
            .append('path')
            .attr('class', '_3d ygrid')
            .merge(yGrid)
            .attr('stroke', '#999')
            .attr('stroke-width', 0.3)
            .attr('fill-opacity', 0.05)
            .attr('d', ygrid3d.draw);

        yGrid.exit().remove();

        /* ----------- Z-GRID ----------- */

        var zGrid = svg.selectAll('path.zgrid').data(data.zGrid, key);

        zGrid
            .enter()
            .append('path')
            .attr('class', '_3d zgrid')
            .merge(zGrid)
            .attr('stroke', '#999')
            .attr('stroke-width', 0.3)
            .attr('fill-opacity', 0.05)
            .attr('d', zgrid3d.draw);

        zGrid.exit().remove();

        /* ----------- POINTS ----------- */

        var points = svg.selectAll('circle').data(data.points, key);

        var cValue = function(d) {
                return d.m;
            },
            color = d3.scaleOrdinal(d3.schemeCategory10);

        points
            .enter()
            .append('circle')
            .attr('class', '_3d')
            .merge(points)
            .attr('r', 3)
            .attr('stroke', function(d) {
                return d3.color(color(cValue(d))).darker(3);
            })
            .attr('cx', posPointX)
            .attr('cy', posPointY)
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
                        "</strong><br />" +
                        $("#pca1").val() +
                        ": <strong>" +
                        d.pca1 +
                        "</strong><br />" +
                        $("#pca2").val() +
                        ": <strong>" +
                        d.pca2 +
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

        points.exit().remove();

        /* ----------- x-Scale ----------- */

        var xScale = svg.selectAll('path.xScale').data(data.xScale);

        xScale
            .enter()
            .append('path')
            .attr('class', '_3d xScale')
            .merge(xScale)
            .attr('stroke', 'black')
            .attr('stroke-width', .5)
            .attr('d', xScale3d.draw);

        xScale.exit().remove();

        /* ----------- x-Scale Text ----------- */

        var xText = svg.selectAll('text.xText').data(data.xScale[0]);

        xText
            .enter()
            .append('text')
            .attr('class', '_3d xText')
            .attr('dx', '.3em')
            .merge(xText)
            .each(function(d) {
                d.centroid = {
                    x: d.rotated.x,
                    y: d.rotated.y,
                    z: d.rotated.z
                };
            })
            .attr('x', function(d) {
                return d.projected.x;
            })
            .attr('y', function(d) {
                return d.projected.y;
            })
            .text(function(d) {
                return d[0];
            });

        xText.exit().remove();


        /* ----------- y-Scale ----------- */

        var yScale = svg.selectAll('path.yScale').data(data.yScale);

        yScale
            .enter()
            .append('path')
            .attr('class', '_3d yScale')
            .merge(yScale)
            .attr('stroke', 'black')
            .attr('stroke-width', .5)
            .attr('d', yScale3d.draw);

        yScale.exit().remove();

        /* ----------- y-Scale Text ----------- */

        var yText = svg.selectAll('text.yText').data(data.yScale[0]);

        yText
            .enter()
            .append('text')
            .attr('class', '_3d yText')
            .attr('dx', '.3em')
            .merge(yText)
            .each(function(d) {
                d.centroid = {
                    x: d.rotated.x,
                    y: d.rotated.y,
                    z: d.rotated.z
                };
            })
            .attr('x', function(d) {
                return d.projected.x;
            })
            .attr('y', function(d) {
                return d.projected.y;
            })
            .text(function(d) {
                return d[1];
            });

        yText.exit().remove();


        /* ----------- z-Scale ----------- */

        var zScale = svg.selectAll('path.zScale').data(data.zScale);

        zScale
            .enter()
            .append('path')
            .attr('class', '_3d yScale')
            .merge(zScale)
            .attr('stroke', 'black')
            .attr('stroke-width', .5)
            .attr('d', zScale3d.draw);

        zScale.exit().remove();

        /* ----------- z-Scale Text ----------- */

        var zText = svg.selectAll('text.zText').data(data.zScale[0]);

        zText
            .enter()
            .append('text')
            .attr('class', '_3d zText')
            .attr('dx', '.3em')
            .merge(zText)
            .each(function(d) {
                d.centroid = {
                    x: d.rotated.x,
                    y: d.rotated.y,
                    z: d.rotated.z
                };
            })
            .attr('x', function(d) {
                return d.projected.x;
            })
            .attr('y', function(d) {
                return d.projected.y;
            })
            .text(function(d) {
                return d[2];
            });

        zText.exit().remove();


        d3.selectAll('._3d').sort(d3._3d().sort);

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
                .attr("x", 0)
                .attr("width", 18)
                .attr("height", 18)
                .style("fill", color);

            // draw legend text
            legend
                .append("text")
                .attr("x", 24)
                .attr("y", 9)
                .attr("dy", ".35em")
                .text(function(d) {
                    return d;
                });
        }
    }

    function posPointX(d) {
        return d.projected.x;
    }

    function posPointY(d) {
        return d.projected.y;
    }

    function init(args) {
        var cnt = 0;
        xg = [], yg = [], zg = [], scatter = [], xLine = [], yLine = [], zLine = [];

        for (var x = maxRange[0], a = 0; a < 10; x += maxGap, a += 1) {
            for (var z = maxRange[0], b = 0; b < 10; z += maxGap, b += 1) {
                xg.push([x, maxRange[0], z]);
                yg.push([x, z, maxRange[0]]);
                zg.push([maxRange[0], x, z]);
            }

            xLine.push([x, maxRange[0], maxRange[0]]);
            yLine.push([maxRange[0], x, maxRange[0]]);
            zLine.push([maxRange[0], maxRange[0], x]);
        }

        scatter = args["pca"].map(function(d) {
            return {
                ...d,
                x: d.pca1,
                y: d.pca2,
                z: d.pca3,
                id: d.s,
            };
        });

        var data = {
            xGrid: xgrid3d(xg),
            yGrid: ygrid3d(yg),
            zGrid: zgrid3d(zg),
            points: point3d(scatter),
            xScale: xScale3d([xLine]),
            yScale: yScale3d([yLine]),
            zScale: zScale3d([zLine])
        };
        processData(data, 1000);

        pcaOverrideScale = pcaOverrideScale ? pcaOverrideScale : 15;
        svgBase.call(zoom.transform, d3.zoomIdentity.translate(0, 0).scale(pcaOverrideScale));
    }

    function dragStart() {
        mx = d3.event.x;
        my = d3.event.y;
    }

    function dragged() {
        mouseX = mouseX || 0;
        mouseY = mouseY || 0;
        beta = (d3.event.x - mx + mouseX) * Math.PI / 230;
        alpha = (d3.event.y - my + mouseY) * Math.PI / 230 * (-1);

        pcaOverrideBeta = beta;
        pcaOverrideAlpha = alpha;

        var data = {
            xGrid: xgrid3d.rotateY(beta + startAngle).rotateX(alpha - startAngle)(xg),
            yGrid: ygrid3d.rotateY(beta + startAngle).rotateX(alpha - startAngle)(yg),
            zGrid: ygrid3d.rotateY(beta + startAngle).rotateX(alpha - startAngle)(zg),
            points: point3d.rotateY(beta + startAngle).rotateX(alpha - startAngle)(scatter),
            xScale: yScale3d.rotateY(beta + startAngle).rotateX(alpha - startAngle)([xLine]),
            yScale: yScale3d.rotateY(beta + startAngle).rotateX(alpha - startAngle)([yLine]),
            zScale: zScale3d.rotateY(beta + startAngle).rotateX(alpha - startAngle)([zLine]),
        };
        processData(data, 0);
    }

    function dragEnd() {
        mouseX = d3.event.x - mx + mouseX;
        mouseY = d3.event.y - my + mouseY;
    }


    function zoomed() {
        pcaOverrideScale = d3.event.transform.k;
        var data = {
            xGrid: xgrid3d.scale(d3.event.transform.k)(xg),
            yGrid: ygrid3d.scale(d3.event.transform.k)(yg),
            zGrid: ygrid3d.scale(d3.event.transform.k)(zg),
            points: point3d.scale(d3.event.transform.k)(scatter),
            xScale: yScale3d.scale(d3.event.transform.k)([xLine]),
            yScale: yScale3d.scale(d3.event.transform.k)([yLine]),
            zScale: zScale3d.scale(d3.event.transform.k)([zLine]),
        };
        processData(data, 0);
    }

    init(args);
}

function renderPCA(data) {
    $("#analysis-container-2d").empty();

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
            return d.pca1;
        }, // data -> value
        xScale = d3.scaleLinear().range([0, width]), // value -> display
        xMap = function(d) {
            return xScale(xValue(d));
        }, // data -> display
        xAxis = d3.axisBottom(xScale);

    // setup y
    var yValue = function(d) {
            return d.pca2;
        }, // data -> value
        yScale = d3.scaleLinear().range([height, 0]), // value -> display
        yMap = function(d) {
            return yScale(yValue(d));
        }, // data -> display
        yAxis = d3.axisLeft(yScale);

    // setup fill color
    var cValue = function(d) {
            return d.m;
        },
        color = d3.scaleOrdinal(d3.schemeCategory10);

    var zoom = d3.zoom()
        .on("zoom", zoomFunction);

    // add the graph canvas to the body of the webpage
    var svgBase = d3
        .select("#analysis-container-2d")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);

    var svg = svgBase
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
        .call(zoom);

    xDomain = [];
    if (boundX.length == 0) {
        xDomain = d3.extent(data, function(d) {
            return d.pca1;
        });
    } else {
        xDomain = [boundX[0], boundX[1]];
    }

    yDomain = [];
    if (boundY.length == 0) {
        yDomain = d3.extent(data, function(d) {
            return d.pca2;
        });
    } else {
        yDomain = [boundY[0], boundY[1]];
    }

    xScale.domain(xDomain);
    yScale.domain(yDomain);

    // tooltip that appears when hovering over a dot
    var tooltip = d3
        .select("#analysis-container-2d")
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
        .style("fill", "#000")
        .text($("#pca1 option:selected").text());

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
        .style("fill", "#000")
        .text($("#pca2 option:selected").text());

    var view = svg.append("rect")
        .attr("class", "zoom")
        .attr("width", width)
        .attr("height", height)
        .style("fill", "none")
        .style("pointer-events", "all")
        .call(zoom);

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
                    "</strong><br />" +
                    $("#pca1").val() +
                    ": <strong>" +
                    d.pca1 +
                    "</strong><br />" +
                    $("#pca2").val() +
                    ": <strong>" +
                    d.pca2 +
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

function renderPCAVar(data) {
    $("#variance-container").empty();
    $("#variance-container").html("<h5>Variance Captured By Principal Components</h5>");

    var margin = {
            top: 20,
            right: 20,
            bottom: 50,
            left: 80
        },
        width = 640 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    // setup x
    var xValue = function(d, i) {
            return i;
        }, // data -> value
        xScale = d3.scaleLinear().range([0, width]), // value -> display
        xAxis = d3
        .axisBottom()
        .scale(xScale);

    // setup y
    var yValue = function(d) {
            return d;
        }, // data -> value
        yScale = d3.scaleLinear().range([height, 0]), // value -> display
        yAxis = d3
        .axisLeft()
        .scale(yScale);

    xScale.domain(
        d3.extent(data, function(d, i) {
            return i + 1;
        })
    );
    yScale.domain(
        d3.extent(data, function(d) {
            return d;
        })
    );

    // add the graph canvas to the body of the webpage
    var svg = d3
        .select("#variance-container")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // x-axis
    svg
        .append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis)
        .append("text")
        .attr("class", "label")
        .attr("x", width / 2)
        .attr("y", 36)
        .style("fill", "#000")
        .text("Principal Component #");

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
        .style("fill", "#000")
        .style("text-anchor", "end")
        .text("Variance (%)");

    var line = d3
        .line()
        .x(function(d, i) {
            return xScale(i + 1);
        })
        .y(function(d) {
            return yScale(d);
        });

    svg
        .append("path")
        .datum(data)
        .attr("class", "line")
        .attr("d", line);
}

function renderRangeSlider(sliderNum) {
    $("div#slider-range-" + sliderNum).empty();

    var dataRange = [abundancesObj["pca" + sliderNum + "Min"], abundancesObj["pca" + sliderNum + "Max"]];
    var defaultRange = dataRange;

    // Set the default PCA range based on the URL params (if applicable)
    if (pcaOverrideRangeMin && pcaOverrideRangeMax) {
        defaultRange = [pcaOverrideRangeMin, pcaOverrideRangeMax];
        pcaOverrideRangeMin = null;
        pcaOverrideRangeMax = null;
    }
    var sliderRange = d3
        .sliderBottom()
        .min(d3.min(dataRange))
        .max(d3.max(dataRange))
        .width(270)
        .tickFormat(d3.format('.1f'))
        .ticks(5)
        .default(defaultRange)
        .fill('#2196f3')
        .on('onchange',
            _.debounce(function(val) {
                abundancesObj["overrideMin"] = val[0];
                abundancesObj["overrideMax"] = val[1];
                setGetParameters({
                    "rangeMin": val[0],
                    "rangeMax": val[1],
                });
                if ($("#numberAxes").val() === "3D") {
                    $("#pca-axis3").show();
                    $("#axis-range-container").show();
                    $("#analysis-container").show();
                    $("#analysis-container-2d").hide();
                    render3dPCA(abundancesObj);
                } else {
                    $("#pca-axis3").hide();
                    $("#axis-range-container").hide();
                    $("#analysis-container").hide();
                    $("#analysis-container-2d").show();
                    renderPCA(abundancesObj["pca"]);
                }
                renderPCAVar(abundancesObj["pcaVar"]);
            }, 500)
        );

    var gRange = d3
        .select('div#slider-range-' + sliderNum)
        .append('svg')
        .attr('width', 340)
        .attr('height', 80)
        .append('g')
        .attr('transform', 'translate(15,30)');

    gRange.call(sliderRange);
}

function render() {

    renderRangeSlider(1);

    if ($("#numberAxes").val() === "3D") {
        $("#pca-axis3").show();
        $("#axis-range-container").show();
        $("#analysis-container").show();
        $("#analysis-container-3d-info").show();
        $("#analysis-container-2d").hide();
        render3dPCA(abundancesObj);
    } else {
        $("#pca-axis3").hide();
        $("#axis-range-container").hide();
        $("#analysis-container").hide();
        $("#analysis-container-3d-info").hide();
        $("#analysis-container-2d").show();
        renderPCA(abundancesObj["pca"]);
    }

    renderPCAVar(abundancesObj["pcaVar"]);
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
    var pca1 = $("#pca1").val();
    var pca2 = $("#pca2").val();
    var pca3 = $("#pca3").val();

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
        pca1: pca1,
        pca2: pca2,
        pca3: pca3
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/pca" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            abundancesObj = JSON.parse(result);
            if (abundancesObj["no_tree"]) {
                loadNoTree();
                $("#analysis-container-2d").hide();
                $("#analysis-container-3d-info").hide();
                $("#variance-container").hide();
            } else if (abundancesObj["has_float"]) {
                loadFloatDataWarning();
                $("#analysis-container-2d").hide();
                $("#analysis-container-3d-info").hide();
                $("#variance-container").hide();
            } else {
                loadSuccess();
                $("#variance-container").show();
                boundX = [];
                boundY = [];

                render();
            }
        },
        error: function(err) {
            loadError();
            $("#analysis-container-2d").hide();
            $("#analysis-container-3d-info").hide();
            $("#variance-container").hide();

            console.log(err);
        }
    });
}
