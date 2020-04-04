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
var cachedTrainingIndexes = null;

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

    if (getParameterByName("trainingIndexes") !== null) {
        cachedTrainingIndexes = JSON.parse(getParameterByName("trainingIndexes"));
    }

    if (getParameterByName("rocFor") !== null) {
        $("#rocFor").val(getParameterByName("rocFor"));
    }

    if (getParameterByName("ref") !== null) {
        $("#referral-alert").show();
        $("#referer-name").text(getParameterByName("ref"));
    }

    var ctx = document.getElementById('canvas').getContext('2d');
    window.trainChart = new Chart(ctx, config);
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
        renderTrainingPlot();
        setGetParameters(getUpdateAnalysisData());
    });

    $("#blackout").click(function() {
        $("#blackout").hide();
    });

    $("#download-svg").click(function() {
        downloadCanvas("linear_regression", "canvas");
    });

    $("#save-to-notebook").click(function() {
        saveCanvasToNotebook("Linear Regression (" + $("#expvar").val() + ")", "Taxonomic Level: " + $("#taxonomy option:selected").text() + "\n" + "L1 Regularization Ratio: " + $("#mixingRatio option:selected").text() + "\n", "canvas");
    });
}

//
// Analysis Specific Methods
//
function customLoading() {}

function renderTrainingPlot() {
    if (cachedAbundancesObj == null) {
        return;
    }

    var colors = palette('cb-Accent', 2);
    config.data.datasets = [];
    config.data.datasets.push({
        label: "Training",
        backgroundColor: "#" + colors[0],
        borderColor: "#" + colors[0],
        data: [],
        fill: false,
        lineTension: 0,
        data: cachedAbundancesObj["scores_train"].map((val, i) => {
            return {
                x: i,
                y: val
            }
        }),
    });

    config.data.datasets.push({
        label: "Test",
        backgroundColor: "#" + colors[1],
        borderColor: "#" + colors[1],
        data: [],
        fill: false,
        lineTension: 0,
        data: cachedAbundancesObj["scores_test"].map((val, i) => {
            return {
                x: i,
                y: val
            }
        }),
    });

    window.trainChart.update();
}

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
        trainingIndexes: JSON.stringify(cachedTrainingIndexes != null ? cachedTrainingIndexes : []),
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

            if (cachedAbundancesObj["training_indexes"]) {
                cachedTrainingIndexes = cachedAbundancesObj["training_indexes"];
                data["trainingIndexes"] = cachedTrainingIndexes;
            } else {
                data["trainingIndexes"] = [];
            }
            // Hack to update the URL with the training indexes
            setGetParameters(data);

            loadSuccess();

            if ($("#crossValidate").val() === "full") {
                $("#train-mae").text("N/A");
                $("#train-mse").text("N/A");
                $("#cv-mae").text(`${abundancesObj["cv_mae"]} ± ${abundancesObj["cv_mae_std"]}`);
                $("#cv-mse").text(`${abundancesObj["cv_mse"]} ± ${abundancesObj["cv_mse_std"]}`);
                if (abundancesObj["test_mae"]) {
                    $("#test-mae").text(`${abundancesObj["test_mae"]}`);
                    $("#test-mse").text(`${abundancesObj["test_mse"]}`);
                } else {
                    $("#test-mae").text("N/A");
                    $("#test-mse").text("N/A");
                }
                $("#training-plot-container").hide();
            } else {
                $("#training-plot-container").show();
                renderTrainingPlot();

                $("#train-mae").text(`${abundancesObj["train_mae"]}`);
                $("#train-mse").text(`${abundancesObj["train_mse"]}`);
                $("#cv-mae").text("N/A");
                $("#cv-mse").text("N/A");
                if (abundancesObj["test_mae"]) {
                    $("#test-mae").text(`${abundancesObj["test_mae"]}`);
                    $("#test-mse").text(`${abundancesObj["test_mse"]}`);
                } else {
                    $("#test-mae").text("N/A");
                    $("#test-mse").text("N/A");
                }
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
