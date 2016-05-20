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
    var level = taxonomyLevels[getTaxonomicLevel()];
    var taxonomy = $("#taxonomy-specific").val();
    if (taxonomy == null) {
      taxonomy = []
    }

    var catvar = $("#catvar").val();
    var betaType = $("#betaType").val();

    var data = {
      "pid": $("#project").val(),
      "level": level,
      "taxonomy": taxonomy.join(","),
      "catvar": catvar,
      "betaType": betaType
    };

    $.ajax({
      type: "POST",
      url: "beta_diversity",
      data: data,
      success: function(result) {
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