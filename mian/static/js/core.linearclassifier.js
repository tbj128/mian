// ============================================================
// Linear Classifier JS Component
// ============================================================

//
// Global Components
//
var tableResults = [];
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
                    labelString: 'False-Positive Rate'
                }
            }],
            yAxes: [{
                display: true,
                scaleLabel: {
                    display: true,
                    labelString: 'True-Positive Rate'
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
function initializeFields() {

    if (getParameterByName("lossFunction") !== null) {
        $("#lossFunction").val(getParameterByName("lossFunction"));
    }

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
        } else {
            $("#trainingConfig").show();
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

    if (getParameterByName("rocFor") !== null) {
        $("#rocFor").val(getParameterByName("rocFor"));
    }

    if (getParameterByName("trainingIndexes") !== null) {
        cachedTrainingIndexes = JSON.parse(getParameterByName("trainingIndexes"));
    }

    if (getParameterByName("ref") !== null) {
        $("#referral-alert").show();
        $("#referer-name").text(getParameterByName("ref"));
    }

    var ctx = document.getElementById('canvas').getContext('2d');
    window.rocChart = new Chart(ctx, config);
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

    $("#crossValidate").change(function() {
        if ($("#crossValidate").val() === "full") {
            $("#trainingConfig").hide();
        } else {
            $("#trainingConfig").show();
        }
        updateAnalysis();
    });

    $("#crossValidateFolds").change(function() {
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
        downloadCanvas("linear_classifier", "canvas");
    });

    $("#save-to-notebook").click(function() {
        saveCanvasToNotebook("Linear Classifier (" + $("#catvar").val() + ")", "Taxonomic Level: " + $("#taxonomy option:selected").text() + "\n" + "Loss Function: " + $("#lossFunction option:selected").text() + "\n" + "L1 Regularization Ratio: " + $("#mixingRatio option:selected").text() + "\n", "canvas");
    });
}

function renderTrainingPlot() {
    if (cachedAbundancesObj == null) {
        return;
    }

    $("#auc-rows").empty();

    var trainOrTestKey = ($("#rocFor").val() === "train" || $("#crossValidate").val() === "full") ? "train_class_to_roc" : "test_class_to_roc";
    var curveType = "Test Data";
    if ($("#crossValidate").val() === "full") {
        curveType = "Cross-Validated Full Data";
    } else if ($("#rocFor").val() === "train") {
        curveType = "Cross-Validated Training Data";
    }
    $("#roc-curve-type").text(curveType);

    var colors = palette('cb-Accent', Object.keys(cachedAbundancesObj[trainOrTestKey]).length);
    config.data.datasets = [];
    var i = 0;
    for (var k in cachedAbundancesObj[trainOrTestKey]) {
        if ($("#rocFor").val() === "train" || $("#crossValidate").val() === "full") {
            $("#auc-rows").append("<tr><td>" + k + "</td><td>" + cachedAbundancesObj[trainOrTestKey][k]["auc"] + " ± " + cachedAbundancesObj[trainOrTestKey][k]["auc_std"] + "</td></tr>");
        } else {
            $("#auc-rows").append("<tr><td>" + k + "</td><td>" + cachedAbundancesObj[trainOrTestKey][k]["auc"] + "</td></tr>");
        }
        config.data.datasets.push({
            label: k,
            backgroundColor: "#" + colors[i],
            borderColor: "#" + colors[i],
            data: [],
            fill: false,
            lineTension: 0,
            data: cachedAbundancesObj[trainOrTestKey][k]["tpr"].map((val, i) => {
                return {
                    x: cachedAbundancesObj[trainOrTestKey][k]["fpr"][i],
                    y: cachedAbundancesObj[trainOrTestKey][k]["tpr"][i]
                }
            }),
        });
        i += 1
    }

    window.rocChart.update();
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

    var catvar = $("#catvar").val();
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
        catvar: catvar,
        crossValidate: $("#crossValidate").val(),
        crossValidateFolds: $("#crossValidateFolds").val(),
        lossFunction: $("#lossFunction").val(),
        mixingRatio: $("#mixingRatio").val(),
        maxIterations: $("#maxIterations").val(),
        fixTraining: fixTraining,
        trainingProportion: trainingProportion,
        rocFor: $("#rocFor").val(),
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

    if (catvar === "none") {
        loadNoCatvar();
        return;
    }

    var data = getUpdateAnalysisData();

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/linear_classifier" + getSharedUserProjectSuffixIfNeeded(),
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
            $("#cv-accuracy").text(`${abundancesObj["cv_accuracy"]} ± ${abundancesObj["cv_accuracy_std"]}`);
            $("#test-accuracy").text(`${abundancesObj["test_accuracy"] ? abundancesObj["test_accuracy"] : "N/A"}`);

            renderTrainingPlot();
        },
        error: function(err) {
            loadError();
            console.log(err);
        }
    });

    setGetParameters(data);
}