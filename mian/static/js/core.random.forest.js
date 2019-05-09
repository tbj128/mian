 // ============================================================
// Random Forest JS Component
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

    if (getParameterByName("method") !== null) {
        if (getParameterByName("method") === "boruta") {
            $("#boruta-params").show();
            $("#rf-params").hide();
        } else {
            $("#boruta-params").hide();
            $("#rf-params").show();
        }
    } else {
        $("#boruta-params").show();
        $("#rf-params").hide();
    }

    if (getParameterByName("numTrees") !== null) {
        $("#numTrees").val(getParameterByName("numTrees"));
    }
    if (getParameterByName("maxDepth") !== null) {
        $("#maxDepth").val(getParameterByName("maxDepth"));
    }

    if (getParameterByName("maxruns") !== null) {
        $("#maxruns").val(getParameterByName("maxruns"));
    }
    if (getParameterByName("pval") !== null) {
        $("#pval").val(getParameterByName("pval"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#catvar").change(function() {
        updateAnalysis();
    });

    $("#method").change(function() {
        updateAnalysis();

        if ($("#method").val() === "boruta") {
            $("#boruta-params").show();
            $("#rf-params").hide();
        } else {
            $("#boruta-params").hide();
            $("#rf-params").show();
        }
    });

    $("#numTrees").change(function() {
        updateAnalysis();
    });
    $("#maxDepth").change(function() {
        updateAnalysis();
    });

    $("#maxruns").change(function() {
        updateAnalysis();
    });
    $("#pval").change(function() {
        updateAnalysis();
    });

    $("#download-svg").click(function() {
        downloadCSV(tableResults);
    });
}

//
// Analysis Specific Methods
//
function customLoading() {}

function renderTable(abundancesObj) {
    $("#boruta-container").hide();
    $("#rf-container").show();

    if ($.isEmptyObject(abundancesObj)) {
        return;
    }

    $("#rf-stats-rows").empty();
    var statsArr = abundancesObj["results"];
    var hints = abundancesObj["hints"];

    tableResults = [];
    tableResults.push(["Taxonomy", "Importance"]);

    for (var i = 0; i < statsArr.length; i++) {
        var hint = "";
        if (hints[statsArr[i][0]] && hints[statsArr[i][0]] !== "") {
            hint = " <small class='text-muted'>(" + hints[statsArr[i][0]] + ")</small>";
        }
        var r =
            "<tr><td>" + statsArr[i][0] + hint + "</td><td>" + statsArr[i][1] + "</td></tr>";
        $("#rf-stats-rows").append(r);
        tableResults.push([statsArr[i][0], statsArr[i][1]]);
    }

    $("#cmd-run").text(abundancesObj["cmd"]);
}

function renderBorutaTable(abundancesObj) {
    $("#boruta-container").show();
    $("#rf-container").hide();

    if ($.isEmptyObject(abundancesObj)) {
        return;
    }

    tableResults = [];

    var $statsHeader = $("#boruta-stats-headers");
    var $statsRows = $("#boruta-stats-rows");
    $statsHeader.empty();
    $statsRows.empty();

    var stats = abundancesObj["results"];
    var hints = abundancesObj["hints"];

    var confirmedInfo = "These taxonomic groups/OTUs were selected to be important features at the selected p-value threshold."
    var tentativeInfo = "These taxonomic groups/OTUs were unable to be confirmed to be significant at the selected p-value threshold. You can try reducing the p-value threshold or increasing the max runs to further resolve these."
    var rejectedInfo = "These taxonomic groups/OTUs were not selected to be important features at the selected p-value threshold."

    var keys = [];
    $.each(stats, function(key, value) {
        var popupContent = "";
        if (key === "Tentative") {
            popupContent = tentativeInfo;
        } else if (key === "Confirmed") {
            popupContent = confirmedInfo;
        } else {
            popupContent = rejectedInfo;
        }
        var popover = '<i class="fa fa-info-circle" data-toggle="popover" data-title="' + key + '" data-content="' + popupContent + '" data-trigger="hover" data-placement="bottom"></i>';

        $statsHeader.append("<th>" + key + " (" + value.length + ") " + popover + "</th>");
        keys.push(key);
    });

    tableResults.push(keys);

    while (true) {
        var row = [];
        var empty = true;
        var newRow = "<tr>";
        for (var k = 0; k < keys.length; k++) {
            if (stats[keys[k]].length == 0) {
                newRow += "<td></td>";
                row.push("");
            } else {
                var head = stats[keys[k]].shift();
                var hint = "";
                if (hints[head] && hints[head] !== "") {
                    hint = " <small class='text-muted'>(" + hints[head] + ")</small>";
                }
                newRow += "<td><a href='" + shareToBoxplotLink(head) + "' target='_blank'>" + head + "</a>" + hint + "</td>";
                empty = false;
                row.push(head);
            }
        }
        if (empty) {
            break;
        } else {
            $("#boruta-stats-rows").append(newRow);
            tableResults.push(row);
        }
    }

    $('[data-toggle="popover"]').popover();
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
    var method = $("#method").val();
    var pval = $("#pval").val();
    var maxruns = $("#maxruns").val();
    var numTrees = $("#numTrees").val();
    var maxDepth = $("#maxDepth").val();

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
        method: method
    };

    if (method === "boruta") {
        data["pval"] = pval;
        data["maxruns"] = maxruns;

        $.ajax({
            type: "POST",
            url: getSharedPrefixIfNeeded() + "/boruta" + getSharedUserProjectSuffixIfNeeded(),
            data: data,
            success: function(result) {
                var abundancesObj = JSON.parse(result);
                if (!$.isEmptyObject(abundancesObj["results"])) {
                    loadSuccess()
                    renderBorutaTable(abundancesObj);
                } else {
                    loadNoResults();
                }
            },
            error: function(err) {
                loadError();
                console.log(err);
            }
        });
    } else {
        data["numTrees"] = numTrees;
        data["maxDepth"] = maxDepth;

        $.ajax({
            type: "POST",
            url: getSharedPrefixIfNeeded() + "/random_forest" + getSharedUserProjectSuffixIfNeeded(),
            data: data,
            success: function(result) {
                var abundancesObj = JSON.parse(result);
                if (!$.isEmptyObject(abundancesObj["results"])) {
                    loadSuccess();
                    renderTable(abundancesObj);
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

    setGetParameters(data);

}
