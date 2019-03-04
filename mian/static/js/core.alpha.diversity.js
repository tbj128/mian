// ============================================================
// Alpha Diversity Boxplot JS Component
// ============================================================
var statsTypes = {
    wilcoxon: "Wilcoxon Rank-Sum",
    ttest: "Welch's T-Test"
};
var expectedLoadFactor = 712;

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
    if (getParameterByName("alphaType") !== null) {
        $("#alphaType").val(getParameterByName("alphaType"));
        if (getParameterByName("alphaType") === "faith_pd") {
            $("#alphaContextContainer").hide();
        }
    }
    if (getParameterByName("alphaContext") !== null) {
        $("#alphaContext").val(getParameterByName("alphaContext"));
    }
    if (getParameterByName("statisticalTest") !== null) {
        $("#statisticalTest").val(getParameterByName("statisticalTest"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#catvar").change(function() {
        updateAnalysis();
    });

    $("#alphaType").change(function() {
        updateAnalysis();

        if ($("#alphaType").val() === "faith_pd") {
            $("#alphaContextContainer").hide();
        } else {
            $("#alphaContextContainer").show();
        }
    });

    $("#alphaContext").change(function() {
        updateAnalysis();
    });

    $("#statisticalTest").change(function() {
        $("#stats-type").text(statsTypes[$("#statisticalTest").val()]);
        updateAnalysis();
    });

    $("#download-svg").click(function() {
        downloadSVG("alpha.diversity." + $("#catvar").val() + "." + $("#alphaType").val() + "." + $("#alphaContext").val() + "." + $("#statisticalTest").val());
    });


    $("#yvals").change(function() {
        var val = $("#yvals").val();
        if (val === "mian-max" || val === "mian-min") {
            if (val === "mian-max") {
                $("#taxonomic-level-label").text("Max Abundance Taxonomic Level");
            } else if (val === "mian-min") {
                $("#taxonomic-level-label").text("Min Abundance Taxonomic Level");
            }

            $("#taxonomic-level").show();
        } else {
            $("#taxonomic-level").hide();
        }

        updateAnalysis();
    });
}

//
// Analysis Specific Methods
//
function updateAnalysis() {

    showLoading(expectedLoadFactor);
    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var alphaType = $("#alphaType").val();
    var alphaContext = $("#alphaContext").val();
    var statisticalTest = $("#statisticalTest").val();

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
        alphaType: alphaType,
        alphaContext: alphaContext,
        statisticalTest: statisticalTest
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/alpha_diversity" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            $("#stats-type").text(statsTypes[$("#statisticalTest").val()]);
            var abundancesObj = JSON.parse(result);
            if (abundancesObj["no_tree"]) {
                loadNoTree();
            } else if (abundancesObj["has_float"]) {
                loadFloatDataWarning();
            } else if ($.isEmptyObject(abundancesObj.abundances)) {
                loadNoResults();
            } else {
                loadSuccess();
                renderBoxplots(abundancesObj);
                renderPvaluesTable(abundancesObj);
            }
        },
        error: function(err) {
            loadError();
            console.log(err);
        }
    });
}

function customLoading() {
    $("#yvals").empty();
    $("#yvals").append(
        '<option value="mian-abundance">Aggregate Abundance</option><option value="mian-max">Max Abundance</option><option value="mian-min">Min Abundance</option><option value="mian-mean">Mean Abundance</option><option value="mian-median">Median Abundance</option>'
    );
    for (var i = 0; i < catVars.length; i++) {
        $("#yvals").append(
            '<option value="' + catVars[i] + '">' + catVars[i] + "</option>"
        );
    }
}
