// ============================================================
// Boruta JS Component
// ============================================================

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
    if (getParameterByName("maxruns") !== null) {
        $("#maxruns").val(getParameterByName("maxruns"));
    }
    if (getParameterByName("pval") !== null) {
        $("#pval").val(getParameterByName("pval"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#catvar").change(function() {
        updateAnalysis();
    });

    $("#pval").change(function() {
        updateAnalysis();
    });

    $("#maxruns").change(function() {
        updateAnalysis();
    });
}

//
// Analysis Specific Methods
//
function customLoading() {
    // Boruta is a random forest wrapper so it needs a categorical variable to work
    $("#catvar option[value='none']").remove();
}

function updateAnalysis() {
    showLoading();

    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var pval = $("#pval").val();
    var maxruns = $("#maxruns").val();

    if (catvar === "none") {
        $("#analysis-container").hide();
        hideLoading();
        hideNotifications();
        showNoCatvar();
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
        pval: pval,
        maxruns: maxruns
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: "boruta",
        data: data,
        success: function(result) {
            hideNotifications();
            hideLoading();

            var abundancesObj = JSON.parse(result);
            if (!$.isEmptyObject(abundancesObj["results"])) {
                $("#analysis-container").show();
                renderBorutaTable(abundancesObj);
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

function renderBorutaTable(abundancesObj) {
    $("#stats-container").hide();

    if ($.isEmptyObject(abundancesObj)) {
        return;
    }

    var $statsHeader = $("#stats-headers");
    var $statsRows = $("#stats-rows");
    $statsHeader.empty();
    $statsRows.empty();

    var stats = abundancesObj["results"];

    var keys = [];
    $.each(stats, function(key, value) {
        $statsHeader.append("<th>" + key + " (" + value.length + ")</th>");
        keys.push(key);
    });

    while (true) {
        var empty = true;
        var newRow = "<tr>";
        for (var k = 0; k < keys.length; k++) {
            if (stats[keys[k]].length == 0) {
                newRow += "<td></td>";
            } else {
                var head = stats[keys[k]].shift();
                newRow += "<td>" + head + "</td>";
                empty = false;
            }
        }
        if (empty) {
            break;
        } else {
            $("#stats-rows").append(newRow);
        }
    }

    $("#stats-container").fadeIn(250);
}
