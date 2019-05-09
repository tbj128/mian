// ============================================================
// Fisher Exact JS Component
// ============================================================

//
// Global Components
//
var tableResults = [];
var expectedLoadFactor = 500;

//
// Initialization
//
initializeFields();
initializeComponent({
    hasCatVar: true,
    hasCatVarNoneOption: true
});
createSpecificListeners();

//
// Initializes fields based on the URL params
//
function initializeFields() {
    if (getParameterByName("pwVar1") !== null) {
        $("#pwVar1").val(getParameterByName("pwVar1"));
    }
    if (getParameterByName("pwVar2") !== null) {
        $("#pwVar2").val(getParameterByName("pwVar2"));
    }
    if (getParameterByName("minthreshold") !== null) {
        $("#minthreshold").val(getParameterByName("minthreshold"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    // Alter the second option so that the pairwise aren't both the same value
    $("#pwVar2 option:eq(1)").attr("selected", "selected");

    $("#catvar").change(function() {
        updatePWComparisonSidebar().then(function() {
            updateAnalysis();
        });
    });

    $("#minthreshold").change(function() {
        updateAnalysis();
    });

    $("#pwVar1").change(function() {
        updateAnalysis();
    });

    $("#pwVar2").change(function() {
        updateAnalysis();
    });

    $("#download-svg").click(function() {
        downloadCSV(tableResults);
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
        pid: $("#project").val(),
        catvar: $("#catvar").val()
    };

    return $.ajax({
        type: "GET",
        url: getSharedPrefixIfNeeded() + "/metadata_vals" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            hideLoading();
            $("#pwVar1").empty();
            $("#pwVar2").empty();
            var uniqueVals = JSON.parse(result);

            for (var i = 0; i < uniqueVals.length; i++) {
                $("#pwVar1").append(
                    "<option value='" + uniqueVals[i] + "'>" + uniqueVals[i] + "</option>"
                );
                if (i == 1) {
                    $("#pwVar2").append(
                        "<option value='" +
                        uniqueVals[i] +
                        "' selected>" +
                        uniqueVals[i] +
                        "</option>"
                    );
                } else {
                    $("#pwVar2").append(
                        "<option value='" +
                        uniqueVals[i] +
                        "'>" +
                        uniqueVals[i] +
                        "</option>"
                    );
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

    $("#stats-rows").empty();
    var statsArr = abundancesObj["results"];
    var hints = abundancesObj["hints"];
    var cat1 = abundancesObj["cat1"];
    var cat2 = abundancesObj["cat2"];
    $("#cat1-present").text(cat1);
    $("#cat1-tot").text(cat1);
    $("#cat2-present").text(cat2);
    $("#cat2-tot").text(cat2);


    tableResults = [];
    tableResults.push(["Taxonomic Group/OTU", "P-Value", "Q-Value", cat1 + " Present", cat1 + " Absent", cat2 + " Present", cat2 + " Absent"]);


    for (var i = 0; i < statsArr.length; i++) {
        var r = "<tr>";
        for (var j = 0; j < statsArr[i].length; j++) {
            if (j == 0) {
                // The last element in the array contains the genus hint
                if (hints[statsArr[i][j]] && hints[statsArr[i][j]] !== "") {
                    r = r + "<td><a href='" + shareToBoxplotLink(statsArr[i][j]) + "' target='_blank'>" + statsArr[i][j] + "</a> <small class='text-muted'>(" + hints[statsArr[i][j]] + ")</small></td>";
                } else {
                    r = r + "<td><a href='" + shareToBoxplotLink(statsArr[i][j]) + "' target='_blank'>" + statsArr[i][j] + "</a></td>";
                }
            } else {
                r = r + "<td>" + statsArr[i][j] + "</td>";
            }
        }
        r = r + "<tr>";
        $("#stats-rows").append(r);
        tableResults.push(statsArr[i]);
    }

    $("#stats-container").fadeIn(250);
}

function updateAnalysis() {
    showLoading(expectedLoadFactor);

    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var minthreshold = $("#minthreshold").val();
    var pwVar1 = $("#pwVar1").val();
    var pwVar2 = $("#pwVar2").val();

    if (catvar === "none") {
        loadNoCatvar();
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
        minthreshold: minthreshold,
        pwVar1: pwVar1,
        pwVar2: pwVar2
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/fisher_exact" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            var abundancesObj = JSON.parse(result);
            if (!$.isEmptyObject(abundancesObj["results"])) {
                loadSuccess();
                renderFisherTable(abundancesObj);
            } else {
                loadNoResults();
            }
        },
        error: function(err) {
            loadError();
            console.log(err);
        }
    });
}
