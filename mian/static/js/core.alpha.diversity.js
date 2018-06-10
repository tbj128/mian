// ============================================================
// Alpha Diversity Boxplot JS Component
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

    $("#alphaType").change(function () {
      updateAnalysis();
    });

    $("#alphaContext").change(function () {
      updateAnalysis();
    });

    $("#yvals").change(function () {
      var val = $("#yvals").val();
      if (val === "mian-max" || val === "mian-min") {
        if (val === "mian-max") {
          $("#taxonomic-level-label").text("Max Abundance Taxonomic Level");
        } else if (val === "mian-min") {
          $("#taxonomic-level-label").text("Min Abundance Taxonomic Level");
        }

        $("#taxonomic-level").show();
      } else {
        $("#taxonomic-level").hide();
      }

      updateAnalysis();
    });
}

//
// Analysis Specific Methods
//
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
    var alphaType = $("#alphaType").val();
    var alphaContext = $("#alphaContext").val();

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
      "alphaType": alphaType,
      "alphaContext": alphaContext
    };

    $.ajax({
      type: "POST",
      url: "alpha_diversity",
      data: data,
      success: function(result) {
        $("#display-error").hide();
        hideLoading();
        $("#analysis-container").show();
        $("#stats-container").show();
        var abundancesObj = JSON.parse(result);
        renderBoxplots(abundancesObj);
        renderPvaluesTable(abundancesObj);
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

function customLoading() {
    $("#yvals").empty();
    $("#yvals").append('<option value="mian-abundance">Aggregate Abundance</option><option value="mian-max">Max Abundance</option><option value="mian-min">Min Abundance</option><option value="mian-mean">Mean Abundance</option><option value="mian-median">Median Abundance</option>');
    for (var i = 0; i < catVars.length; i++) {
      $("#yvals").append('<option value="' + catVars[i] + '">' + catVars[i] + '</option>')
    }
}