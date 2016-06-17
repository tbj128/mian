$(document).ready(function() {
  // Initialization
  createListeners();
  updateAnalysis();

  // updateTaxonomicLevel(true, function() {
  //   updateAnalysis();
  // });

  function createListeners() {
    // Alter the second option so that the pairwise aren't both the same value
    $('#pwVar2 option:eq(1)').attr('selected', 'selected');

    $("#project").change(function () {
      $.when(updateTaxonomicLevel(true, function() {}), updateCatVar()).done(function(a1, a2) {
        updatePWComparisonSidebar(function() {
          updateAnalysis();
        });
      });
    });

    $("#taxonomy").change(function () {
      updateTaxonomicLevel(false, function() {
        updateAnalysis();
      });
    });

    // $("#taxonomy-specific").change(function () {
    //   updateAnalysis();
    // });

    $("#catvar").change(function () {
      updateAnalysis();
    });

    $("#enrichedthreshold").change(function () {
      updateAnalysis();
    });

    $("#pwVar1").change(function () {
      updateAnalysis();
    });

    $("#pwVar2").change(function () {
      updateAnalysis();
    });
  }

  function updatePWComparisonSidebar(callback) {
    var data = {
      "pid": $("#project").val(),
      "catvar": $("#catvar").val(),
    };

    $.ajax({
      type: "GET",
      url: "metadata_vals",
      data: data,
      success: function(result) {
        hideLoading();
        $("#pwVar1").empty();
        $("#pwVar2").empty();
        var uniqueVals = JSON.parse(result);

        for (var i = 0; i < uniqueVals.length; i++) {
          $("#pwVar1").append("<option value='" + uniqueVals[i] + "'>" + uniqueVals[i] + "</option>");
          if (i == 1) {
            $("#pwVar2").append("<option value='" + uniqueVals[i] + "' selected>" + uniqueVals[i] + "</option>");
          } else {
            $("#pwVar2").append("<option value='" + uniqueVals[i] + "'>" + uniqueVals[i] + "</option>");
          }
        }

        callback();
      },
      error: function(err) {
        console.log(err);
      }
    });
  }

  function renderEnrichedTable(abundancesObj) {
    $("#analysis-container-cat1").hide();
    $("#analysis-container-cat2").hide();

    if ($.isEmptyObject(abundancesObj)) {
      return;
    }

    $('#stats-rows-cat1').empty();
    $('#stats-rows-cat2').empty();
    var cat1 = $("#pwVar1").val();
    var cat2 = $("#pwVar2").val();
    $("#cat1-present").text(cat1);
    $("#cat2-present").text(cat2);

    var diff1 = abundancesObj["diff1"];
    var diff2 = abundancesObj["diff2"];

    for (var i = 0; i < diff1.length; i++) {
      var r = '<tr>';
      r = r + '<td>' + diff1[i].t + '</td><td>' + diff1[i].c + '</td>';
      r = r + '<tr>';
      $('#stats-rows-cat1').append(r);
    }
    
    for (var i = 0; i < diff2.length; i++) {
      var r = '<tr>';
      r = r + '<td>' + diff2[i].t + '</td><td>' + diff2[i].c + '</td>';
      r = r + '<tr>';
      $('#stats-rows-cat2').append(r);
    }

    $("#analysis-container-cat1").fadeIn(250);
    $("#analysis-container-cat2").fadeIn(250);
  }


  function updateAnalysis() {
    showLoading();
    var level = taxonomyLevels[getTaxonomicLevel()];
    var taxonomy = $("#taxonomy-specific").val();
    if (taxonomy == null) {
      taxonomy = []
    }

    var catvar = $("#catvar").val();
    var enrichedthreshold = $("#enrichedthreshold").val();
    var pwVar1 = $("#pwVar1").val();
    var pwVar2 = $("#pwVar2").val();

    var data = {
      "pid": $("#project").val(),
      "level": level,
      // "taxonomy": taxonomy.join(","),
      "taxonomy": "All", // TODO: FIX
      "catvar": catvar,
      "enrichedthreshold": enrichedthreshold,
      "pwVar1": pwVar1,
      "pwVar2": pwVar2
    };

    $.ajax({
      type: "POST",
      url: "enriched_selection",
      data: data,
      success: function(result) {
        hideLoading();
        var abundancesObj = JSON.parse(result);
        renderEnrichedTable(abundancesObj);
      },
      error: function(err) {
        console.log(err)
      }
    });
  }
});