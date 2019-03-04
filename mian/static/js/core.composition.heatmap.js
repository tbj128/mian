// ============================================================
// Composition Heatmap JS Component
// ============================================================

var expectedLoadFactor = 3000;

// Global variables storing the data
var uniqueGroupVals = [];
var idMap = {};

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
    if (getParameterByName("rows") !== null) {
        $("#rows").val(getParameterByName("rows"));
    }
    if (getParameterByName("cols") !== null) {
        $("#cols").val(getParameterByName("cols"));
    }
    if (getParameterByName("showlabels") !== null) {
        $("#showlabels").val(getParameterByName("showlabels"));
    }
    if (getParameterByName("clustersamples") !== null) {
        $("#clustersamples").val(getParameterByName("clustersamples"));
    }
    if (getParameterByName("clustertaxonomic") !== null) {
        $("#clustertaxonomic").val(getParameterByName("clustertaxonomic"));
    }
    if (getParameterByName("colorscheme") !== null) {
        $("#colorscheme").val(getParameterByName("colorscheme"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#catvar").change(function() {
        updateAnalysis();
    });

    $("#rows").change(function() {
        if ($("#rows").val() === "Taxonomic") {
            $("#cols").val("SampleID");
        } else {
            $("#cols").val("Taxonomic");
        }
        updateAnalysis();
    });

    $("#cols").change(function() {
        if ($("#cols").val() === "Taxonomic") {
            $("#rows").val("SampleID");
        } else {
            $("#rows").val("Taxonomic");
        }
        updateAnalysis();
    });

    $("#clustersamples").change(function() {
        updateAnalysis();
    });

    $("#clustertaxonomic").change(function() {
        updateAnalysis();
    });

    $("#showlabels").change(function() {
        updateAnalysis();
    });

    $("#colorscheme").change(function() {
        updateAnalysis();
    });

    $("#download-svg").click(function() {
        downloadSVG("composition.heatmap." + $("#catvar").val());
    });
}

//
// Analysis Specific Methods
//
function customCatVarCallback(result) {
}

function getTaxonomicLevel() {
    return $("#taxonomy").val();
}

function updateAnalysis() {
    showLoading(expectedLoadFactor);
    $("#stats-container").fadeIn(250);

    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();

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
        rows: $("#rows").val(),
        cols: $("#cols").val(),
        clustersamples: $("#clustersamples").val(),
        clustertaxonomic: $("#clustertaxonomic").val(),
        showlabels: $("#showlabels").val(),
        colorscheme: $("#colorscheme").val()
    };


    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/composition_heatmap" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            var abundancesObj = JSON.parse(result);
            if ((abundancesObj["abundances"] && abundancesObj["abundances"].length === 0) || (abundancesObj["row_headers"] && abundancesObj["row_headers"].length === 0)) {
                loadNoResults();
            } else {
                loadSuccess();
                renderHeatmap(abundancesObj, abundancesObj["min"], abundancesObj["max"], $("#rows").val(), $("#cols").val());
            }
        },
        error: function(err) {
            loadError();
            console.log(err);
        }
    });
}
