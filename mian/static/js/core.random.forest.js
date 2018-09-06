// ============================================================
// Fisher Exact JS Component
// ============================================================

//
// Initialization
//
initializeComponent({
  hasCatVar: true,
  hasCatVarNoneOption: true
});
createSpecificListeners();

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
  $("#catvar").change(function() {
    updateAnalysis();
  });
  $("#numTrees").change(function() {
    updateAnalysis();
  });
  $("#maxDepth").change(function() {
    updateAnalysis();
  });
}

//
// Analysis Specific Methods
//
function customLoading() {}

function renderTable(abundancesObj) {
  $("#stats-container").hide();

  if ($.isEmptyObject(abundancesObj)) {
    return;
  }

  $("#stats-rows").empty();
  var statsArr = abundancesObj["results"];

  for (var i = 0; i < statsArr.length; i++) {
    var r =
      "<tr><td>" + statsArr[i][0] + "</td><td>" + statsArr[i][1] + "</td></tr>";
    $("#stats-rows").append(r);
  }

  $("#cmd-run").text(abundancesObj["cmd"]);

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
  var numTrees = $("#numTrees").val();
  var maxDepth = $("#maxDepth").val();

  if (catvar === "none") {
    $("#analysis-container").hide();
    hideLoading();
    hideNotifications();
    showNoCatvar();
    return;
  }

  var data = {
    pid: $("#project").val(),
    taxonomyFilterCount: getLowCountThreshold(),
    taxonomyFilterPrevalence: getPrevalenceThreshold(),
    taxonomyFilter: taxonomyFilter,
    taxonomyFilterRole: taxonomyFilterRole,
    taxonomyFilterVals: taxonomyFilterVals,
    sampleFilter: sampleFilter,
    sampleFilterRole: sampleFilterRole,
    sampleFilterVals: sampleFilterVals,
    level: level,
    catvar: catvar,
    numTrees: numTrees,
    maxDepth: maxDepth
  };

  $.ajax({
    type: "POST",
    url: "random_forest",
    data: data,
    success: function(result) {
      hideNotifications();
      hideLoading();

      var abundancesObj = JSON.parse(result);
      if (!$.isEmptyObject(abundancesObj["results"])) {
        $("#analysis-container").show();
        renderTable(abundancesObj);
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
