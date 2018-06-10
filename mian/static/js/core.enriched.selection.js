// ============================================================
// Boxplot JS Component
// ============================================================

//
// Initialization
//
initializeComponent({
    hasCatVar: true,
    hasCatVarNoneOption: false,
});
createSpecificListeners();

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    // Alter the second option so that the pairwise aren't both the same value
    $('#pwVar2 option:eq(1)').attr('selected', 'selected');

    $("#catvar").change(function () {
      updatePWComparisonSidebar(function() {
        updateAnalysis();
      });
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


//
// Analysis Specific Methods
//

function customLoading() {
    return updatePWComparisonSidebar();
}


function updatePWComparisonSidebar(callback) {
    var data = {
      "pid": $("#project").val(),
      "catvar": $("#catvar").val(),
    };

    return $.ajax({
      type: "GET",
      url: "metadata_vals",
      data: data,
      success: function(result) {
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

        if (callback) {
            callback();
        }
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

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var enrichedthreshold = $("#enrichedthreshold").val();
    var pwVar1 = $("#pwVar1").val();
    var pwVar2 = $("#pwVar2").val();

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
      "enrichedthreshold": enrichedthreshold,
      "pwVar1": pwVar1,
      "pwVar2": pwVar2
    };

    $.ajax({
      type: "POST",
      url: "enriched_selection",
      data: data,
      success: function(result) {
        $("#display-error").hide();
        hideLoading();
        $("#analysis-container").show();
        $("#stats-container").show();

        var abundancesObj = JSON.parse(result);
        renderEnrichedTable(abundancesObj);
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