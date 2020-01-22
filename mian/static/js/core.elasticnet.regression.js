// ============================================================
// Elastic Net Regression JS Component
// ============================================================

//
// Global Components
//
var tableResults = [];
var expVarToType = {};
var expectedLoadFactor = 500;
var cachedAbundancesObj = null;
var cachedTrainingIndexes = null;

//
// Initialization
//
var initialExpVar = getParameterByName("expvar");
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

    if (getParameterByName("mixingRatio") !== null) {
        $("#mixingRatio").val(getParameterByName("mixingRatio"));
    }

    if (getParameterByName("keep") !== null) {
        $("#keep").val(getParameterByName("keep"));
    }

    if (getParameterByName("maxIterations") !== null) {
        $("#maxIterations").val(getParameterByName("maxIterations"));
    }

    if (getParameterByName("fixTraining") !== null) {
        $("#fixTraining").val(getParameterByName("fixTraining"));

        if ($("#fixTraining").val() === "yes") {
            $("#trainingProportion").prop("readonly", true);
        } else {
            $("#trainingProportion").prop("readonly", false);
        }
    }

    if (getParameterByName("trainingProportion") !== null) {
        $("#trainingProportion").val(getParameterByName("trainingProportion"));
    }

    if (getParameterByName("trainingIndexes") !== null) {
        cachedTrainingIndexes = JSON.parse(getParameterByName("trainingIndexes"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#expvar").change(function() {
        updateAnalysis();
    });

    $("#lossFunction").change(function() {
        updateAnalysis();
    });

    $("#mixingRatio").change(function() {
        updateAnalysis();
    });

    $("#maxIterations").change(function() {
        updateAnalysis();
    });

    $("#trainingProportion").change(function() {
        updateAnalysis();
    });

    $("#keep").change(function() {
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

    $("#blackout").click(function() {
        $("#blackout").hide();
    });

    $("#download-svg").click(function() {
        downloadCSV(tableResults);
    });

    $("#save-to-notebook").click(function() {
        saveTableToNotebook("Elastic Net Regression (" + $("#expvar").val() + ")", "Taxonomic Level: " + $("#taxonomy option:selected").text() + "\n", tableResults);
    });

    $("#send-to-lr").click(function() {
        if (cachedTrainingIndexes != null) {
            window.open('/linear_regression?pid=' + $("#project").val() + '&ref=Elastic+Net+Regression&trainingIndexes=' + JSON.stringify(cachedTrainingIndexes) + '&taxonomyFilter=' + taxonomyLevels[$("#taxonomy").val()] + '&taxonomyFilterRole=Include&taxonomyFilterVals=' + JSON.stringify(cachedSelectedFeatures.map(f => f.split("; ")[f.split("; ").length - 1])) + '&expvar=' + $("#expvar").val(), '_blank');
        }
    });

    $("#send-to-dnn").click(function() {
        if (cachedTrainingIndexes != null) {
            window.open('/deep_neural_network?pid=' + $("#project").val() + '&ref=Elastic+Net+Regression&problemType=regression&trainingIndexes=' + JSON.stringify(cachedTrainingIndexes) + '&taxonomyFilter=' + taxonomyLevels[$("#taxonomy").val()] + '&taxonomyFilterRole=Include&taxonomyFilterVals=' + JSON.stringify(cachedSelectedFeatures.map(f => f.split("; ")[f.split("; ").length - 1])) + '&expvar=' + $("#expvar").val(), '_blank');
        }
    });
}

function renderTable(featureMap, hints) {
    cachedSelectedFeatures = featureMap["features"];
    tableResults = [["Selected Feature", "Absolute Feature Weight"]];
    featureMap["features"].map((feature, i) => {
        newRow = [feature, featureMap["weights"][i]];
        tableResults.push(newRow);
    });

    $("#analysis-container").empty();

    $("#analysis-container").append("<div><table class='table table-hover'><thead><tr><th scope='col'>Selected Feature</th><th scope='col'>Absolute Feature Weight</th></tr></thead><tbody id='elasticnet-rows'></tbody></table><hr /></div>");

    featureMap["features"].forEach((feature, i) => {
        var hint = "";
        if (hints[feature] && hints[feature] !== "") {
            hint = " <small class='text-muted'>(" + hints[feature] + ")</small>";
        }
        $("#elasticnet-rows").append("<tr><td><a href='" + shareToBoxplotLink(feature) + "' target='_blank'>" + feature + "</a>" + hint + "</td><td>" + featureMap["weights"][i] + "</td></tr>");
    });
}

//
// Analysis Specific Methods
//
function customLoading() {}

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

    var expvar = $("#expvar").val();
    var trainingProportion = $("#trainingProportion").val();
    var fixTraining = $("#fixTraining").val();

    if (expvar === "None") {
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
        expvar: expvar,
        mixingRatio: $("#mixingRatio").val(),
        maxIterations: $("#maxIterations").val(),
        keep: $("#keep").val(),
        fixTraining: fixTraining,
        trainingProportion: trainingProportion,
        trainingIndexes: JSON.stringify(cachedTrainingIndexes != null ? cachedTrainingIndexes : []),
    };

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/elastic_net_selection_regression" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            var abundancesObj = JSON.parse(result);
            cachedAbundancesObj = abundancesObj;
            cachedTrainingIndexes = cachedAbundancesObj["training_indexes"];

            // Hack to update the URL with the training indexes
            data["trainingIndexes"] = cachedTrainingIndexes;
            setGetParameters(data);

            if (abundancesObj["training_indexes"].length > 0) {
                loadSuccess();
                $("#send-to-container").show();
                renderTable(abundancesObj["feature_map"], abundancesObj["hints"]);
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

function customCatVarCallback(result) {
    result.forEach(function(obj) {
        expVarToType[obj.name] = obj.type;
    });
    var allHeaders = ["None"].concat(result.map(function(obj) { return obj.name; }));

    //
    // Renders the experimental variable
    //
    $("#expvar").empty();
    allHeaders.forEach(function(obj) {
        if (obj === "None" || expVarToType[obj] === "both" || expVarToType[obj] === "numeric") {
            $("#expvar").append(
                '<option value="' + obj + '">' + obj + "</option>"
            );
        }
    });
    if (initialExpVar) {
        $("#expvar").val(initialExpVar);
        initialExpVar = null;
    }
}
