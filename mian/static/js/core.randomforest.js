// ============================================================
// Random Forest JS Component
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
    if (getParameterByName("numTrees") !== null) {
        $("#numTrees").val(getParameterByName("numTrees"));
    }

    if (getParameterByName("maxDepth") !== null) {
        $("#maxDepth").val(getParameterByName("maxDepth"));
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

    $("#maxDepth").change(function() {
        updateAnalysis();
    });

    $("#numTrees").change(function() {
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
        downloadCanvas("random_forest", "canvas");
    });

    $("#save-to-notebook").click(function() {
        saveCanvasToNotebook("Random Forest (" + $("#catvar").val() + ")", "Taxonomic Level: " + $("#taxonomy option:selected").text() + "\n", "canvas");
    });
}

function renderTrainingPlot() {
    if (cachedAbundancesObj == null) {
        return;
    }

    $("#auc-rows").empty();

    var colors = palette('cb-Accent', Object.keys(cachedAbundancesObj["class_to_roc"]).length);
    config.data.datasets = [];
    var i = 0;
    for (var k in cachedAbundancesObj["class_to_roc"]) {
        $("#auc-rows").append("<tr><td>" + k + "</td><td>" + cachedAbundancesObj["class_to_roc"][k]["auc"] + "</td></tr>");
        config.data.datasets.push({
            label: k,
            backgroundColor: "#" + colors[i],
            borderColor: "#" + colors[i],
            data: [],
            fill: false,
            lineTension: 0,
            data: cachedAbundancesObj["class_to_roc"][k]["tpr"].map((val, i) => {
                return {
                    x: cachedAbundancesObj["class_to_roc"][k]["fpr"][i],
                    y: cachedAbundancesObj["class_to_roc"][k]["tpr"][i]
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
        numTrees: $("#numTrees").val(),
        maxDepth: $("#maxDepth").val(),
        fixTraining: fixTraining,
        trainingProportion: trainingProportion,
        trainingIndexes: JSON.stringify(cachedTrainingIndexes != null ? cachedTrainingIndexes : []),
    };
    if (getParameterByName("ref") != null) {
        data["ref"] = getParameterByName("ref");
    }

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/random_forest" + getSharedUserProjectSuffixIfNeeded(),
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
                $("#oob-error").text(abundancesObj["oob_error"]);
                $("#accuracy").text(abundancesObj["accuracy"]);
                renderTrainingPlot();
            } else {
                loadNoResults();
            }
        },
        error: function(err) {
            loadError();
            console.log(err);
        }
    });

    setGetParameters(data);
}
