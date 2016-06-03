$(document).ready(function() {
  // Initialization
  createListeners();

  updateTaxonomicLevel(true, function() {
    updateAnalysis();
  });

  function createListeners() {
    // Alter the second option so that the pairwise aren't both the same value
    $('#pwVar2 option:eq(1)').attr('selected', 'selected');

    $("#project").change(function () {
      updateTaxonomicLevel(false, function() {
        updateAnalysis();
      });
      updateCatVar();
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

    $("#minthreshold").change(function () {
      updateAnalysis();
    });

    $("#keepthreshold").change(function () {
      updateAnalysis();
    });

    $("#pwVar1").change(function () {
      updateAnalysis();
    });

    $("#pwVar2").change(function () {
      updateAnalysis();
    });
  }

  function renderFisherTable(abundancesObj) {
    $("#stats-container").hide();

    if ($.isEmptyObject(abundancesObj)) {
      return;
    }

    $('#stats-rows').empty();
    var statsArr = abundancesObj["results"];
    var cat1 = abundancesObj["cat1"];
    var cat2 = abundancesObj["cat2"];
    $("#cat1-present").text(cat1);
    $("#cat1-tot").text(cat1);
    $("#cat2-present").text(cat2);
    $("#cat2-tot").text(cat2);

    for (var i = 0; i < statsArr.length; i++) {
      var r = '<tr>';
      for (var j = 0; j < statsArr[i].length; j++) {
        r = r + '<td>' + statsArr[i][j] + '</td>';
      }
      r = r + '<tr>';
      $('#stats-rows').append(r);
    }
    
    $("#stats-container").fadeIn(250);
  }


  function updateAnalysis() {
    showLoading();
    var level = taxonomyLevels[getTaxonomicLevel()];
    var taxonomy = $("#taxonomy-specific").val();
    if (taxonomy == null) {
      taxonomy = []
    }

    var catvar = $("#catvar").val();
    var minthreshold = $("#minthreshold").val();
    var keepthreshold = $("#keepthreshold").val();
    var pwVar1 = $("#pwVar1").val();
    var pwVar2 = $("#pwVar2").val();

    var data = {
      "pid": $("#project").val(),
      "level": level,
      // "taxonomy": taxonomy.join(","),
      "taxonomy": "All", // TODO: FIX
      "catvar": catvar,
      "minthreshold": minthreshold,
      "keepthreshold": keepthreshold,
      "pwVar1": pwVar1,
      "pwVar2": pwVar2
    };

    $.ajax({
      type: "POST",
      url: "fisher_exact",
      data: data,
      success: function(result) {
        hideLoading();
        var abundancesObj = JSON.parse(result);
        renderFisherTable(abundancesObj);
      },
      error: function(err) {
        console.log(err)
      }
    });
  }
});