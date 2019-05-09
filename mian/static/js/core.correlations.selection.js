// ============================================================
// Correlations Selection JS Component
// ============================================================

//
// Global Components
//
var tableResults = [];
var correlationDataTable;
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
    // No initial fields
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#expvar").change(function() {
        updateAnalysis();
    });

    $("#download-svg").click(function() {
        downloadCSV(tableResults);
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
        }
    });
    if (initialExpVar) {
        $("#expvar").val(initialExpVar);
        initialExpVar = null;
    }
}

function updateAnalysis() {
    showLoading(expectedLoadFactor);

    var level = taxonomyLevels[getTaxonomicLevel()];
    var expvar = $("#expvar").val();

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

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
        expvar: expvar,
        level: level
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
                renderCorrelationsSelection(abundancesObj);
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

function renderCorrelationsSelection(abundancesObj) {
    $("#correlation-metadata").text($("#expvar").val());

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

                        var toRender = "<a href='"+ shareToCorrelationsLink(oData.otu, $("#expvar").val()) + "' target='_blank'>" + oData.otu + "</a>";
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
