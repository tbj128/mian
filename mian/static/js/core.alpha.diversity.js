$(document).ready(function() {
  // Initialization

  $.when(updateTaxonomicLevel(true, function() {}), updateCatVar()).done(function(a1, a2) {
    updateAnalysis();
  });

  createListeners();

  function createListeners() {
    $("#project").change(function () {
      $.when(updateTaxonomicLevel(false, function() {}), updateCatVar()).done(function(a1, a2) {
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

    $("#alphaType").change(function () {
      updateAnalysis();
    });

    $("#alphaContext").change(function () {
      updateAnalysis();
    });
  }


  function updateAnalysis() {
    showLoading();
    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var alphaType = $("#alphaType").val();
    var alphaContext = $("#alphaContext").val();

    var data = {
      "pid": $("#project").val(),
      "taxonomyFilter": taxonomyFilter,
      "taxonomyFilterVals": taxonomyFilterVals,
      "sampleFilter": sampleFilter,
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
        hideLoading();
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