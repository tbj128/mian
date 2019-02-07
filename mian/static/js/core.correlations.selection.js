// ============================================================
// Correlations Selection JS Component
// ============================================================
var correlationDataTable;

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
    // No initial fields
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#catvar").change(function() {
        updateAnalysis();
    });
}

//
// Analysis Specific Methods
//

function customLoading() {
    return updateCatVar(true);
}

function updateAnalysis() {
    showLoading();

    var level = taxonomyLevels[getTaxonomicLevel()];
    var catvar = $("#catvar").val();

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    if (catvar === "none") {
        $("#analysis-container").hide();
        hideLoading();
        hideNotifications();
        showNoCatvar();
        return;
    }

    var data = {
        pid: $("#project").val(),
        taxonomyFilter: taxonomyFilter,
        taxonomyFilterRole: taxonomyFilterRole,
        taxonomyFilterVals: taxonomyFilterVals,
        sampleFilter: sampleFilter,
        sampleFilterRole: sampleFilterRole,
        sampleFilterVals: sampleFilterVals,
        catvar: catvar,
        level: level
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: "/correlations_selection",
        data: data,
        success: function(result) {
            hideNotifications();
            hideLoading();

            var abundancesObj = JSON.parse(result);
            if (!$.isEmptyObject(abundancesObj["correlations"])) {
                $("#analysis-container").show();

                abundancesObj = JSON.parse(result);
                renderCorrelationsSelection(abundancesObj);
            } else {
                $("#analysis-container").hide();
                showNoResults();
            }
        },
        error: function(err) {
            $("#analysis-container").hide();
            hideLoading();
            hideNotifications();
            showError();
            console.log(err);
        }
    });
}

function renderCorrelationsSelection(abundancesObj) {
    $("#correlation-metadata").text($("#catvar").val());

    if (correlationDataTable) {
        correlationDataTable.clear();
    } else {
        correlationDataTable = $("#correlation-table").DataTable({
            order: [
                [2, "asc"]
            ],
            columns: [{
                    data: "otu"
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

    var correlations = abundancesObj["correlations"];
    correlationDataTable.rows.add(correlations);
    correlationDataTable.draw();
}
