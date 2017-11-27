$(document).ready(function() {
  // Initialization
  createListeners();

  updateAnalysis();
  
  function createListeners() {
    $("#project").change(function () {
      $.when(updateCatVar()).done(function(a1) {
        updateAnalysis();
      });
    });

    $("#filter-sample").change(function() {
      var filterVal = $("#filter-sample").val();
      if (filterVal === "none" || filterVal === "mian-sample-id") {
        updateAnalysis();
      }
    });

    $("#filter-otu").change(function() {
      var filterVal = $("#filter-otu").val();
      if (filterVal === "none") {
        updateAnalysis();
      }
    });

    $("#taxonomy-specific").change(function () {
      updateAnalysis();
    });

    $("#filter-sample-specific").change(function () {
      updateAnalysis();
    });

    $("#taxonomy").change(function () {
      updateAnalysis();
    });

    $("#catvar").change(function () {
      updateAnalysis();
    });

    $("#keepthreshold").change(function () {
      updateAnalysis();
    });

    $("#alpha").change(function () {
      updateAnalysis();
    });

    $("#family").change(function () {
      updateAnalysis();
    });

    $("#lambdathreshold").change(function () {
      updateAnalysis();
      if ($("#lambdathreshold").val() === "Custom") {
        $("#lambdaval").show();
        $("#lambdatitle").show();
      } else {
        $("#lambdaval").hide();
        $("#lambdatitle").hide();
      }
    });

    $("#lambdaval").change(function () {
      updateAnalysis();
    });
  }

  function renderGlmnetTable(abundancesObj) {
    $("#stats-container").hide();

    if ($.isEmptyObject(abundancesObj)) {
      return;
    }

    $("#analysis-container").empty();

    var familyType = $("#family").val();

    var stats = abundancesObj["results"];
    var render = "<div>";

    var s = 0;
    $.each( stats, function( key, value ) {
      if (familyType != "binomial") {
        render += "<h3>" + key + "</h3>";
      }

      if (familyType == "binomial" && s == 1) {
        return;
      } else {
        s = 1;
      }

      var numPos = 0;
      var numNeg = 0;
      value.forEach(function(val) {
        if (val[1] > 0) {
          numPos += 1;
        } else if (val[1] < 0) {
          numNeg += 1;
        }
      });

      for (var i = 0; i < 2; i++) {
        if (i == 0) {
          render += "<h4>Positive (" + numPos + " Relevant)</h4>";
        } else if (i == 1) {
          render += "<h4>Negative (" + numNeg + " Relevant)</h4>";
        } else if (i == 2) {
          render += "<h4>Not Important</h4>";
        }

        render += '<table class="table table-hover"><thead><tr><th>Taxonomy</th><th>Value</th></tr></thead><tbody> ';
        value.forEach(function(val) {
          if (i == 0) {
            if (val[1] > 0) {
              render += '<tr><td>' + val[0] + '</td><td>' + val[1] + '</td></tr>';
            }
          } else if (i == 1) {
            if (val[1] < 0) {
              render += '<tr><td>' + val[0] + '</td><td>' + val[1] + '</td></tr>';
            }
          } else if (i == 2) {
            if (val[1] == 0) {
              render += '<tr><td>' + val[0] + '</td><td>' + val[1] + '</td></tr>';
            }
          }
        });
        render += '</tbody></table>';
      }
    });

    render += "</div><br /><hr /><br />";
    $("#analysis-container").append(render);

    $("#stats-container").fadeIn(250);
  }


  function updateAnalysis() {
    showLoading();
    
    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var keepthreshold = $("#keepthreshold").val();
    var alpha = $("#alpha").val();
    var family = $("#family").val();
    var lambdathreshold = $("#lambdathreshold").val();
    var lambdaval = $("#lambdaval").val();

    var data = {
      "pid": $("#project").val(),
      "taxonomyFilter": taxonomyFilter,
      "taxonomyFilterVals": taxonomyFilterVals,
      "sampleFilter": sampleFilter,
      "sampleFilterVals": sampleFilterVals,
      "level": level,
      "catvar": catvar,
      "keepthreshold": keepthreshold,
      "alpha": alpha,
      "family": family,
      "lambdathreshold": lambdathreshold,
      "lambdaval": lambdaval
    };

    $.ajax({
      type: "POST",
      url: "glmnet",
      data: data,
      success: function(result) {
        hideLoading();
        var abundancesObj = JSON.parse(result);
        renderGlmnetTable(abundancesObj);
      },
      error: function(err) {
        console.log(err)
      }
    });
  }
});