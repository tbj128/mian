// ============================================================
// Table JS Component
// ============================================================

//
// Global Components
//
var tableResults = [];
var differentialDataTable;

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
    // Not used
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#download-svg").click(function() {
        downloadCSV(tableResults);
    });
}

//
// Analysis Specific Methods
//
function customLoading() {}

function renderTableView(table) {

    if (differentialDataTable) {
        differentialDataTable.destroy();
    }
    differentialDataTable = $("#table-view").DataTable({
        order: [
            [0, "asc"]
        ],
        columns: table[0].map(t => {
            return {
                title: t
            }
        }),
        data: table.slice(1)
    });
    tableResults = table;
}

function updateAnalysis() {
    $("#download-btn").hide();
    $("#too-large-message").hide();
    showLoading();

    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var data = {
        pid: $("#project").val(),
        taxonomyFilter: taxonomyFilter,
        taxonomyFilterRole: taxonomyFilterRole,
        taxonomyFilterVals: taxonomyFilterVals,
        sampleFilter: sampleFilter,
        sampleFilterRole: sampleFilterRole,
        sampleFilterVals: sampleFilterVals,
        level: level
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/table" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            loadSuccess();
            $("#download-btn").show();

            var table = JSON.parse(result);
            tableResults = table;

            if (tableResults.length > 2000 || tableResults[0].length > 2000) {
                $("#too-large-message").show();
            } else {
                $("#too-large-message").hide();
                renderTableView(table);
            }
        },
        error: function(err) {
            loadError();
            $("#too-large-message").hide();
            $("#download-btn").hide();
            tableResults = [];
            console.log(err);
        }
    });
}
