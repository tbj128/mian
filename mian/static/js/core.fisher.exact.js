// ============================================================
// Fisher Exact JS Component
// ============================================================

//
// Initialization
//
initializeComponent({
    hasCatVar: true,
    hasCatVarNoneOption: true,
});
createSpecificListeners();

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    // Alter the second option so that the pairwise aren't both the same value
    $('#pwVar2 option:eq(1)').attr('selected', 'selected');

    $("#catvar").change(function () {
      updatePWComparisonSidebar().then(function() {
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

//
// Analysis Specific Methods
//

function customCatVarValueLoading() {
    return updatePWComparisonSidebar();
}

function updatePWComparisonSidebar() {
    var data = {
      "pid": $("#project").val(),
      "catvar": $("#catvar").val(),
    };

    return $.ajax({
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
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var minthreshold = $("#minthreshold").val();
    var keepthreshold = $("#keepthreshold").val();
    var pwVar1 = $("#pwVar1").val();
    var pwVar2 = $("#pwVar2").val();

    if (catvar === "none") {
        $("#analysis-container").hide();
        hideLoading();
        hideNotifications();
        showNoCatvar();
        return;
    }

    var data = {
      "pid": $("#project").val(),
      "taxonomyFilterCount": getLowCountThreshold(),
      "taxonomyFilterPrevalence": getPrevalenceThreshold(),
      "taxonomyFilter": taxonomyFilter,
      "taxonomyFilterRole": taxonomyFilterRole,
      "taxonomyFilterVals": taxonomyFilterVals,
      "sampleFilter": sampleFilter,
      "sampleFilterRole": sampleFilterRole,
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
        hideNotifications();
        hideLoading();

        var abundancesObj = JSON.parse(result);
        if (!$.isEmptyObject(abundancesObj["results"])) {
            $("#analysis-container").show();
            renderFisherTable(abundancesObj);
        } else {
            $("#analysis-container").hide();
            showNoResults();
        }
      },
      error: function(err) {
        $("#analysis-container").hide();
        hideLoading();
        hideNotifications();
        showError();
        console.log(err);
      }
    });
}