// ============================================================
// Table JS Component
// ============================================================

//
// Global Components
//
var tableResults = [];

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
    $("#download-btn").click(function () {
        var csvContent = "data:text/csv;charset=utf-8," + tableResults.map(e=>e.join(",")).join("\n");
        var encodedUri = encodeURI(csvContent);
        window.open(encodedUri);
    });
}

//
// Analysis Specific Methods
//
function customLoading() {}

function renderTableView(table) {
    $("#stats-container").hide();

    $("#stats-headers").empty();
    var headers = table[0];
    for (var i = 0; i < headers.length; i++) {
        var r = "<th>" + headers[i] + "</th>";
        $("#stats-headers").append(r);
    }

    $("#stats-rows").empty();
    for (var i = 1; i < table.length; i++) {
        var r = "<tr>";
        for (var j = 0; j < table[i].length; j++) {
            r = r + "<td>" + table[i][j] + "</td>";
        }
        r = r + "</tr>";
        $("#stats-rows").append(r);
    }

    $("#stats-container").fadeIn(250);
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
        url: "table",
        data: data,
        success: function(result) {
            $("#display-error").hide();
            hideLoading();
            $("#analysis-container").show();
            $("#stats-container").show();
            $("#download-btn").show();

            var table = JSON.parse(result);
            tableResults = table;

            if (result.length > 5000 && result[0].length > 5000) {
                $("#too-large-message").show();
            } else {
                $("#too-large-message").hide();
                renderTableView(table);
            }
        },
        error: function(err) {
            hideLoading();
            $("#analysis-container").hide();
            $("#too-large-message").hide();
            $("#download-btn").hide();
            $("#stats-container").hide();
            $("#display-error").show();
            tableResults = [];
            console.log(err);
        }
    });
}
