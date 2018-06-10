// ============================================================
// NMDS JS Component
// ============================================================

var abundancesObj = {};

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
function renderNMDS(data) {
    $("#analysis-container").empty();
    $("#analysis-container").append("<img src='" + data["fn"] + "' />")
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

    var data = {
      "pid": $("#project").val(),
      "taxonomyFilter": taxonomyFilter,
      "taxonomyFilterRole": taxonomyFilterRole,
      "taxonomyFilterVals": taxonomyFilterVals,
      "sampleFilter": sampleFilter,
      "sampleFilterRole": sampleFilterRole,
      "sampleFilterVals": sampleFilterVals,
      "level": level,
      "catvar": catvar
    };

    $.ajax({
      type: "POST",
      url: "nmds",
      data: data,
      success: function(result) {
        $("#display-error").hide();
        hideLoading();
        $("#analysis-container").show();
        $("#stats-container").show();

        abundancesObj = JSON.parse(result);
        renderNMDS(abundancesObj);
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