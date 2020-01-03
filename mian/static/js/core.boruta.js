// ============================================================
// Boruta Feature Selection JS Component
// Feature Selection flow chart: http://proceedings.mlr.press/v10/liu10b/liu10b.pdf
// ============================================================

//
// Global Components
//
var tableResults = [];
var expectedLoadFactor = 500;
var cachedTrainingIndexes = null;
var cachedSelectedFeatures = null;

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
    if (getParameterByName("maxruns") !== null) {
        $("#maxruns").val(getParameterByName("maxruns"));
    }
    if (getParameterByName("pval") !== null) {
        $("#pval").val(getParameterByName("pval"));
    }
    if (getParameterByName("trainingProportion") !== null) {
        $("#trainingProportion").val(getParameterByName("trainingProportion"));
    }
    if (getParameterByName("fixTraining") !== null) {
        $("#fixTraining").val(getParameterByName("fixTraining"));

        if ($("#fixTraining").val() === "yes") {
            $("#trainingProportion").prop("readonly", true);
        } else {
            $("#trainingProportion").prop("readonly", false);
        }
    }
    if (getParameterByName("trainingIndexes") !== null) {
        cachedTrainingIndexes = JSON.parse(getParameterByName("trainingIndexes"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#catvar").change(function() {
        updateAnalysis();
    });

    $("#maxruns").change(function() {
        updateAnalysis();
    });

    $("#pval").change(function() {
        updateAnalysis();
    });

    $("#trainingProportion").change(function() {
        updateAnalysis();
    });

    $("#fixTraining").change(function() {

        if ($("#fixTraining").val() === "yes") {
            $("#trainingProportion").prop("readonly", true);
        } else {
            $("#trainingProportion").prop("readonly", false);
        }

        updateAnalysis();
    });

    $("#download-svg").click(function() {
        downloadCSV(tableResults);
    });

    $("#send-to-rf").click(function() {
        if (cachedTrainingIndexes != null) {
            window.open('/random_forest?pid=' + $("#project").val() + '&ref=boruta&trainingIndexes=' + JSON.stringify(cachedTrainingIndexes) + '&taxonomyFilter=' + taxonomyLevels[$("#taxonomy").val()] + '&taxonomyFilterRole=Include&taxonomyFilterVals=' + JSON.stringify(cachedSelectedFeatures), '_blank');
        }
    });

    $("#send-to-dnn").click(function() {
        if (cachedTrainingIndexes != null) {
            window.open('/deep_neural_network?pid=' + $("#project").val() + '&ref=boruta&trainingIndexes=' + JSON.stringify(cachedTrainingIndexes) + '&taxonomyFilter=' + taxonomyLevels[$("#taxonomy").val()] + '&taxonomyFilterRole=Include&taxonomyFilterVals=' + JSON.stringify(cachedSelectedFeatures) + '&expvar=' + $("#catvar").val(), '_blank');
        }
    });
}

//
// Analysis Specific Methods
//
function customLoading() {}

function renderBorutaTable(abundancesObj) {
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
    var trainingProportion = $("#trainingProportion").val();
    var fixTraining = $("#fixTraining").val();

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
        trainingProportion: trainingProportion,
        fixTraining: fixTraining,
        pval: pval,
        maxruns: maxruns,
        trainingIndexes: JSON.stringify(cachedTrainingIndexes != null ? cachedTrainingIndexes : []),
    };

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/boruta" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            var abundancesObj = JSON.parse(result);
            if (!$.isEmptyObject(abundancesObj["results"])) {
                cachedTrainingIndexes = [...abundancesObj["training_indexes"]];
                if (abundancesObj["results"]["Confirmed"]) {
                    cachedSelectedFeatures = [...abundancesObj["results"]["Confirmed"]];
                } else {
                    cachedSelectedFeatures = [];
                }

                loadSuccess();
                $("#send-to-container").show();
                renderBorutaTable(abundancesObj);

                // Hack to update the URL with the training indexes
                data["trainingIndexes"] = cachedTrainingIndexes;
                setGetParameters(data);
            } else {
                loadNoResults();
                $("#send-to-container").hide();
            }
        },
        error: function(err) {
            loadError();
            console.log(err);
            $("#send-to-container").hide();
        }
    });

    setGetParameters(data);
}
