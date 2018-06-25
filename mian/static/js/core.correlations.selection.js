// ============================================================
// Correlations Selection JS Component
// ============================================================

var correlationDataTable;

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
}


//
// Analysis Specific Methods
//

function customLoading() {
    return updateCatVar(true);
}

function updateAnalysis() {
    showLoading();
    
    var level = taxonomyLevels[getTaxonomicLevel()];
    var catvar = $("#catvar").val();

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var data = {
      "pid": $("#project").val(),
      "taxonomyFilter": taxonomyFilter,
      "taxonomyFilterRole": taxonomyFilterRole,
      "taxonomyFilterVals": taxonomyFilterVals,
      "sampleFilter": sampleFilter,
      "sampleFilterRole": sampleFilterRole,
      "sampleFilterVals": sampleFilterVals,
      "catvar": catvar,
      "level": level
    };

    $.ajax({
      type: "POST",
      url: "correlations_selection",
      data: data,
      success: function(result) {
        $("#display-error").hide();
        hideLoading();
        $("#analysis-container").show();
        abundancesObj = JSON.parse(result);
        renderCorrelationsSelection(abundancesObj);
      },
      error: function(err) {
        hideLoading();
        $("#analysis-container").hide();
        $("#display-error").show();
        console.log(err);
      }
    });
}

function renderCorrelationsSelection(abundancesObj) {
    $("#correlation-metadata").text($("#catvar").val());

    if (correlationDataTable) {
        correlationDataTable
            .clear();
    } else {
        correlationDataTable = $('#correlation-table').DataTable({
                                    order: [[ 2, "asc" ]],
                                    columns: [
                                        { "data": "otu" },
                                        { "data": "coef" },
                                        { "data": "pval" },
                                        { "data": "qval" }
                                    ]
                               });
    }

    var correlations = abundancesObj["correlations"];
    correlationDataTable.rows.add(correlations);
    correlationDataTable.draw();
}
