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
      updateTaxonomicLevel(false, function() {
        updateAnalysis();
      });
      updateCatVar();
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
    showLoading();

    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();

    var data = {
      "pid": $("#project").val(),
      "taxonomyFilter": taxonomyFilter,
      "taxonomyFilterVals": taxonomyFilterVals,
      "sampleFilter": sampleFilter,
      "sampleFilterVals": sampleFilterVals,
      "level": level,
      "catvar": catvar
    };

    $.ajax({
      type: "POST",
      url: "nmds",
      data: data,
      success: function(result) {
        hideLoading();
        abundancesObj = JSON.parse(result);
        renderNMDS(abundancesObj);
      },
      error: function(err) {
        console.log(err)
      }
    });
  }
});