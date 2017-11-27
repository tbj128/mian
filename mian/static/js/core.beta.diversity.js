$(document).ready(function() {
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

    $("#betaType").change(function () {
      updateAnalysis();
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

  function updateAnalysis() {
    showLoading();

    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var betaType = $("#betaType").val();

    var data = {
      "pid": $("#project").val(),
      "taxonomyFilter": taxonomyFilter,
      "taxonomyFilterVals": taxonomyFilterVals,
      "sampleFilter": sampleFilter,
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
        hideLoading();
        var abundancesObj = JSON.parse(result);
        renderBoxplots(abundancesObj);
        renderPvaluesTable(abundancesObj);
        renderPERMANOVA(abundancesObj);
        renderBetadisper(abundancesObj);
      },
      error: function(err) {
        console.log(err)
      }
    });
  }
});