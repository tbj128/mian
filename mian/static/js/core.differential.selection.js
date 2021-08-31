// ============================================================
// Differential Selection JS Component
// ============================================================

//
// Global Components
//
var tableResults = [];
var differentialDataTable;
var expectedLoadFactor = 500;
var cachedSeed = null;
var cachedSelectedFeatures = null;

//
// Initialization
//
initializeFields();
initializeComponent({
    hasCatVar: true,
    hasCatVarNoneOption: false
});
createSpecificListeners();

//
// Initializes fields based on the URL params
//
var initialPwVar1 = getParameterByName("pwVar1");
var initialPwVar2 = getParameterByName("pwVar2");
function initializeFields() {
    if (getParameterByName("pvalthreshold") !== null) {
        $("#pvalthreshold").val(getParameterByName("pvalthreshold"));
    }
    if (getParameterByName("type") !== null) {
        $("#type").val(getParameterByName("type"));
    }
    if (getParameterByName("trainingProportion") !== null) {
        $("#trainingProportion").val(getParameterByName("trainingProportion"));
    }
    if (getParameterByName("seed") !== null) {
        cachedSeed = getParameterByName("seed");
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
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    // Alter the second option so that the pairwise aren't both the same value
    $("#pwVar2 option:eq(1)").attr("selected", "selected");

    $("#catvar").change(function() {
        updatePWComparisonSidebar(function() {
            updateAnalysis();
        });
    });

    $("#pvalthreshold").change(function() {
        updateAnalysis();
    });

    $("#pwVar1").change(function() {
        updateAnalysis();
    });

    $("#pwVar2").change(function() {
        updateAnalysis();
    });

    $("#type").change(function() {
        updateAnalysis();
    });

    $("#trainingProportion").change(function() {
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

    $("#download-svg").click(function() {
        downloadCSV(tableResults);
    });

    $("#save-to-notebook").click(function() {
        saveTableToNotebook("Differential Selection (" + $("#catvar").val() + ")", "Taxonomic Level: " + $("#taxonomy option:selected").text() + "\n", tableResults);
    });

    $("#send-to-lc").click(function() {
        if (cachedSeed != null) {
            var trainingProportion = $("#useTrainingSet").val() === "yes" ? $("#trainingProportion").val() : 0.7;
            window.open('/linear_classifier?pid=' + $("#project").val() + '&ref=Fisher+Exact&trainingProportion=' + trainingProportion + '&seed=' + cachedSeed + '&taxonomyFilter=' + getSelectedTaxFilter() + '&taxonomyFilterRole=Include&taxonomyFilterVals=' + JSON.stringify(cachedSelectedFeatures.map(f => f.split("; ")[f.split("; ").length - 1])) + '&catvar=' + $("#catvar").val(), '_blank');
        }
    });

    $("#send-to-rf").click(function() {
        if (cachedSeed != null) {
            var trainingProportion = $("#useTrainingSet").val() === "yes" ? $("#trainingProportion").val() : 0.7;
            window.open('/random_forest?pid=' + $("#project").val() + '&ref=Fisher+Exact&trainingProportion=' + trainingProportion + '&seed=' + cachedSeed + '&taxonomyFilter=' + getSelectedTaxFilter() + '&taxonomyFilterRole=Include&taxonomyFilterVals=' + JSON.stringify(cachedSelectedFeatures.map(f => f.split("; ")[f.split("; ").length - 1])) + '&catvar=' + $("#catvar").val(), '_blank');
        }
    });

    $("#send-to-dnn").click(function() {
        if (cachedSeed != null) {
            var trainingProportion = $("#useTrainingSet").val() === "yes" ? $("#trainingProportion").val() : 0.7;
            window.open('/deep_neural_network?pid=' + $("#project").val() + '&ref=Fisher+Exact&trainingProportion=' + trainingProportion + '&problemType=classification&seed=' + cachedSeed + '&taxonomyFilter=' + getSelectedTaxFilter() + '&taxonomyFilterRole=Include&taxonomyFilterVals=' + JSON.stringify(cachedSelectedFeatures.map(f => f.split("; ")[f.split("; ").length - 1])) + '&expvar=' + $("#catvar").val(), '_blank');
        }
    });
}

//
// Analysis Specific Methods
//

function customCatVarValueLoading() {
    return updatePWComparisonSidebar();
}

function updatePWComparisonSidebar(callback) {
    var data = {
        pid: $("#project").val(),
        catvar: $("#catvar").val()
    };

    return $.ajax({
        type: "GET",
        url: getSharedPrefixIfNeeded() + "/metadata_vals" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            $("#pwVar1").empty();
            $("#pwVar2").empty();
            var uniqueVals = JSON.parse(result);

            for (var i = 0; i < uniqueVals.length; i++) {
                if (initialPwVar1 && initialPwVar1 == uniqueVals[i]) {
                    $("#pwVar1").append(
                        "<option value='" + uniqueVals[i] + "' selected>" + uniqueVals[i] + "</option>"
                    );
                    initialPwVar1 = null;
                } else {
                    $("#pwVar1").append(
                        "<option value='" + uniqueVals[i] + "'>" + uniqueVals[i] + "</option>"
                    );
                }


                if (initialPwVar2 && initialPwVar2 == uniqueVals[i]) {
                    $("#pwVar2").append(
                        "<option value='" +
                        uniqueVals[i] +
                        "' selected>" +
                        uniqueVals[i] +
                        "</option>"
                    );
                } else if (i == 1) {
                    $("#pwVar2").append(
                        "<option value='" +
                        uniqueVals[i] +
                        "' selected>" +
                        uniqueVals[i] +
                        "</option>"
                    );
                } else {
                    $("#pwVar2").append(
                        "<option value='" +
                        uniqueVals[i] +
                        "'>" +
                        uniqueVals[i] +
                        "</option>"
                    );
                }
            }

            if (callback) {
                callback();
            }
        },
        error: function(err) {
            console.log(err);
        }
    });
}

function renderDifferentialTable(abundancesObj) {
    if (differentialDataTable) {
        differentialDataTable.clear();
    } else {
        differentialDataTable = $("#differential-table").DataTable({
            order: [
                [2, "asc"]
            ],
            columns: [{
                data: "otu",
                fnCreatedCell: function (nTd, sData, oData, iRow, iCol) {
                    var toRender = "<a href='"+ shareToBoxplotLink(oData.otu) + "' target='_blank'>" + oData.otu + "</a>";
                    if (oData.hint && oData.hint !== "") {
                        toRender += " <small class='text-muted'>(" + oData.hint + ")</small>";
                    }
                    $(nTd).html(toRender);
                }
            }, {
                data: "pval"
            }, {
                data: "qval"
            }]
        });
    }

    tableResults = [];
    tableResults.push(["otu", "pval", "qval"]);

    var differentials = abundancesObj["differentials"];
    differentialDataTable.rows.add(differentials);
    differentialDataTable.draw();

    tableResults = tableResults.concat(differentials);
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

    var catvar = $("#catvar").val();
    var pvalthreshold = $("#pvalthreshold").val();
    var pwVar1 = $("#pwVar1").val();
    var pwVar2 = $("#pwVar2").val();
    var type = $("#type").val();

    if (!catvar || catvar === "none") {
        loadNoCatvar();
        return;
    }

    var trainingProportion = $("#trainingProportion").val();
    var useTrainingSet = $("#useTrainingSet").val();

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
        pvalthreshold: pvalthreshold,
        pwVar1: pwVar1,
        pwVar2: pwVar2,
        type: type,
        trainingProportion: trainingProportion,
        useTrainingSet: useTrainingSet,
        seed: cachedSeed,
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/differential_selection" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            var abundancesObj = JSON.parse(result.replace(/\bNaN\b/g, "null"));
            if (abundancesObj["differentials"].length > 0) {
                loadSuccess();
                $("#send-to-container").show();
                renderDifferentialTable(abundancesObj);
                cachedSeed = abundancesObj["seed"];
                cachedSelectedFeatures = abundancesObj["differentials"].map(d => d["otu"]);
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
}
