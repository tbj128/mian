// ============================================================
// Alpha Diversity Boxplot JS Component
// ============================================================
var statsTypes = {
    wilcoxon: "Wilcoxon Rank-Sum",
    ttest: "Welch's T-Test"
};
var expectedLoadFactor = 712;
var expVarToType = {};

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
var initialColorVar = getParameterByName("colorvar");
var initialSizeVar = getParameterByName("sizevar");
function initializeFields() {
    if (getParameterByName("alphaContext") !== null) {
        $("#alphaContext").val(getParameterByName("alphaContext"));
        if ($("#alphaContext").val() === "speciesnumber") {
            $("#alphaTypeContainer").hide();
        } else {
            $("#alphaTypeContainer").show();
        }
    }
    if (getParameterByName("alphaType") !== null) {
        $("#alphaType").val(getParameterByName("alphaType"));
    }
    if (getParameterByName("statisticalTest") !== null) {
        $("#statisticalTest").val(getParameterByName("statisticalTest"));
    }
    if (getParameterByName("plotType") !== null) {
        $("#plotType").val(getParameterByName("plotType"));
        if (getParameterByName("plotType") === "boxplot") {
            $("#colorvarContainer").hide();
        } else {
            $("#colorvarContainer").show();
        }
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#expvar").change(function() {
        if (expVarToType[$("#expvar").val()] === "both" || expVarToType[$("#expvar").val()] === "categorical") {
            $("#plotType").val("boxplot");
            $("#colorvarContainer").hide();
        } else {
            $("#plotType").val("scatterplot");
            $("#colorvarContainer").show();
        }
        updateAnalysis();
    });

    $("#colorvar").change(function() {
        updateAnalysis();
    });

    $("#sizevar").change(function() {
        updateAnalysis();
    });

    $("#plotType").change(function() {
        if ($("#plotType").val() === "boxplot") {
            $("#colorvarContainer").hide();
        } else {
            $("#colorvarContainer").show();
        }
        updateAnalysis();
    });

    $("#alphaContext").change(function() {
        if ($("#alphaContext").val() === "speciesnumber") {
            $("#alphaTypeContainer").hide();
        } else {
            $("#alphaTypeContainer").show();
        }
        updateAnalysis();
    });

    $("#alphaType").change(function() {
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

    var expvar = $("#expvar").val();
    var alphaType = $("#alphaType").val();
    var alphaContext = $("#alphaContext").val();
    var statisticalTest = $("#statisticalTest").val();
    var plotType = $("#plotType").val();
    var colorvar = $("#colorvar").val();
    var sizevar = $("#sizevar").val();

    if (alphaType === "faith_pd" && alphaContext === "evenness") {
        loadError("<strong>Evenness cannot be calculated using Faith's Phylogenetic Diversity.</strong>");
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
        alphaType: alphaType,
        alphaContext: alphaContext,
        statisticalTest: statisticalTest,
        plotType: plotType,
        colorvar: colorvar,
        sizevar: sizevar
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
            } else if (($("#plotType").val() === "boxplot" && $.isEmptyObject(abundancesObj.abundances)) || ($("#plotType").val() !== "boxplot" && abundancesObj.corrArr.length === 0)) {
                loadNoResults();
            } else {
                loadSuccess();

                var yAxisText = $("#alphaType option:selected").text() + " " + $("#alphaContext option:selected").text();
                if ($("#alphaContext").val() === "speciesnumber") {
                    yAxisText = $("#alphaContext option:selected").text();
                }
                if ($("#plotType").val() === "boxplot") {
                    renderBoxplots(abundancesObj, "", yAxisText);
                    renderPvaluesTable(abundancesObj);
                } else {
                    renderCorrelations(abundancesObj, $("#expvar").val(), yAxisText);
                    renderCorrelationsTable(abundancesObj);
                }
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

function customCatVarCallback(result) {
    result.forEach(function(obj) {
        expVarToType[obj.name] = obj.type;
    });
    var allHeaders = ["None"].concat(result.map(function(obj) { return obj.name; }));
    var numericHeaders = ["None"].concat(result.filter(function(obj) { return obj.type === "both" || obj.type === "numeric"; }).map(function(obj) { return obj.name; }));

    //
    // Renders the experimental variable
    //
    $("#expvar").empty();
    $("#colorvar").empty();
    $("#sizevar").empty();
    allHeaders.forEach(function(obj) {
        $("#expvar").append(
            '<option value="' + obj + '">' + obj + "</option>"
        );
        $("#colorvar").append(
            '<option value="' + obj + '">' + obj + "</option>"
        );
    });
    numericHeaders.forEach(function(obj) {
        $("#sizevar").append(
            '<option value="' + obj + '">' + obj + "</option>"
        );
    });
    if (initialExpVar) {
        $("#expvar").val(initialExpVar);
        initialExpVar = null;
    }
    if (initialColorVar) {
        $("#colorvar").val(initialColorVar);
        initialColorVar = null;
    }
    if (initialSizeVar) {
        $("#sizevar").val(initialSizeVar);
        initialSizeVar = null;
    }
}
