$(document).ready(function() {
  // Initialization
  updateTaxonomicLevel(true, function() {
    updateAnalysis();
  });
  updateCatVar();
  createListeners();

  function createListeners() {
    $("#project").change(function () {
      updateAnalysis();
    });
    
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

    $("#alphaType").change(function () {
      updateAnalysis();
    });

    $("#alphaContext").change(function () {
      updateAnalysis();
    });
  }


  function updateAnalysis() {
    var level = taxonomyLevels[getTaxonomicLevel()];
    var taxonomy = $("#taxonomy-specific").val();
    if (taxonomy == null) {
      taxonomy = []
    }

    var catvar = $("#catvar").val();
    var alphaType = $("#alphaType").val();
    var alphaContext = $("#alphaContext").val();

    var data = {
      "pid": $("#project").val(),
      "level": level,
      "taxonomy": taxonomy.join(","),
      "catvar": catvar,
      "alphaType": alphaType,
      "alphaContext": alphaContext
    };

    $.ajax({
      type: "POST",
      url: "alpha_diversity",
      data: data,
      success: function(result) {
        var abundancesObj = JSON.parse(result);
        renderBoxplots(abundancesObj);
        renderPvaluesTable(abundancesObj);
      },
      error: function(err) {
        console.log(err)
      }
    });
  }
});