// ============================================================
// GLMNet JS Component
// ============================================================

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

//
// Analysis Specific Methods
//
function customLoading() {
    // This needs a categorical variable to work
    $("#catvar option[value='none']").remove();
}

function renderGlmnetTable(abundancesObj) {
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

    var catvar = $("#catvar").val();
    var keepthreshold = $("#keepthreshold").val();
    var alpha = $("#alpha").val();
    var family = $("#family").val();
    var lambdathreshold = $("#lambdathreshold").val();
    var lambdaval = $("#lambdaval").val();

    if (catvar === "none") {
        $("#analysis-container").hide();
        hideLoading();
        hideNotifications();
        showNoCatvar();
        return;
    }

    var data = {
      "pid": $("#project").val(),
      "taxonomyFilterCount": getLowCountThreshold(),
      "taxonomyFilterPrevalence": getPrevalenceThreshold(),
      "taxonomyFilter": taxonomyFilter,
      "taxonomyFilterRole": taxonomyFilterRole,
      "taxonomyFilterVals": taxonomyFilterVals,
      "sampleFilter": sampleFilter,
      "sampleFilterRole": sampleFilterRole,
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
        hideNotifications();
        hideLoading();

        var abundancesObj = JSON.parse(result);
        if (!$.isEmptyObject(abundancesObj)) {
            $("#analysis-container").show();
            renderGlmnetTable(abundancesObj);
        } else {
            $("#analysis-container").hide();
            showNoResults();
        }
      },
      error: function(err) {
        $("#analysis-container").hide();
        hideLoading();
        hideNotifications();
        showError();
        console.log(err);
      }
    });
}