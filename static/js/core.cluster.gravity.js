$(document).ready(function() {
  // Initialization
  updateTaxonomicLevel(true, function() {
    updateAnalysis();
  });
  updateCatVar();
  createListeners();

  function createListeners() {
    $("#taxonomy").change(function () {
      updateTaxonomicLevel(false, function() {
        updateAnalysis();
      });
    });

    $("#taxonomy-specific").change(function () {
      updateAnalysis();
    });

    $("#catvar").change(function () {
      updateAnalysis();
    });

    $("#taxonomy_group_general").change(function () {
      updateAnalysis();
    });

    $("#taxonomy_group_specific").change(function () {
      updateAnalysis();
    });
  }

  function updateAnalysis(abundancesObj) {
    var level = taxonomyLevels[getTaxonomicLevel()];
    var taxonomy = $("#taxonomy-specific").val();
    if (taxonomy == null) {
      taxonomy = []
    }

    var catvar = $("#catvar").val();
    var taxonomy_group_general = $("#taxonomy_group_general").val();
    var taxonomy_group_specific = $("#taxonomy_group_specific").val();

    var data = {
      "pid": $("#project").val(),
      "level": level,
      "taxonomy": taxonomy.join(","),
      "catvar": catvar,
      "taxonomy_group_general": taxonomyLevels[taxonomy_group_general],
      "taxonomy_group_specific": taxonomyLevels[taxonomy_group_specific]
    };

    $.ajax({
      type: "POST",
      url: "abundances_grouping",
      data: data,
      success: function(result) {
        var abundancesObj = JSON.parse(result);
        console.log(abundancesObj)
        renderClusters(abundancesObj);
      },
      error: function(err) {
        console.log(err)
      }
    });
  }

  function renderClusters(abundancesObj) {
    var root = abundancesObj["root"];

    var diameter = 960,
        format = d3.format(",d");

    var pack = d3.layout.pack()
        .size([diameter - 4, diameter - 4])
        .value(function(d) { 
          return d["IPF"].c; 
        });

    var svg = d3.select("#analysis-container").append("svg")
        .attr("width", diameter)
        .attr("height", diameter)
      .append("g")
        .attr("transform", "translate(2,2)");

    var node = svg.datum(root).selectAll(".node")
        .data(pack.nodes)
      .enter().append("g")
        .attr("class", function(d) { return d.children ? "node" : "leaf node"; })
        .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });

    node.append("title")
        .text(function(d) { return d.name + (d.children ? "" : ": " + format(d["IPF"].c)); });

    node.append("circle")
        .attr("r", function(d) { return d.r; });

    node.filter(function(d) { return !d.children; }).append("text")
        .attr("dy", ".3em")
        .style("text-anchor", "middle")
        .text(function(d) { return d.name.substring(0, d.r / 3); });

  }

  // http://bl.ocks.org/mbostock/1748247
  function renderClusters2(abundancesObj) {
    var width = 960,
        height = 500,
        padding = 1.5, // separation between same-color circles
        clusterPadding = 36, // separation between different-color circles
        maxRadius = 12;

    var n = 200, // total number of circles
        m = 10; // number of distinct clusters

    var color = d3.scale.category10().domain(d3.range(m));

    // The largest node for each cluster.
    var clusters = new Array(m);

    var nodes = d3.range(n).map(function() {
      var i = Math.floor(Math.random() * m),
          r = Math.sqrt((i + 1) / m * -Math.log(Math.random())) * maxRadius,
          d = {
            cluster: i, 
            radius: r,
            x: Math.cos(i / m * 2 * Math.PI) * 200 + width / 2 + Math.random(),
            y: Math.sin(i / m * 2 * Math.PI) * 200 + height / 2 + Math.random()
          };

      if (!clusters[i] || (r > clusters[i].radius)) {
        clusters[i] = d;
      }

      return d;
    });

    var force = d3.layout.force()
        .nodes(nodes)
        .size([width, height])
        .gravity(0.1)
        .charge(0)
        // .on("tick", tick)
        .start();

    var svg = d3.select("#analysis-container").append("svg")
        .attr("width", width)
        .attr("height", height);

    var circle = svg.selectAll("circle")
        .data(nodes)
      .enter().append("circle")
        .attr("r", function(d) { return d.radius; })
        .style("fill", function(d) { return color(d.cluster); })
        .each(collide(.5))
        .attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; });

    // Resolves collisions between d and all other circles.
    function collide(alpha) {
      var quadtree = d3.geom.quadtree(nodes);

      return function(d) {
        var r = d.radius + maxRadius + Math.max(padding, clusterPadding),
            nx1 = d.x - r,
            nx2 = d.x + r,
            ny1 = d.y - r,
            ny2 = d.y + r;
        quadtree.visit(function(quad, x1, y1, x2, y2) {
          if (quad.point && (quad.point !== d)) {
            var x = d.x - quad.point.x,
                y = d.y - quad.point.y,
                l = Math.sqrt(x * x + y * y),
                r = d.radius + quad.point.radius + (d.cluster === quad.point.cluster ? padding : clusterPadding);
            if (l < r) {
              l = (l - r) / l * alpha;
              d.x -= x *= l;
              d.y -= y *= l;
              quad.point.x += x;
              quad.point.y += y;
            }
          }
          return x1 > nx2 || x2 < nx1 || y1 > ny2 || y2 < ny1;
        });
      };
    }
  }
});