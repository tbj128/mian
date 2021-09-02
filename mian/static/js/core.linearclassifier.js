// ============================================================
// Linear Classifier JS Component
// ============================================================

//
// Global Components
//
var tableResults = [];
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
                    labelString: 'Accuracy'
                }
            }]
        },
    }
};

var configRoc = {
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

    if (getParameterByName("ref") !== null) {
        $("#referral-alert").show();
        $("#referer-name").text(getParameterByName("ref"));
    }

    var ctxRoc = document.getElementById('canvas-roc').getContext('2d');
    window.rocChart = new Chart(ctxRoc, configRoc);
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

    $("#blackout").click(function() {
        $("#blackout").hide();
    });

    $("#download-svg").click(function() {
        downloadCSV(tableResults);
        downloadCanvas("linear_classifier", "canvas-roc");
    });

    $("#save-to-notebook").click(function() {
        saveTableToNotebook("Linear Classifier (" + $("#catvar").val() + ")", "Taxonomic Level: " + $("#taxonomy option:selected").text() + "\n" + "Loss Function: " + $("#lossFunction option:selected").text() + "\n" + "L1 Regularization Ratio: " + $("#mixingRatio").val() + "\n", tableResults);
    });
}

function renderRocPlot() {
    if (cachedAbundancesObj == null) {
        return;
    }

    $("#auc-rows").empty();

    var trainOrTestKey = ($("#crossValidate").val() === "full") ? "train_class_to_roc" : "test_class_to_roc";
    var curveType = "Test Data";
    if ($("#crossValidate").val() === "full") {
        curveType = "Cross-Validated Full Data";
    }
    $("#roc-curve-type").text(curveType);

    tableResults = [];
    if ($("#crossValidate").val() === "full") {
        tableResults.push(["Label", "Cross-Validation AUROC"]);
    } else {
        tableResults.push(["Label", "Training AUROC", "Validation AUROC", "Test AUROC"]);
        $("#train-n").text(cachedAbundancesObj["train_size"][0]);
        $("#val-n").text(cachedAbundancesObj["val_size"][0]);
        $("#test-n").text(cachedAbundancesObj["test_size"][0]);
    }

    var colors = palette('cb-Accent', Object.keys(cachedAbundancesObj[trainOrTestKey]).length);
    configRoc.data.datasets = [];
    var i = 0;
    for (var k in cachedAbundancesObj[trainOrTestKey]) {
        if ($("#crossValidate").val() === "full") {
            tableResults.push([k, cachedAbundancesObj[trainOrTestKey][k]["auc"] + " ± " + cachedAbundancesObj[trainOrTestKey][k]["auc_std"]]);
            $("#auc-rows").append("<tr><td>" + k + "</td><td>N/A</td><td>" + cachedAbundancesObj[trainOrTestKey][k]["auc"] + " ± " + cachedAbundancesObj[trainOrTestKey][k]["auc_std"] + "</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td></tr>");
        } else {
            var trainAuc = cachedAbundancesObj["train_class_to_roc"][k] ? cachedAbundancesObj["train_class_to_roc"][k]["auc"] : "N/A";
            var valAuc = cachedAbundancesObj["val_class_to_roc"][k] ? cachedAbundancesObj["val_class_to_roc"][k]["auc"] : "N/A";
            var testAuc = cachedAbundancesObj["test_class_to_roc"][k] ? cachedAbundancesObj["test_class_to_roc"][k]["auc"] : "N/A";
            var trainPos = cachedAbundancesObj["train_class_to_roc"][k] ? cachedAbundancesObj["train_class_to_roc"][k]["num_positives"] : "N/A";
            var valPos = cachedAbundancesObj["val_class_to_roc"][k] ? cachedAbundancesObj["val_class_to_roc"][k]["num_positives"] : "N/A";
            var testPos = cachedAbundancesObj["test_class_to_roc"][k] ? cachedAbundancesObj["test_class_to_roc"][k]["num_positives"] : "N/A";
            tableResults.push([k, trainAuc, valAuc, testAuc]);
            $("#auc-rows").append("<tr><td>" + k + "</td><td>" + trainPos + "</td><td>" + trainAuc + "</td><td>" + valPos + "</td><td>" + valAuc+ "</td><td>" + testPos + "</td><td>" + testAuc + "</td></tr>");
        }
        configRoc.data.datasets.push({
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
        seed: cachedSeed
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

    if (!$("#catvar").val() || $("#catvar").val() === "none") {
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

            if (cachedAbundancesObj["seed"]) {
                cachedSeed = cachedAbundancesObj["seed"];
                data["seed"] = cachedSeed;
            } else {
                data["seed"] = "";
            }
            // Hack to update the URL with the training indexes
            setGetParameters(data);

            loadSuccess();
            renderRocPlot();
        },
        error: function(err) {
            loadError();
            console.log(err);
        }
    });

    setGetParameters(data);
}
