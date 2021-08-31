// ============================================================
// Boruta Feature Selection JS Component
// Feature Selection flow chart: http://proceedings.mlr.press/v10/liu10b/liu10b.pdf
// ============================================================

//
// Global Components
//
var tableResults = [];
var expectedLoadFactor = 500;
var cachedSeed = null;
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
    if (getParameterByName("useTrainingSet") !== null) {
        $("#useTrainingSet").val(getParameterByName("useTrainingSet"));

        if ($("#useTrainingSet").val() === "yes") {
            $("#trainingProportionContainer").show();
        } else {
            $("#trainingProportion").val(1);
            $("#trainingProportionContainer").hide();
        }
    }
    if (getParameterByName("seed") !== null) {
        cachedSeed = getParameterByName("seed");
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

    $("#useTrainingSet").change(function() {

        if ($("#useTrainingSet").val() === "yes") {
            $("#trainingProportion").val(0.7);
            $("#trainingProportionContainer").show();
        } else {
            $("#trainingProportion").val(1);
            $("#trainingProportionContainer").hide();
        }

        updateAnalysis();
    });

    $("#download-svg").click(function() {
        downloadCSV(tableResults);
    });

    $("#save-to-notebook").click(function() {
        saveTableToNotebook("Boruta (" + $("#catvar").val() + ")", "Taxonomic Level: " + $("#taxonomy option:selected").text() + "\n", tableResults);
    });

    $("#send-to-lc").click(function() {
        if (cachedSeed != null) {
            var trainingProportion = $("#useTrainingSet").val() === "yes" ? $("#trainingProportion").val() : 0.7;
            window.open('/linear_classifier?pid=' + $("#project").val() + '&ref=Boruta&trainingProportion=' + trainingProportion + '&seed=' + cachedSeed + '&taxonomyFilter=' + getSelectedTaxFilter() + '&taxonomyFilterRole=Include&taxonomyFilterVals=' + JSON.stringify(cachedSelectedFeatures.map(f => f.split("; ")[f.split("; ").length - 1])) + '&catvar=' + $("#catvar").val(), '_blank');
        }
    });

    $("#send-to-rf").click(function() {
        if (cachedSeed != null) {
            var trainingProportion = $("#useTrainingSet").val() === "yes" ? $("#trainingProportion").val() : 0.7;
            window.open('/random_forest?pid=' + $("#project").val() + '&ref=Boruta&trainingProportion=' + trainingProportion + '&seed=' + cachedSeed + '&taxonomyFilter=' + getSelectedTaxFilter() + '&taxonomyFilterRole=Include&taxonomyFilterVals=' + JSON.stringify(cachedSelectedFeatures.map(f => f.split("; ")[f.split("; ").length - 1])) + '&catvar=' + $("#catvar").val(), '_blank');
        }
    });

    $("#send-to-dnn").click(function() {
        if (cachedSeed != null) {
            var trainingProportion = $("#useTrainingSet").val() === "yes" ? $("#trainingProportion").val() : 0.7;
            window.open('/deep_neural_network?pid=' + $("#project").val() + '&ref=Boruta&trainingProportion=' + trainingProportion + '&problemType=classification&seed=' + cachedSeed + '&taxonomyFilter=' + getSelectedTaxFilter() + '&taxonomyFilterRole=Include&taxonomyFilterVals=' + JSON.stringify(cachedSelectedFeatures.map(f => f.split("; ")[f.split("; ").length - 1])) + '&expvar=' + $("#catvar").val(), '_blank');
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
    if (!loaded) {
        return;
    }
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
    var useTrainingSet = $("#useTrainingSet").val();

    if (!catvar || catvar === "none") {
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
        useTrainingSet: useTrainingSet,
        pval: pval,
        maxruns: maxruns,
        seed: cachedSeed,
    };

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/boruta" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            var abundancesObj = JSON.parse(result);
            if (!$.isEmptyObject(abundancesObj["results"])) {
                cachedSeed = abundancesObj["seed"];
                if (abundancesObj["results"]["Confirmed"]) {
                    cachedSelectedFeatures = [...abundancesObj["results"]["Confirmed"]];
                } else {
                    cachedSelectedFeatures = [];
                }

                loadSuccess();
                $("#send-to-container").show();
                renderBorutaTable(abundancesObj);

                // Hack to update the URL with the training indexes
                data["seed"] = cachedSeed;
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
