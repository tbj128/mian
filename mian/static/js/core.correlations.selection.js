// ============================================================
// Correlations Selection JS Component
// ============================================================

//
// Global Components
//
var tableResults = [];
var correlationDataTable;
var expectedLoadFactor = 500;
var cachedTrainingIndexes = null;
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
var initialExpVar = getParameterByName("expvar");
var initialGenes = getParameterByName("genes");
function initializeFields() {
    if (getParameterByName("select") !== null) {
        $("#select").val(getParameterByName("select"));
    }
    if (getParameterByName("against") !== null) {
        $("#against").val(getParameterByName("against"));
    }
    if ($("#against").val() === "metadata") {
        showNumericalVariableContainer(1);
    } else if ($("#against").val() === "gene") {
        showGeneInputContainer(1);
    } else if ($("#against").val() === "alpha") {
        showAlphaInputContainer(1);
    } else {
        showSpecificTaxonomyContainer(1);
    }
    if (getParameterByName("trainingProportion") !== null) {
        $("#trainingProportion").val(getParameterByName("trainingProportion"));
    }
    if (getParameterByName("fixTraining") !== null) {
        $("#fixTraining").val(getParameterByName("fixTraining"));

        if ($("#fixTraining").val() === "yes") {
            $("#trainingProportion").prop("readonly", true);
        } else {
            $("#trainingProportion").prop("readonly", false);
        }
    }
    if (getParameterByName("trainingIndexes") !== null) {
        cachedTrainingIndexes = JSON.parse(getParameterByName("trainingIndexes"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#select").change(function() {
        updateAnalysis();
    });

    $("#against").change(function() {
        if ($(this).val() === "metadata") {
            showNumericalVariableContainer(1);
        } else if ($(this).val() === "gene") {
            showGeneInputContainer(1);
        } else if ($(this).val() === "alpha") {
            showAlphaInputContainer(1);
        } else {
            showSpecificTaxonomyContainer(1);
        }
        updateAnalysis();
    });

    $("#expvar").change(function() {
        updateAnalysis();
    });

    $("#specific-taxonomy-typeahead-1").change(function() {
        updateAnalysis();
    });

    $("#gene-typeahead-1").change(function() {
        updateAnalysis();
    });

    $("#pvalthreshold").change(function() {
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

    $("#download-svg").click(function() {
        downloadCSV(tableResults);
    });

    $("#save-to-notebook").click(function() {
        saveTableToNotebook("Correlation Selection (" + $("#expvar").val() + ")", "Taxonomic Level: " + $("#taxonomy option:selected").text() + "\n", tableResults);
    });

    $("#send-to-lr").click(function() {
        if (cachedTrainingIndexes != null) {
            window.open('/linear_regression?pid=' + $("#project").val() + '&ref=Correlations+Selection&trainingIndexes=' + JSON.stringify(cachedTrainingIndexes) + '&taxonomyFilter=' + taxonomyLevels[$("#taxonomy").val()] + '&taxonomyFilterRole=Include&taxonomyFilterVals=' + JSON.stringify(cachedSelectedFeatures.map(f => f.split("; ")[f.split("; ").length - 1])) + '&expvar=' + $("#expvar").val(), '_blank');
        }
    });

    $("#send-to-dnn").click(function() {
        if (cachedTrainingIndexes != null) {
            window.open('/deep_neural_network?pid=' + $("#project").val() + '&ref=Correlations+Selection&problemType=regression&trainingIndexes=' + JSON.stringify(cachedTrainingIndexes) + '&taxonomyFilter=' + taxonomyLevels[$("#taxonomy").val()] + '&taxonomyFilterRole=Include&taxonomyFilterVals=' + JSON.stringify(cachedSelectedFeatures.map(f => f.split("; ")[f.split("; ").length - 1])) + '&expvar=' + $("#expvar").val(), '_blank');
        }
    });
}

//
// Analysis Specific Methods
//

function customCatVarCallback(result) {
    $("#expvar").empty();
    var allHeaders = result.map(function(obj) {
        return obj.name;
    });
    result.forEach(function(obj) {
        if (obj.type !== "categorical") {
            $("#expvar").append(
                '<option value="' + obj.name + '">' + obj.name + "</option>"
            );
        } else {
            $("#strata").append(
                '<option value="' + obj.name + '">' + obj.name + "</option>"
            );
        }
    });
}

function customCatVarValueLoading() {
    return $.when(loadOTUTableHeaders(1), loadGeneSelector(1)).then(function() {
        if (initialExpVar) {
            var initialExpVarArr = [];
            if (initialExpVar !== "") {
                initialExpVarArr = initialExpVar.split(",");
            }
            if ($("#against").val() === "alpha") {
                $("#alphaContext").val(initialExpVarArr[0]);
                $("#alphaType").val(initialExpVarArr[1]);
                initialExpVar = null;
            } else {
                initialExpVarArr.forEach(function(val) {
                if ($("#against").val() === "taxonomy") {
                    $("#specific-taxonomy-typeahead-1").tagsinput('add', val);
                    initialExpVar = null;
                } else if ($("#against").val() === "gene") {
                    $("#gene-typeahead-1").tagsinput('add', val);
                    initialExpVar = null;
                } else {
                    $("#expvar").val(initialExpVar);
                    initialExpVar = null;
                }
            });
            }
        }
    });
}

function updateAnalysis() {
    if (!loaded) {
        return;
    }
    showLoading(expectedLoadFactor);

    var level = taxonomyLevels[getTaxonomicLevel()];
    var expvar = getExpvarValue();

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var select = $("#select").val();
    var against = $("#against").val();
    if ((select === "gene" || against === "gene") && !hasGenes) {
        loadNoGenesWarning();
        return;
    }

    if (!expvar || expvar === "none") {
        loadNoCatvar();
        return;
    }

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
        select: select,
        against: against,
        pvalthreshold: $("#pvalthreshold").val(),
        expvar: expvar,
        level: level,
        trainingProportion: trainingProportion,
        fixTraining: fixTraining,
        trainingIndexes: JSON.stringify(cachedTrainingIndexes != null ? cachedTrainingIndexes : []),
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/correlations_selection" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            hideNotifications();
            hideLoading();

            var abundancesObj = JSON.parse(result);
            if (!$.isEmptyObject(abundancesObj["correlations"])) {
                loadSuccess();
                $("#send-to-container").show();
                renderCorrelationsSelection(abundancesObj);
                cachedTrainingIndexes = [...abundancesObj["training_indexes"]];
                cachedSelectedFeatures = abundancesObj["correlations"].map(d => d["otu"]);
            } else {
                loadNoResults();
                $("#send-to-container").hide();
            }
        },
        error: function(err) {
            loadError();
            $("#send-to-container").hide();
            console.log(err);
        }
    });
}

function renderCorrelationsSelection(abundancesObj) {
    $("#correlation-metadata").text(getExpvarValue());

    if (correlationDataTable) {
        correlationDataTable.clear();
    } else {
        correlationDataTable = $("#correlation-table").DataTable({
            order: [
                [2, "asc"]
            ],
            columns: [{
                    data: "otu",
                    fnCreatedCell: function (nTd, sData, oData, iRow, iCol) {

                        var toRender = "<a href='"+ shareToCorrelationsLink($("#against").val(), getExpvarValue(), $("#select").val(), oData.otu) + "' target='_blank'>" + oData.otu + "</a>";
                        if (oData.hint && oData.hint !== "") {
                            toRender += " <small class='text-muted'>(" + oData.hint + ")</small>";
                        }
                        $(nTd).html(toRender);
                    }
                },
                {
                    data: "coef"
                },
                {
                    data: "pval"
                },
                {
                    data: "qval"
                }
            ]
        });
    }

    tableResults = [];
    tableResults.push(["otu", "coef", "pval", "qval"]);

    var correlations = abundancesObj["correlations"];
    correlationDataTable.rows.add(correlations);
    correlationDataTable.draw();

    tableResults = tableResults.concat(correlations);
}

function showNumericalVariableContainer(index) {
    $("#numerical-variable-container").show();
    $("#specific-taxonomy-container-" + index).hide();
    $("#alphaDiversityContainer").hide();
}

function showSpecificTaxonomyContainer(index) {
    $("#numerical-variable-container").hide();
    $("#specific-taxonomy-container-" + index).show();
    $("#gene-input-container-" + index).hide();
    $("#alphaDiversityContainer").hide();
}

function showGeneInputContainer(index) {
    $("#numerical-variable-container").hide();
    $("#specific-taxonomy-container-" + index).hide();
    $("#gene-input-container-" + index).show();
    $("#alphaDiversityContainer").hide();
}

function showAlphaInputContainer(index) {
    $("#numerical-variable-container").hide();
    $("#specific-taxonomy-container-" + index).hide();
    $("#gene-input-container-" + index).hide();
    $("#alphaDiversityContainer").show();
}

function loadOTUTableHeaders(index) {
    $("#specific-taxonomy-typeahead-" + index).empty();
    var level = taxonomyLevels[$("#taxonomy").val()];
    return $.ajax({
        url: getSharedPrefixIfNeeded() + "/otu_table_headers_at_level?pid=" +
            $("#project").val() +
            "&level=" +
            level +
            getSharedUserSuffixIfNeeded(),
        success: function(result) {
            var typeAheadSource = JSON.parse(result);
            if (taxonomyRenderedTypeahead[index]) {
                $("#specific-taxonomy-typeahead-" + index).tagsinput("removeAll");
                $("#specific-taxonomy-typeahead-" + index).tagsinput("destroy");
            }
            taxonomyRenderedTypeahead[index] = true;
            tagsInput = $("#specific-taxonomy-typeahead-" + index).tagsinput({
                typeahead: {
                    source: typeAheadSource,
                    afterSelect: function() {
                        $("#specific-taxonomy-typeahead-" + index)
                            .tagsinput("input")
                            .val("");
                    }
                },
                freeInput: false
            });
            $(".taxonomy-specific-typeahead-wrapper .bootstrap-tagsinput").css(
                "width",
                "320px"
            );
        }
    });
}

function getExpvarValue() {
    var expvar = $("#expvar").val();
    if ($("#against").val() === "taxonomy") {
        expvar = $("#specific-taxonomy-typeahead-1").val();
    } else if ($("#against").val() === "gene") {
        expvar = $("#gene-typeahead-1").val();
    } else if ($("#against").val() === "alpha") {
        expvar = $("#alphaContext").val() + "," + $("#alphaType").val();
    }

    if (expvar === null) {
        // Occurs if there is no numerical variable
        expvar = "";
    }
    return expvar;
}
