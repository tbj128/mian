// ============================================================
// Elastic Net Classification JS Component
// ============================================================

//
// Global Components
//
var tableResults = [];
var expectedLoadFactor = 500;
var cachedAbundancesObj = null;
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

    if (getParameterByName("lossFunction") !== null) {
        $("#lossFunction").val(getParameterByName("lossFunction"));
    }

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
    $("#catvar").change(function() {
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
        saveTableToNotebook("Elastic Net Classification (" + $("#catvar").val() + ")", "Taxonomic Level: " + $("#taxonomy option:selected").text() + "\n", tableResults);
    });

    $("#analysis-container").on('click', '.send-to-lc', function() {
        if (cachedSeed != null) {
            var trainingProportion = $("#useTrainingSet").val() === "yes" ? $("#trainingProportion").val() : 0.7;
            window.open('/linear_classifier?pid=' + $("#project").val() + '&ref=Elastic+Net+Classificatio&trainingProportion=' + trainingProportion + '&seed=' + cachedSeed + '&taxonomyFilter=' + getSelectedTaxFilter() + '&taxonomyFilterRole=Include&taxonomyFilterVals=' + JSON.stringify(cachedSelectedFeatures[$(this).data("key")]["features"].map(f => f.split("; ")[f.split("; ").length - 1])) + '&catvar=' + $("#catvar").val(), '_blank');
        }
    });

    $("#analysis-container").on('click', '.send-to-rf', function() {
        if (cachedSeed != null) {
            var trainingProportion = $("#useTrainingSet").val() === "yes" ? $("#trainingProportion").val() : 0.7;
            window.open('/random_forest?pid=' + $("#project").val() + '&ref=Elastic+Net+Classification&trainingProportion=' + trainingProportion + '&seed=' + cachedSeed + '&taxonomyFilter=' + getSelectedTaxFilter() + '&taxonomyFilterRole=Include&taxonomyFilterVals=' + JSON.stringify(cachedSelectedFeatures[$(this).data("key")]["features"].map(f => f.split("; ")[f.split("; ").length - 1])) + '&catvar=' + $("#catvar").val(), '_blank');
        }
    });

    $("#analysis-container").on('click', '.send-to-dnn', function() {
        if (cachedSeed != null) {
            var trainingProportion = $("#useTrainingSet").val() === "yes" ? $("#trainingProportion").val() : 0.7;
            window.open('/deep_neural_network?pid=' + $("#project").val() + '&ref=Elastic+Net+Classification&trainingProportion=' + trainingProportion + '&problemType=classification&seed=' + cachedSeed + '&taxonomyFilter=' + getSelectedTaxFilter() + '&taxonomyFilterRole=Include&taxonomyFilterVals=' + JSON.stringify(cachedSelectedFeatures[$(this).data("key")]["features"].map(f => f.split("; ")[f.split("; ").length - 1])) + '&expvar=' + $("#catvar").val(), '_blank');
        }
    });
}

function renderTable(featureMap, hints) {
    tableResults = [["Selected Feature", "Absolute Feature Weight"]];
    for (var key in featureMap) {
        tableResults.push([key]);
        featureMap[key]["features"].map((feature, i) => {
            newRow = [feature, featureMap[key]["weights"][i]];
            tableResults.push(newRow);
        });
    }

    $("#analysis-container").empty();

    var k = 0;
    for (var key in featureMap) {
        var sendToCode = `
            <div id="send-to-container">
                <div class="row">
                    <div class="col-md-12">
                        <h4>Train and test selected features with...</h4>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12">
                        <button class="btn btn-default send-to-lc" type="button" data-key="${key}">Linear Classifier</button>
                        <button class="btn btn-default send-to-rf" type="button" data-key="${key}">Random Forest</button>
                        <button class="btn btn-default send-to-dnn" type="button" data-key="${key}">Deep Learning</button>
                    </div>
                </div>
                <hr style="margin-bottom: 12px" />
            </div>
        `;
        $("#analysis-container").append("<div><h3>" + key + "</h3>" + sendToCode + "<table class='table table-hover'><thead><tr><th scope='col'>Selected Feature</th><th scope='col'>Absolute Feature Weight</th></tr></thead><tbody id='elasticnet-rows-" + k + "'></tbody></table><hr /></div>");

        featureMap[key]["features"].forEach((feature, i) => {
            var hint = "";
            if (hints[feature] && hints[feature] !== "") {
                hint = " <small class='text-muted'>(" + hints[feature] + ")</small>";
            }
            $("#elasticnet-rows-" + k).append("<tr><td><a href='" + shareToBoxplotLink(feature) + "' target='_blank'>" + feature + "</a>" + hint + "</td><td>" + featureMap[key]["weights"][i] + "</td></tr>");
        });
        k++;
    }
}

//
// Analysis Specific Methods
//
function customLoading() {}

function updateAnalysis() {
    if (!loaded) {
        return;
    }
    $("#send-to-container").hide();
    showLoading(expectedLoadFactor);

    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
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
        lossFunction: $("#lossFunction").val(),
        mixingRatio: $("#mixingRatio").val(),
        maxIterations: $("#maxIterations").val(),
        keep: $("#keep").val(),
        useTrainingSet: useTrainingSet,
        trainingProportion: trainingProportion,
        seed: cachedSeed,
    };

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/elastic_net_selection_classification" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            var abundancesObj = JSON.parse(result);
            cachedAbundancesObj = abundancesObj;
            cachedSeed = abundancesObj["seed"];
            cachedSelectedFeatures = abundancesObj["feature_map"];

            // Hack to update the URL with the training indexes
            data["seed"] = cachedSeed;
            setGetParameters(data);

            if (abundancesObj["timeout"]) {
                loadError("This can occur if your data set is very large. Consider using a file with fewer OTUs or samples. <a href='#'>Learn more here.</a>", "Maximum Running Time Exceeded");
                $("#send-to-container").hide();
            }
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
