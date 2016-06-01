$(document).ready(function() {
  var abundancesObj = {};

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
  }

  function renderNMDS(data) {
    $("#analysis-container").empty();
    $("#analysis-container").append("<img src='" + data["fn"] + "' />")
  }

  function updateAnalysis() {
    var level = taxonomyLevels[getTaxonomicLevel()];
    var taxonomy = $("#taxonomy-specific").val();
    if (taxonomy == null) {
      taxonomy = []
    }

    var catvar = $("#catvar").val();

    var data = {
      "pid": $("#project").val(),
      "level": level,
      "taxonomy": taxonomy.join(","),
      "catvar": catvar
    };

    $.ajax({
      type: "POST",
      url: "nmds",
      data: data,
      success: function(result) {
        abundancesObj = JSON.parse(result);
        renderNMDS(abundancesObj);
      },
      error: function(err) {
        console.log(err)
      }
    });
  }
});