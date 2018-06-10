// ============================================================
// Beta Diversity Boxplot JS Component
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

    $("#betaType").change(function () {
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
    var betaType = $("#betaType").val();

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
      "betaType": betaType
    };

    $.ajax({
      type: "POST",
      url: "beta_diversity",
      data: data,
      success: function(result) {
        $("#display-error").hide();
        hideLoading();
        $("#analysis-container").show();
        $("#stats-container").show();
        var abundancesObj = JSON.parse(result);
        renderBoxplots(abundancesObj);
        renderPvaluesTable(abundancesObj);
        renderPERMANOVA(abundancesObj);
        renderBetadisper(abundancesObj);
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

function renderPERMANOVA(abundancesObj) {
    $("#permanova-container").hide();
    var permanova = abundancesObj["permanova"];
    permanova = permanova.replace(/(?:\r\n|\r|\n)/g, '<br />');
    permanova = permanova.replace(/<br \/><br \/>/g, '<br />');
    $("#permanova").html(permanova);
    $("#permanova-container").fadeIn(250);
}

function renderBetadisper(abundancesObj) {
    $("#betadisper-container").hide();
    var betaDisper = abundancesObj["dispersions"];
    betaDisper = betaDisper.replace(/(?:\r\n|\r|\n)/g, '<br />');
    betaDisper = betaDisper.replace(/<br \/><br \/>/g, '<br />');
    $("#betadisper").html(betaDisper);
    $("#betadisper-container").fadeIn(250);
}