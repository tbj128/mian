// ============================================================
// Deep Learning JS Component
// ============================================================

//
// Global Components
//
var tableResults = [];
var expectedLoadFactor = 500;
var expVarToType = {};
var dnnModel = [];
var cachedAbundancesObj = null;
var cachedTrainingIndexes = null;

window.chartColors = {
	red: 'rgb(255, 99, 132)',
	orange: 'rgb(255, 159, 64)',
	yellow: 'rgb(255, 205, 86)',
	green: 'rgb(75, 192, 192)',
	blue: 'rgb(54, 162, 235)',
	purple: 'rgb(153, 102, 255)',
	grey: 'rgb(201, 203, 207)'
};
var config = {
    type: 'line',
    data: {
        datasets: [{
            label: 'Training',
            backgroundColor: window.chartColors.red,
            borderColor: window.chartColors.red,
            data: [],
            fill: false,
            lineTension: 0,
        }, {
            label: 'Validation',
            fill: false,
            backgroundColor: window.chartColors.blue,
            borderColor: window.chartColors.blue,
            data: [],
            lineTension: 0,
        }]
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
                    labelString: ''
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
    if (getParameterByName("epochs") !== null) {
        $("#epochs").val(getParameterByName("epochs"));
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

    if (getParameterByName("validationProportion") !== null) {
        $("#validationProportion").val(getParameterByName("validationProportion"));
    }

    if (getParameterByName("regressionMeasure") !== null) {
        $("#regressionMeasure").val(getParameterByName("regressionMeasure"));
    }

    if (getParameterByName("classificationMeasure") !== null) {
        $("#classificationMeasure").val(getParameterByName("classificationMeasure"));
    }

    if (getParameterByName("dnnModel") !== null) {
        dnnModel = JSON.parse(getParameterByName("dnnModel"));
    } else {
        dnnModel = [
            {type: "dense", units: 10, dropoutfrac: 0},
            {type: "dropout", units: 0, dropoutfrac: 0.5},
            {type: "dense", units: 10, dropoutfrac: 0},
            {type: "dropout", units: 0, dropoutfrac: 0.5},
        ];
    }

    if (getParameterByName("problemType") !== null) {
        $("#problemType").val(getParameterByName("problemType"));
        if (getParameterByName("problemType") === "classification") {
            $("#regressionMeasureContainer").hide();
            $("#classificationMeasureContainer").show();
        } else {
            $("#regressionMeasureContainer").show();
            $("#classificationMeasureContainer").hide();
        }
    }

    if (getParameterByName("trainingIndexes") !== null) {
        cachedTrainingIndexes = JSON.parse(getParameterByName("trainingIndexes"));
    }

    renderDnnDesigner(dnnModel);
    renderDnnSidebar(dnnModel);

    var ctx = document.getElementById('canvas').getContext('2d');
    window.dnnChart = new Chart(ctx, config);
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#expvar").change(function() {
        if (expVarToType[$(this).val()] === "numeric") {
            $("#problemType").val("regression");
            $("#regressionMeasureContainer").show();
            $("#classificationMeasureContainer").hide();
        } else {
            $("#problemType").val("classification");
            $("#regressionMeasureContainer").hide();
            $("#classificationMeasureContainer").show();
        }
        updateAnalysis();
    });

    $("#epochs").change(function() {
        updateAnalysis();
    });

    $("#validationProportion").change(function() {
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

    $("#problemType").change(function() {
        if ($(this).val() === "classification") {
            $("#regressionMeasureContainer").hide();
            $("#classificationMeasureContainer").show();
        } else {
            $("#regressionMeasureContainer").show();
            $("#classificationMeasureContainer").hide();
        }
        updateAnalysis();
    });

    $("#regressionMeasure").change(function() {
        renderTrainingPlot();

        if (classificationMeasure === "mae") {
            $("#test-error-measure").text("Test Mean Absolute Error");
            $("#test-error-measure-val").text(abundancesObj["test_mae"]);
        } else {
            $("#test-error-measure").text("Test Mean Squared Error");
            $("#test-error-measure-val").text(abundancesObj["test_mse"]);
        }

        updateAnalysis();
    });

    $("#classificationMeasure").change(function() {
        renderTrainingPlot();

        if (classificationMeasure === "accuracy") {
            $("#test-error-measure").text("Test Accuracy");
            $("#test-error-measure-val").text(abundancesObj["test_accuracy"]);
        } else {
            $("#test-error-measure").text("Test Loss");
            $("#test-error-measure-val").text(abundancesObj["test_loss"]);
        }

        updateAnalysis();
    });

    $("#dnn-edit").click(function() {
        $("#dnn-box").show();
        $("#blackout").show();
    });

    $("#dnn-cancel").click(function() {
        $("#dnn-box").hide();
        $("#blackout").hide();
    });

    $("#blackout").click(function() {
        $("#dnn-box").hide();
        $("#blackout").hide();
    });

    $("#download-svg").click(function() {
        downloadCanvas("deep_learning", "canvas");
    });

    $("#save-to-notebook").click(function() {
        saveCanvasToNotebook("Deep Learning (" + $("#expvar").val() + ")", "Taxonomic Level: " + $("#taxonomy option:selected").text() + "\n", "canvas");
    });

    //
    // DNN Model Designer
    //
    $("#dnn-add-layer").click(function() {
        var newLayer = {
            type: "dense",
            units: 0,
            dropoutfrac: 0
        };
        addDnnLayer(newLayer, dnnModel.length);
        dnnModel.push(newLayer);
    });
    $(document).on('click', '.dnn-remove-layer', function() {
        $("#dnn-layer-" + $(this).data("layer")).remove();
        dnnModel = dnnModel.splice($(this).data("layer"), 1);
    });
    $(document).on('change', '.dnn-layer-type', function() {
        if ($(this).val() === "dense") {
            $("#dnn-layer-type-dense-" + $(this).data("layer")).show();
            $("#dnn-layer-type-dropout-" + $(this).data("layer")).hide();
            dnnModel[$(this).data("layer")].type = "dense";
        } else {
            $("#dnn-layer-type-dense-" + $(this).data("layer")).hide();
            $("#dnn-layer-type-dropout-" + $(this).data("layer")).show();
            dnnModel[$(this).data("layer")].type = "dropout";
        }
    });
    $(document).on('change', '.dnn-layer-units', function() {
        dnnModel[$(this).data("layer")].units = $(this).val();
    });
    $(document).on('change', '.dnn-layer-dropout-frac', function() {
        dnnModel[$(this).data("layer")].dropoutfrac = $(this).val();
    });
    $("#dnn-save").click(function() {
        renderDnnSidebar(dnnModel);
        $("#dnn-box").hide();
        $("#blackout").hide();
        updateAnalysis();
    });
}

//
// Analysis Specific Methods
//
function customLoading() {}

function renderDnnSidebar(dnnModel) {
    $("#editor-layers").empty();
    dnnModel.map((layer, i) => {
        if (layer.type === "dense") {
            $("#editor-layers").append(`<li><strong>Layer ${i + 1}: </strong>Dense (${layer.units} units)</li>`);
        } else {
            $("#editor-layers").append(`<li><strong>Layer ${i + 1}: </strong>Dropout (${layer.dropoutfrac} fraction)</li>`);
        }
    });
}

function renderDnnDesigner(dnnModel) {
    dnnModel.map((layer, i) => {
        addDnnLayer(layer, i);
    });
}

function addDnnLayer(layer, i) {
    $("#dnn-layers").append(`
        <div class="row" id="dnn-layer-${i}" style="border-bottom: 1px solid #ececec; margin-bottom: 20px; padding-bottom: 20px;">
            <div class="col-md-3">
                <label class="control-label">Layer Type</label>
                <select id="dnn-layer-type-${i}" class="form-control dnn-layer-type" data-layer="${i}">
                    <option value="dense">Dense</option>
                    <option value="dropout">Dropout</option>
                </select>
            </div>
            <div id="dnn-layer-type-dense-${i}" class="col-md-3" style="${layer.type !== 'dense' && 'display: none;'}">
                <label class="control-label">Hidden Units</label>
                <input data-layer="${i}" class="form-control dnn-layer-units" type="number" placeholder="Number of units" min="1" max="1000" step="10" value="${layer.units}" />
            </div>
            <div id="dnn-layer-type-dropout-${i}" class="col-md-3" style="${layer.type !== 'dropout' && 'display: none;'}">
                <label class="control-label">Dropout Fraction</label>
                <input data-layer="${i}" class="form-control dnn-layer-dropout-frac" type="number" placeholder="Number of units" min="0" max="1" step="0.1" value="${layer.dropoutfrac}" />
            </div>
            <div class="col-md-6 text-right">
                <button class="dnn-remove-layer btn btn-default" data-layer="${i}" type="button" style="margin-top: 25px;">Remove Layer</button>
            </div>
        </div>
    `);
}

function renderTrainingPlot() {
    if (cachedAbundancesObj == null) {
        return;
    }

    var dataKey = null;
    if ($("#problemType").val() === "classification") {
        if ($("#classificationMeasure").val() === "accuracy") {
            config.options.scales.yAxes[0].scaleLabel.labelString = "Accuracy";
            dataKey = "accuracy";
        } else {
            config.options.scales.yAxes[0].scaleLabel.labelString = "Cross-Entropy Loss";
            dataKey = "loss";
        }
    } else {
        if ($("#regressionMeasure").val() === "mse") {
            config.options.scales.yAxes[0].scaleLabel.labelString = "Mean Squared Error";
            dataKey = "mse";
        } else {
            config.options.scales.yAxes[0].scaleLabel.labelString = "Mean Absolute Error";
            dataKey = "mae";
        }
    }
    config.data.datasets.forEach(function(dataset) {
        if (dataset.label === "Training") {
            dataset.data = cachedAbundancesObj[dataKey].map((val, i) => {
                return {
                    x: i + 1,
                    y: val
                }
            });
        } else {
            dataset.data = cachedAbundancesObj["val_" + dataKey].map((val, i) => {
                return {
                    x: i + 1,
                    y: val
                }
            });
        }
    });

    window.dnnChart.update();
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

    var expvar = $("#expvar").val();
    var epochs = $("#epochs").val();
    var problemType = $("#problemType").val();
    var regressionMeasure = $("#regressionMeasure").val();
    var classificationMeasure = $("#classificationMeasure").val();
    var trainingProportion = $("#trainingProportion").val();
    var validationProportion = $("#validationProportion").val();
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
        epochs: epochs,
        problemType: problemType,
        classificationMeasure: classificationMeasure,
        regressionMeasure: regressionMeasure,
        dnnModel: JSON.stringify(dnnModel),
        fixTraining: fixTraining,
        trainingProportion: trainingProportion,
        validationProportion: validationProportion,
        trainingIndexes: JSON.stringify(cachedTrainingIndexes != null ? cachedTrainingIndexes : []),
    };

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/deep_neural_network" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            var abundancesObj = JSON.parse(result);
            cachedAbundancesObj = abundancesObj;
            cachedTrainingIndexes = cachedAbundancesObj["training_indexes"];

            // Hack to update the URL with the training indexes
            data["trainingIndexes"] = cachedTrainingIndexes;
            setGetParameters(data);

            if (abundancesObj["num_samples"] < 1000) {
                $("#low-sample-warning").show();
            } else {
                $("#low-sample-warning").hide();
            }

            if (problemType === "classification") {
                if (abundancesObj["accuracy"].length > 0) {
                    loadSuccess();
                    renderTrainingPlot(abundancesObj);

                    if (classificationMeasure === "accuracy") {
                        $("#test-error-measure").text("Test Accuracy");
                        $("#test-error-measure-val").text(abundancesObj["test_accuracy"]);
                    } else {
                        $("#test-error-measure").text("Test Loss");
                        $("#test-error-measure-val").text(abundancesObj["test_loss"]);
                    }
                } else {
                    loadNoResults();
                }
            } else {
                if (abundancesObj["mae"].length > 0) {
                    loadSuccess();
                    renderTrainingPlot(abundancesObj);

                    if (classificationMeasure === "mae") {
                        $("#test-error-measure").text("Test Mean Absolute Error");
                        $("#test-error-measure-val").text(abundancesObj["test_mae"]);
                    } else {
                        $("#test-error-measure").text("Test Mean Squared Error");
                        $("#test-error-measure-val").text(abundancesObj["test_mse"]);
                    }
                } else {
                    loadNoResults();
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
        $("#expvar").append(
            '<option value="' + obj + '">' + obj + "</option>"
        );
    });
    if (initialExpVar) {
        $("#expvar").val(initialExpVar);
        initialExpVar = null;
    }
}

