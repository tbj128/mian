// ============================================================
// Beta Diversity Boxplot JS Component
// ============================================================

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
var initialStrata = getParameterByName("strata") ? getParameterByName("strata") : "";
function initializeFields() {
    if (getParameterByName("betaType") !== null) {
        $("#betaType").val(getParameterByName("betaType"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#catvar").change(function() {
        updateAnalysis();
    });

    $("#strata").change(function() {
        updateAnalysis();
    });

    $("#betaType").change(function() {
        updateAnalysis();
    });
}

//
// Analysis Specific Methods
//
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
    var strata = $("#strata").val();
    var betaType = $("#betaType").val();

    var data = {
        pid: $("#project").val(),
        taxonomyFilter: taxonomyFilter,
        taxonomyFilterRole: taxonomyFilterRole,
        taxonomyFilterVals: taxonomyFilterVals,
        sampleFilter: sampleFilter,
        sampleFilterRole: sampleFilterRole,
        sampleFilterVals: sampleFilterVals,
        level: level,
        catvar: catvar,
        strata: strata,
        betaType: betaType
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/beta_diversity" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            $("#display-error").hide();
            hideLoading();
            $("#analysis-container").show();
            var abundancesObj = JSON.parse(result);
            renderBoxplots(abundancesObj);
            renderPERMANOVA(abundancesObj);
            renderBetadisper(abundancesObj);
        },
        error: function(err) {
            hideLoading();
            $("#analysis-container").hide();
            $("#display-error").show();
            console.log(err);
        }
    });
}

function renderPERMANOVA(abundancesObj) {
    $("#permanova-container").hide();
    var permanova = abundancesObj["permanova"];
    permanova = permanova.replace(/(?:\r\n|\r|\n)/g, "<br />");
    permanova = permanova.replace(/<br \/><br \/>/g, "<br />");
    $("#permanova").html(permanova);
    $("#permanova-container").fadeIn(250);
}

function renderBetadisper(abundancesObj) {
    $("#betadisper-container").hide();
    var betaDisper = abundancesObj["dispersions"];
    betaDisper = betaDisper.replace(/(?:\r\n|\r|\n)/g, "<br />");
    betaDisper = betaDisper.replace(/<br \/><br \/>/g, "<br />");
    $("#betadisper").html(betaDisper);
    $("#betadisper-container").fadeIn(250);
}


function customCatVarCallback(json) {
    updateStrata(json);
}

function updateStrata(result) {
    var categoricalHeaders = [
        "None",
        ...result.filter(obj => obj.type === "categorical" || obj.type === "both").map(obj => obj.name)
    ];

    $("#strata").empty();

    for (var i = 0; i < categoricalHeaders.length; i++) {
        if (initialStrata && categoricalHeaders[i] == initialStrata) {
            $("#strata").append('<option value="' + categoricalHeaders[i] + '" selected>' + categoricalHeaders[i] + '</option>');
            initialStrata = null;
        } else {
            $("#strata").append('<option value="' + categoricalHeaders[i] + '">' + categoricalHeaders[i] + '</option>');
        }
    }
}
