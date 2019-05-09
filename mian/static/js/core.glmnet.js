// ============================================================
// GLMNet JS Component
// ============================================================

//
// Global Components
//
var tableResults = [];
var expVarToType = {};
var expectedLoadFactor = 500;

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
    if (getParameterByName("alpha") !== null) {
        $("#alpha").val(getParameterByName("alpha"));
    }
    if (getParameterByName("lambdathreshold") !== null) {
        $("#lambdathreshold").val(getParameterByName("lambdathreshold"));

        if ($("#lambdathreshold").val() === "Custom") {
            $("#lambdaval").show();
            $("#lambdatitle").show();
        } else {
            $("#lambdaval").hide();
            $("#lambdatitle").hide();
        }
    }
    if (getParameterByName("lambdaval") !== null) {
        $("#lambdaval").val(getParameterByName("lambdaval"));
    }
    if (getParameterByName("model") !== null) {
        $("#model").val(getParameterByName("model"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#expvar").change(function() {
        var expVarType = expVarToType[$(this).val()];
        renderModelType(expVarType);
        updateAnalysis();
    });

    $("#model").change(function() {
        updateAnalysis();
    });

    $("#alpha").change(function() {
        updateAnalysis();
    });

    $("#lambdathreshold").change(function() {
        updateAnalysis();
        if ($("#lambdathreshold").val() === "Custom") {
            $("#lambdaval").show();
            $("#lambdatitle").show();
        } else {
            $("#lambdaval").hide();
            $("#lambdatitle").hide();
        }
    });

    $("#lambdaval").change(function() {
        updateAnalysis();
    });

    $("#download-svg").click(function() {
        downloadCSV(tableResults);
    });
}

//
// Analysis Specific Methods
//
function customLoading() {
    // This needs a categorical variable to work
    $("#catvar option[value='none']").remove();
}

function customCatVarCallback(result) {
    $("#expvar").empty();
    result.forEach(function(obj) {
        expVarToType[obj.name] = obj.type;
        $("#expvar").append(
            '<option value="' + obj.name + '">' + obj.name + "</option>"
        );
    });
    if (initialExpVar) {
        $("#expvar").val(initialExpVar);
        initialExpVar = null;
    }
    renderModelType(expVarToType[$("#expvar").val()]);
}

function renderModelType(type) {
    var prevSelectedModel = $("#model").val();
    $("#model").empty();
    if (type === "numeric" || type === "both") {
        $("#model").append(
            "<option value=\"poisson\">Poisson</option>"
        );
        $("#model").append(
            "<option value=\"gaussian\">Gaussian</option>"
        );

        if (prevSelectedModel === "poisson" || prevSelectedModel === "gaussian") {
            $("#model").val(prevSelectedModel);
        }
    }
    if (type === "both" || type === "categorical") {
        $("#model").append(
            "<option value=\"multinomial\">Binomial/Multinomial (Logistic)</option>"
        );

        if (prevSelectedModel === "logistic") {
            $("#model").val(prevSelectedModel);
        }
    }
}

function renderGlmnetTable(abundancesObj) {
    if ($.isEmptyObject(abundancesObj)) {
        return;
    }

    $("#analysis-container").empty();

    var familyType = $("#model").val();

    var stats = abundancesObj["results"];
    var hints = abundancesObj["hints"];
    var render = "<div>";
    var emptyTable = true;
    $.each(stats, function(key, value) {
        if (familyType === "multinomial") {
            var multinomialPopover = '<i class="fa fa-info-circle" data-toggle="popover" data-title="Multinomial Response Value" data-content="The following odds ratios apply specifically for this particular response value of the experimental variable" data-trigger="hover" data-placement="bottom"></i>';

            render += "<h3><strong>" + key + "</strong> " + multinomialPopover + "</h3>";
        }

        tableResults = [];

        var taxonomyPopover = '<i class="fa fa-info-circle" data-toggle="popover" data-title="Taxonomic Group/OTU" data-content="The taxonomic group or OTU that has a non-zero coefficient in the selected generalized linear model" data-trigger="hover" data-placement="bottom"></i>';
        var valuePopover = '<i class="fa fa-info-circle" data-toggle="popover" data-title="Coefficient Value" data-content="This coefficient is the weight assigned to the corresponding taxonomic group/OTU - it should be interpreted in relation to the model itself. <br/><br/>For linear models (Poisson, Gaussian), coefficients generally represent the rate of change. <br/><br/>For logistic models, coefficients are odds ratio (ie. >1 values are associated with higher odds of categorical variable occurring).<br/><br/> Note: Use these coefficient values with caution as this tool does not validate the assumptions of the selected model (eg. whether it is a normal distribution)." data-html="true" data-trigger="hover" data-placement="bottom"></i>';

        if (familyType === "binomial" || familyType === "multinomial") {
            render +=
                '<table class="table table-hover"><thead><tr><th>Taxonomic Group/OTU ' + taxonomyPopover + '</th><th>Coefficient (Odds Ratio) ' + valuePopover + '</th></tr></thead><tbody> ';
            tableResults.push(["Taxonomy", "Value"]);

            value.forEach(function(val) {
                if (val[1] !== 1) {
                    var hint = "";
                    if (hints[val[0]] && hints[val[0]] !== "") {
                        hint = " <small class='text-muted'>(" + hints[val[0]] + ")</small>";
                    }
                    render += "<tr><td><a href='" + shareToBoxplotLink(val[0]) + "' target='_blank'>" + val[0] + "</a>" + hint + "</td><td>" + val[1] + "</td></tr>";
                    tableResults.push([val[0], val[1]]);
                    emptyTable = false;
                }
            });
            render += "</tbody></table>";
        } else {
            render +=
                '<table class="table table-hover"><thead><tr><th>Taxonomic Group/OTU ' + taxonomyPopover + '</th><th>Coefficient Value ' + valuePopover + '</th></tr></thead><tbody> ';
            tableResults.push(["Taxonomy", "Value"]);

            value.forEach(function(val) {
                if (val[1] !== 0) {
                    var hint = "";
                    if (hints[val[0]] && hints[val[0]] !== "") {
                        hint = " <small class='text-muted'>(" + hints[val[0]] + ")</small>";
                    }
                    render += "<tr><td><a href='" + shareToBoxplotLink(val[0]) + "' target='_blank'>" + val[0] + "</a>" + hint + "</td><td>" + val[1] + "</td></tr>";
                    tableResults.push([val[0], val[1]]);
                    emptyTable = false;
                }
            });
            render += "</tbody></table>";
        }

        tableResults.push([""]);
    });

    render += "</div><br /><hr /><br />";
    if (emptyTable) {
        loadNoResults();
    } else {
        $("#analysis-container").append(render);
        $('[data-toggle="popover"]').popover();
    }
}

function updateAnalysis() {
    showLoading(expectedLoadFactor);
    $("#display-poisson-error").hide();

    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var expvar = $("#expvar").val();
    var alpha = $("#alpha").val();
    var model = $("#model").val();
    var lambdathreshold = $("#lambdathreshold").val();

    if (expvar === "none") {
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
        alpha: alpha,
        model: model,
        lambdathreshold: lambdathreshold
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/glmnet" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            var abundancesObj = JSON.parse(result);
            if (!$.isEmptyObject(abundancesObj)) {
                if (abundancesObj["error"]) {
                    hideLoading();
                    $("#display-poisson-error").show();
                } else {
                    loadSuccess();
                    renderGlmnetTable(abundancesObj);
                }
            } else {
                loadNoResults();
            }
        },
        error: function(err) {
            loadError();
            console.log(err);
        }
    });
}
