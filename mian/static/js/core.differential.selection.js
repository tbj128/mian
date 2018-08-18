// ============================================================
// Differential Selection JS Component
// ============================================================

var differentialDataTable;

//
// Initialization
//
initializeComponent({
    hasCatVar: true,
    hasCatVarNoneOption: false,
});
createSpecificListeners();

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    // Alter the second option so that the pairwise aren't both the same value
    $('#pwVar2 option:eq(1)').attr('selected', 'selected');

    $("#catvar").change(function () {
      updatePWComparisonSidebar(function() {
        updateAnalysis();
      });
    });

    $("#pvalthreshold").change(function () {
      updateAnalysis();
    });

    $("#pwVar1").change(function () {
      updateAnalysis();
    });

    $("#pwVar2").change(function () {
      updateAnalysis();
    });
}


//
// Analysis Specific Methods
//

function customLoading() {
    return updatePWComparisonSidebar();
}


function updatePWComparisonSidebar(callback) {
    var data = {
      "pid": $("#project").val(),
      "catvar": $("#catvar").val(),
    };

    return $.ajax({
      type: "GET",
      url: "metadata_vals",
      data: data,
      success: function(result) {
        $("#pwVar1").empty();
        $("#pwVar2").empty();
        var uniqueVals = JSON.parse(result);

        for (var i = 0; i < uniqueVals.length; i++) {
          $("#pwVar1").append("<option value='" + uniqueVals[i] + "'>" + uniqueVals[i] + "</option>");
          if (i == 1) {
            $("#pwVar2").append("<option value='" + uniqueVals[i] + "' selected>" + uniqueVals[i] + "</option>");
          } else {
            $("#pwVar2").append("<option value='" + uniqueVals[i] + "'>" + uniqueVals[i] + "</option>");
          }
        }

        if (callback) {
            callback();
        }
      },
      error: function(err) {
        console.log(err);
      }
    });
}

function renderDifferentialTable(abundancesObj) {

    if (differentialDataTable) {
        differentialDataTable
            .clear();
    } else {
        differentialDataTable = $('#differential-table').DataTable({
                                    order: [[ 2, "asc" ]],
                                    columns: [
                                        { "data": "otu" },
                                        { "data": "pval" },
                                        { "data": "qval" }
                                    ]
                               });
    }

    var differentials = abundancesObj["differentials"];
    differentialDataTable.rows.add(differentials);
    differentialDataTable.draw();
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
    var pvalthreshold = $("#pvalthreshold").val();
    var pwVar1 = $("#pwVar1").val();
    var pwVar2 = $("#pwVar2").val();

    var data = {
      "pid": $("#project").val(),
      "taxonomyFilter": taxonomyFilter,
      "taxonomyFilterRole": taxonomyFilterRole,
      "taxonomyFilterVals": taxonomyFilterVals,
      "sampleFilter": sampleFilter,
      "sampleFilterRole": sampleFilterRole,
      "sampleFilterVals": sampleFilterVals,
      "level": level,
      "catvar": catvar,
      "pvalthreshold": pvalthreshold,
      "pwVar1": pwVar1,
      "pwVar2": pwVar2
    };

    $.ajax({
      type: "POST",
      url: "differential_selection",
      data: data,
      success: function(result) {
        $("#display-error").hide();
        hideLoading();
        $("#analysis-container").show();
        $("#stats-container").show();

        var abundancesObj = JSON.parse(result);
        renderDifferentialTable(abundancesObj);
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