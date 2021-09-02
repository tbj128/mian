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
var cachedSeed = null;

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
var initialExpVar = getParameterByName("expvar");
function initializeFields() {
    if (getParameterByName("epochs") !== null) {
        $("#epochs").val(getParameterByName("epochs"));
    }

    if (getParameterByName("lr") !== null) {
        $("#lr").val(getParameterByName("lr"));
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

    if (getParameterByName("dnnModel") !== null) {
        dnnModel = JSON.parse(getParameterByName("dnnModel"));
    } else {
        dnnModel = [
            {type: "dense", units: 10, dropoutfrac: 0, key: 1},
            {type: "dropout", units: 0, dropoutfrac: 0.5, key: 2},
            {type: "dense", units: 10, dropoutfrac: 0, key: 3},
            {type: "dropout", units: 0, dropoutfrac: 0.5, key: 4},
        ];
    }

    if (getParameterByName("problemType") !== null) {
        $("#problemType").val(getParameterByName("problemType"));
    }

    if (getParameterByName("seed") !== null) {
        cachedSeed = getParameterByName("seed");
    }

    renderDnnDesigner(dnnModel);
    renderDnnSidebar(dnnModel);

    var ctx = document.getElementById('canvas').getContext('2d');
    window.dnnChart = new Chart(ctx, config);

    var ctxRoc = document.getElementById('canvas-roc').getContext('2d');
    window.rocChart = new Chart(ctxRoc, configRoc);
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#expvar").change(function() {
        if (expVarToType[$(this).val()] === "numeric") {
            $("#problemType").val("regression");
        } else {
            $("#problemType").val("classification");
        }
        updateAnalysis();
    });

    $("#epochs").change(function() {
        updateAnalysis();
    });

    $("#lr").change(function() {
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
        renderDnnSidebar(dnnModel);
        $("#dnn-box").hide();
        $("#blackout").hide();
        updateAnalysis();
    });

    $("#download-svg").click(function() {
        downloadCanvas("deep_learning", "canvas");
        downloadCSV(tableResults);
    });

    $("#save-to-notebook").click(function() {
        saveTableToNotebook("Deep Learning (" + $("#expvar").val() + ")", "Taxonomic Level: " + $("#taxonomy option:selected").text() + "\n", tableResults);
    });

    //
    // DNN Model Designer
    //
    $("#dnn-add-layer").click(function() {
        var now = Date.now();
        var newLayer = {
            type: "dense",
            units: 0,
            dropoutfrac: 0,
            key: now,
        };
        addDnnLayer(newLayer, now);
        dnnModel.push(newLayer);
    });
    $(document).on('click', '.dnn-remove-layer', function() {
        var spliceKey = $(this).data("layer");
        $("#dnn-layer-" + spliceKey).remove();
        dnnModel.forEach(function(item, index, object) {
            if (item["key"] === spliceKey) {
                object.splice(index, 1);
            }
        });
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
    dnnModel.map((layer) => {
        addDnnLayer(layer, layer["key"]);
    });
}

function addDnnLayer(layer, i) {
    $("#dnn-layers").append(`
        <div class="row" id="dnn-layer-${i}" style="border-bottom: 1px solid #ececec; margin-bottom: 20px; padding-bottom: 20px;">
            <div class="col-md-3">
                <label class="control-label">Layer Type</label>
                <select id="dnn-layer-type-${i}" class="form-control dnn-layer-type" data-layer="${i}">
                    ${layer.type === "dense" ? '<option value="dense" selected>Dense</option>' : '<option value="dense">Dense</option>'}
                    ${layer.type === "dropout" ? '<option value="dropout" selected>Dropout</option>' : '<option value="dropout">Dropout</option>'}
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

    $("#auc-rows").empty();
    $("#mae-mse-rows").empty();
    if ($("#problemType").val() === "classification") {
        $("#train-n").text(cachedAbundancesObj["train_size"][0]);
        $("#val-n").text(cachedAbundancesObj["val_size"][0]);
        $("#test-n").text(cachedAbundancesObj["test_size"][0]);

        var colors = palette('cb-Accent', Object.keys(cachedAbundancesObj["train_class_to_roc"]).length);
        configRoc.data.datasets = [];

        var i = 0;
        for (var k in cachedAbundancesObj["train_class_to_roc"]) {
            var trainAuc = cachedAbundancesObj["train_class_to_roc"][k] ? cachedAbundancesObj["train_class_to_roc"][k]["auc"] : "N/A";
            var valAuc = cachedAbundancesObj["val_class_to_roc"][k] ? cachedAbundancesObj["val_class_to_roc"][k]["auc"] : "N/A";
            var testAuc = cachedAbundancesObj["test_class_to_roc"][k] ? cachedAbundancesObj["test_class_to_roc"][k]["auc"] : "N/A";
            var trainPos = cachedAbundancesObj["train_class_to_roc"][k] ? cachedAbundancesObj["train_class_to_roc"][k]["num_positives"] : "N/A";
            var valPos = cachedAbundancesObj["val_class_to_roc"][k] ? cachedAbundancesObj["val_class_to_roc"][k]["num_positives"] : "N/A";
            var testPos = cachedAbundancesObj["test_class_to_roc"][k] ? cachedAbundancesObj["test_class_to_roc"][k]["num_positives"] : "N/A";

            tableResults.push([k, trainAuc, valAuc, testAuc]);
            $("#auc-rows").append("<tr><td>" + k + "</td><td>" + trainPos + "</td><td>" + trainAuc + "</td><td>" + valPos + "</td><td>" + valAuc+ "</td><td>" + testPos + "</td><td>" + testAuc + "</td></tr>");

            if (cachedAbundancesObj["test_class_to_roc"][k]) {
                configRoc.data.datasets.push({
                    label: k,
                    backgroundColor: "#" + colors[i],
                    borderColor: "#" + colors[i],
                    data: [],
                    fill: false,
                    lineTension: 0,
                    data: cachedAbundancesObj["test_class_to_roc"][k]["tpr"].map((val, i) => {
                        return {
                            x: cachedAbundancesObj["test_class_to_roc"][k]["fpr"][i],
                            y: cachedAbundancesObj["test_class_to_roc"][k]["tpr"][i]
                        }
                    }),
                });
            }
            i += 1
        }

        window.rocChart.update();

        $("#auc-table").show();
        $("#mae-mse-table").hide();
    } else {
        tableResults.push(["Training", cachedAbundancesObj["train_mae"], cachedAbundancesObj["train_mse"]])
        tableResults.push(["Validation", cachedAbundancesObj["val_mae"], cachedAbundancesObj["val_mse"]])
        tableResults.push(["Test", cachedAbundancesObj["test_mae"], cachedAbundancesObj["test_mse"]])

        $("#mae-mse-rows").append("<tr><td>Training (n=" + cachedAbundancesObj["train_size"][0] + ")</td><td>" + cachedAbundancesObj["train_mae"] + "</td><td>" + cachedAbundancesObj["train_mse"] + "</td></tr>");
        $("#mae-mse-rows").append("<tr><td>Validation (n=" + cachedAbundancesObj["val_size"][0] + ")</td><td>" + cachedAbundancesObj["val_mae"] + "</td><td>" + cachedAbundancesObj["val_mse"] + "</td></tr>");
        $("#mae-mse-rows").append("<tr><td>Test (n=" + cachedAbundancesObj["test_size"][0] + ")</td><td>" + cachedAbundancesObj["test_mae"] + "</td><td>" + cachedAbundancesObj["test_mse"] + "</td></tr>");

        $("#auc-table").hide();
        $("#mae-mse-table").show();
    }

    config.options.scales.yAxes[0].scaleLabel.labelString = "Loss";
    config.data.datasets.forEach(function(dataset) {
        if (dataset.label === "Training") {
            dataset.data = cachedAbundancesObj["train_loss"].map((val, i) => {
                return {
                    x: i + 1,
                    y: val
                }
            });
        } else {
            dataset.data = cachedAbundancesObj["val_loss"].map((val, i) => {
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
    var epochs = $("#epochs").val();
    var lr = $("#lr").val();
    var problemType = $("#problemType").val();
    var trainingProportion = $("#trainingProportion").val();
    var fixTraining = $("#fixTraining").val();

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
        epochs: epochs,
        lr: lr,
        problemType: problemType,
        dnnModel: JSON.stringify(dnnModel),
        fixTraining: fixTraining,
        trainingProportion: trainingProportion,
        seed: cachedSeed
    };

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/deep_neural_network" + getSharedUserProjectSuffixIfNeeded(),
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

            setGetParameters(data);

            if (abundancesObj["num_samples"] < 1000) {
                $("#low-sample-warning").show();
            } else {
                $("#low-sample-warning").hide();
            }

            if (problemType === "classification") {
                $("#canvas-roc").show();
                if (abundancesObj["train_loss"].length > 0) {
                    loadSuccess();
                    renderTrainingPlot(abundancesObj);
                } else {
                    loadNoResults();
                }
            } else {
                $("#canvas-roc").hide();
                if (abundancesObj["train_loss"].length > 0) {
                    loadSuccess();
                    renderTrainingPlot(abundancesObj);
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

