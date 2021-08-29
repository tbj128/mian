// ============================================================
// Linear Regression JS Component
// ============================================================

//
// Global Components
//
var tableResults = [];
var expVarToType = {};
var expectedLoadFactor = 500;
var cachedAbundancesObj = null;
var cachedSeed = null;

var config = {
    type: 'line',
    data: {
        datasets: []
    },
    options: {
        responsive: true,
        title: {
            display: false,
            text: ''
        },
        tooltips: {
            mode: 'index',
            intersect: false,
        },
        hover: {
            mode: 'nearest',
            intersect: true
        },
        scales: {
            xAxes: [{
                type: 'linear',
                position: 'bottom',
                scaleLabel: {
                    display: true,
                    labelString: 'Epochs'
                }
            }],
            yAxes: [{
                display: true,
                scaleLabel: {
                    display: true,
                    labelString: 'Mean Absolute Error'
                }
            }]
        },
    }
};

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
var initialExpVar = getParameterByName("expvar");
function initializeFields() {
    if (getParameterByName("mixingRatio") !== null) {
        $("#mixingRatio").val(getParameterByName("mixingRatio"));
    }

    if (getParameterByName("maxIterations") !== null) {
        $("#maxIterations").val(getParameterByName("maxIterations"));
    }

    if (getParameterByName("crossValidate") !== null) {
        $("#crossValidate").val(getParameterByName("crossValidate"));
        if ($("#crossValidate").val() === "full") {
            $("#trainingConfig").hide();
            $("#cvFolds").show();
        } else {
            $("#trainingConfig").show();
            $("#cvFolds").hide();
        }
    }

    if (getParameterByName("crossValidateFolds") !== null) {
        $("#crossValidateFolds").val(getParameterByName("crossValidateFolds"));
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

    if (getParameterByName("seed") !== null) {
        cachedSeed = getParameterByName("seed");
    }

    if (getParameterByName("rocFor") !== null) {
        $("#rocFor").val(getParameterByName("rocFor"));
    }

    if (getParameterByName("ref") !== null) {
        $("#referral-alert").show();
        $("#referer-name").text(getParameterByName("ref"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#expvar").change(function() {
        updateAnalysis();
    });

    $("#mixingRatio").change(function() {
        updateAnalysis();
    });

    $("#crossValidate").change(function() {
        if ($("#crossValidate").val() === "full") {
            $("#trainingConfig").hide();
            $("#cvFolds").show();
        } else {
            $("#trainingConfig").show();
            $("#cvFolds").hide();
        }
        updateAnalysis();
    });

    $("#crossValidateFolds").change(function() {
        updateAnalysis();
    });

    $("#maxIterations").change(function() {
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

    $("#rocFor").change(function() {
        setGetParameters(getUpdateAnalysisData());
    });

    $("#blackout").click(function() {
        $("#blackout").hide();
    });

    $("#download-svg").click(function() {
        downloadCSV(tableResults);
    });

    $("#save-to-notebook").click(function() {
        saveTableToNotebook("Linear Regression (" + $("#expvar").val() + ")", "Taxonomic Level: " + $("#taxonomy option:selected").text() + "\n" + "L1 Regularization Ratio: " + $("#mixingRatio").val() + "\n", tableResults);
    });
}

//
// Analysis Specific Methods
//
function customLoading() {}

function getUpdateAnalysisData() {

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
        crossValidate: $("#crossValidate").val(),
        crossValidateFolds: $("#crossValidateFolds").val(),
        mixingRatio: $("#mixingRatio").val(),
        maxIterations: $("#maxIterations").val(),
        fixTraining: fixTraining,
        trainingProportion: trainingProportion,
        seed: cachedSeed,
    };
    if (getParameterByName("ref") != null) {
        data["ref"] = getParameterByName("ref");
    }

    return data;
}


function updateAnalysis() {
    if (!loaded) {
        return;
    }
    showLoading(expectedLoadFactor);

    if (!$("#expvar").val() || $("#expvar").val() === "None") {
        loadNoCatvar();
        return;
    }

    var data = getUpdateAnalysisData();

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/linear_regression" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            var abundancesObj = JSON.parse(result);
            cachedAbundancesObj = abundancesObj;

            if (cachedAbundancesObj["seed"]) {
                cachedSeed = cachedAbundancesObj["seed"];
                data["seed"] = cachedSeed;
            } else {
                data["seed"] = "";
            }
            // Hack to update the URL with the training indexes
            setGetParameters(data);

            loadSuccess();

            if ($("#crossValidate").val() === "full") {
                $("#cv-mae").text(`${abundancesObj["cv_mae"]} ± ${abundancesObj["cv_mae_std"]}`);
                $("#cv-mse").text(`${abundancesObj["cv_mse"]} ± ${abundancesObj["cv_mse_std"]}`);
                $("#cv-row").show();
                $("#training-row").hide();
                $("#val-row").hide();
                $("#test-row").hide();

                tableResults = [];
                tableResults.push(["Dataset", "Mean Absolute Error", "Mean Squared Error"]);
                tableResults.push(["Cross-Validation", `${abundancesObj["cv_mae"]} ± ${abundancesObj["cv_mae_std"]}`, `${abundancesObj["cv_mse"]} ± ${abundancesObj["cv_mse_std"]}`]);
            } else {
                $("#cv-mae").text("N/A");
                $("#cv-mse").text("N/A");
                if (abundancesObj["train_mae"]) {
                    $("#train-mae").text(`${abundancesObj["train_mae"]}`);
                    $("#train-mse").text(`${abundancesObj["train_mse"]}`);
                } else {
                    $("#train-mae").text("N/A");
                    $("#train-mse").text("N/A");
                }
                if (abundancesObj["val_mae"]) {
                    $("#val-mae").text(`${abundancesObj["val_mae"]}`);
                    $("#val-mse").text(`${abundancesObj["val_mse"]}`);
                } else {
                    $("#val-mae").text("N/A");
                    $("#val-mse").text("N/A");
                }
                if (abundancesObj["test_mae"]) {
                    $("#test-mae").text(`${abundancesObj["test_mae"]}`);
                    $("#test-mse").text(`${abundancesObj["test_mse"]}`);
                } else {
                    $("#test-mae").text("N/A");
                    $("#test-mse").text("N/A");
                }
                $("#cv-row").hide();
                $("#training-row").show();
                $("#val-row").show();
                $("#test-row").show();

                tableResults = [];
                tableResults.push(["Dataset", "Mean Absolute Error", "Mean Squared Error"]);
                tableResults.push(["Training", abundancesObj["train_mae"], abundancesObj["train_mse"]]);
                tableResults.push(["Validation", abundancesObj["val_mae"], abundancesObj["val_mse"]]);
                tableResults.push(["Test", abundancesObj["test_mae"], abundancesObj["test_mse"]]);
            }
        },
        error: function(err) {
            loadError();
            console.log(err);
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
        if (expVarToType[obj] === "both" || expVarToType[obj] === "numeric") {
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
