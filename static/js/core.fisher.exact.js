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
      $.when(updateTaxonomicLevel(true, function() {}), updateCatVar()).done(function(a1, a2) {
        updatePWComparisonSidebar(function() {
          updateAnalysis();
        });
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
      updateTaxonomicLevel(false, function() {
        updateAnalysis();
      });
    });

    $("#taxonomy-specific").change(function () {
      updateAnalysis();
    });

    $("#catvar").change(function () {
      updatePWComparisonSidebar(function() {
        updateAnalysis();
      });
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

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var minthreshold = $("#minthreshold").val();
    var keepthreshold = $("#keepthreshold").val();
    var pwVar1 = $("#pwVar1").val();
    var pwVar2 = $("#pwVar2").val();

    var data = {
      "pid": $("#project").val(),
      "taxonomyFilter": taxonomyFilter,
      "taxonomyFilterVals": taxonomyFilterVals,
      "sampleFilter": sampleFilter,
      "sampleFilterVals": sampleFilterVals,
      "level": level,
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