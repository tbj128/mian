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
var cachedSeed = null;

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

    if (getParameterByName("useTrainingSet") !== null) {
        $("#useTrainingSet").val(getParameterByName("useTrainingSet"));

        if ($("#useTrainingSet").val() === "yes") {
            $("#trainingProportionContainer").show();
        } else {
            $("#trainingProportion").val(1);
            $("#trainingProportionContainer").hide();
        }
    }

    if (getParameterByName("trainingProportion") !== null) {
        $("#trainingProportion").val(getParameterByName("trainingProportion"));
    }

    if (getParameterByName("seed") !== null) {
        cachedSeed = getParameterByName("seed");
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
        if (cachedSeed != null) {
            var trainingProportion = $("#useTrainingSet").val() === "yes" ? $("#trainingProportion").val() : 0.7;
            window.open('/linear_regression?pid=' + $("#project").val() + '&ref=Elastic+Net+Regression&trainingProportion=' + trainingProportion + '&seed=' + cachedSeed + '&taxonomyFilter=' + getSelectedTaxFilter() + '&taxonomyFilterRole=Include&taxonomyFilterVals=' + JSON.stringify(cachedSelectedFeatures.map(f => f.split("; ")[f.split("; ").length - 1])) + '&expvar=' + $("#expvar").val(), '_blank');
        }
    });

    $("#send-to-dnn").click(function() {
        if (cachedSeed != null) {
            var trainingProportion = $("#useTrainingSet").val() === "yes" ? $("#trainingProportion").val() : 0.7;
            window.open('/deep_neural_network?pid=' + $("#project").val() + '&ref=Elastic+Net+Regression&trainingProportion=' + trainingProportion + '&problemType=regression&seed=' + cachedSeed + '&taxonomyFilter=' + getSelectedTaxFilter() + '&taxonomyFilterRole=Include&taxonomyFilterVals=' + JSON.stringify(cachedSelectedFeatures.map(f => f.split("; ")[f.split("; ").length - 1])) + '&expvar=' + $("#expvar").val(), '_blank');
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
    var useTrainingSet = $("#useTrainingSet").val();

    if (!expvar || expvar === "None") {
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
        useTrainingSet: useTrainingSet,
        trainingProportion: trainingProportion,
        seed: cachedSeed,
    };

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/elastic_net_selection_regression" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            var abundancesObj = JSON.parse(result);
            cachedAbundancesObj = abundancesObj;
            cachedSeed = abundancesObj["seed"];

            // Hack to update the URL with the training indexes
            data["seed"] = cachedSeed;
            setGetParameters(data);

            if (Object.keys(abundancesObj["feature_map"]).length > 0) {
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
