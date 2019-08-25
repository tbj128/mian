// ============================================================
// Boxplot JS Component
// ============================================================
var tagsInput;
var expectedLoadFactor = 5000;

var statsTypes = {
    wilcoxon: "Wilcoxon Rank-Sum",
    ttest: "Welch's T-Test",
    anova: "ANOVA"
};

//
// Initialization
//
var initialTypeAhead = true; // To prevent the typeahead change from triggering multiple times
initializeFields();
initializeComponent({
    hasCatVar: true,
    hasCatVarNoneOption: true
});
createSpecificListeners();

//
// Initializes fields based on the URL params
//
var initialColorVar = getParameterByName("colorvar");
var initialYvals = getParameterByName("yvals");
var initialYvalsSpecificTaxonomy = getParameterByName("yvalsSpecificTaxonomy") ? JSON.parse(getParameterByName("yvalsSpecificTaxonomy")) : null;
function initializeFields() {
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

    $("#colorvar").change(function() {
        updateAnalysis();
    });

    $("#specific-taxonomy-typeahead").change(function() {
        if (initialYvalsSpecificTaxonomy == null) {
            // We don't want this to fire multiple times when it first is setting up the page
            updateAnalysis();
        }
    });

    $("#statisticalTest").change(function() {
        $("#stats-type").text(statsTypes[$("#statisticalTest").val()]);
        updateAnalysis();
    });

    $("#yvals").change(function() {
        updateYvals(true);
    });

    $("#taxonomy").change(function() {
        var val = $("#yvals").val();
        if (val === "mian-taxonomy-abundance") {
            $.when(loadOTUTableHeaders()).done(function() {
                updateAnalysis();
            });
        }
    });

    $("#gene-typeahead").change(function() {
        if (initialYvalsSpecificTaxonomy == null) {
            updateAnalysis();
        }
    });

    $("#download-svg").click(function() {
        downloadSVG("boxplots." + $("#catvar").val() + "." + $("#yvals").val());
    });
}

function updateYvals(shouldUpdateAnalysis) {
    var val = $("#yvals").val();
    if (val === "mian-taxonomy-abundance") {
        $("#specific-taxonomy-container").show();
        $("#gene-input-container-1").hide();
        $("#taxonomic-level-label").text("Taxonomic Level");
        $("#taxonomic-level-container").show();
        if (shouldUpdateAnalysis) {
            $.when(loadOTUTableHeaders()).done(function() {
                updateAnalysis();
            });
        }
    } else if (val === "mian-gene") {
        $("#specific-taxonomy-container").hide();
        $("#gene-input-container-1").show();
        $("#taxonomic-level-container").hide();
        if (shouldUpdateAnalysis) {
            $.when(loadGeneSelector(1)).done(function() {
                updateAnalysis();
            });
        }
    } else {
        $("#specific-taxonomy-container").hide();
        $("#gene-input-container-1").hide();
        $("#taxonomic-level-container").hide();
        if (val === "mian-max" || val === "mian-min") {
            if (val === "mian-max") {
                $("#taxonomic-level-label").text("Max Abundance Taxonomic Level");
            } else if (val === "mian-min") {
                $("#taxonomic-level-label").text("Min Abundance Taxonomic Level");
            }

            $("#taxonomic-level-container").show();
        } else {
            $("#taxonomic-level-container").hide();
        }
        if (shouldUpdateAnalysis) {
            updateAnalysis();
        }
    }
}

//
// Analysis Specific Methods
//

// Required analysis entry-point method
function updateAnalysis() {
    console.log("Updating analysis");

    showLoading(expectedLoadFactor);
    $("#stats-container").hide();

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var colorvar = $("#colorvar").val();
    var yvals = $("#yvals").val();
    var statisticalTest = $("#statisticalTest").val();

    var yvalsSpecificTaxonomy = "";
    if (yvals === "mian-gene") {
        yvalsSpecificTaxonomy = $("#gene-typeahead-1").val();
    } else if (yvals === "mian-taxonomy-abundance") {
        yvalsSpecificTaxonomy = $("#specific-taxonomy-typeahead").val();
    }

    if (yvals === "mian-gene" && !hasGenes) {
        loadNoGenesWarning();
        return;
    }

    if (yvalsSpecificTaxonomy === "") {
        yvalsSpecificTaxonomy = JSON.stringify([]);
    } else {
        yvalsSpecificTaxonomy = JSON.stringify(yvalsSpecificTaxonomy.split(","));
    }
    var level = taxonomyLevels[$("#taxonomy").val()];

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
        catvar: catvar,
        colorvar: colorvar,
        yvals: yvals,
        level: level,
        yvalsSpecificTaxonomy: yvalsSpecificTaxonomy,
        statisticalTest: statisticalTest
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/boxplots" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            $("#stats-type").text(statsTypes[$("#statisticalTest").val()]);

            var abundancesObj = JSON.parse(result);
            if ($.isEmptyObject(abundancesObj["abundances"])) {
                loadNoResults();
            } else {
                loadSuccess();
                renderBoxplots(abundancesObj, "", $("#yvals option:selected").text());
                renderPvaluesTable(abundancesObj);
            }
        },
        error: function(err) {
            loadError();
            console.log(err);
        }
    });
}

function customCatVarCallback(result) {
    var allHeaders = ["None"].concat(result.map(function(obj) { return obj.name; }));
    var numericHeaders = result.filter(function(obj) { return obj.type === "both" || obj.type === "numeric"; }).map(function(obj) { return obj.name; });

    $("#yvals").empty();
    $("#yvals").append(
        '<option value="mian-taxonomy-abundance">Taxonomic Group or OTU Abundance</option><option value="mian-gene">Gene Expression</option><option value="mian-abundance">Aggregate Abundance</option><option value="mian-max">Max Abundance</option><option value="mian-min">Min Abundance</option><option value="mian-mean">Mean Abundance</option><option value="mian-median">Median Abundance</option>'
    );
    for (var i = 0; i < numericHeaders.length; i++) {
        $("#yvals").append(
            '<option value="' + numericHeaders[i] + '">' + numericHeaders[i] + "</option>"
        );
    }

    $("#colorvar").empty();
    allHeaders.forEach(function(obj) {
        $("#colorvar").append(
            '<option value="' + obj + '">' + obj + "</option>"
        );
    });

    if (initialColorVar) {
        $("#colorvar").val(initialColorVar);
        initialColorVar = null;
    }
}

// Blocks initial loading until this is completed
function customCatVarValueLoading() {
    return $.when(loadOTUTableHeaders(), loadGeneSelector(1)).then(function() {
        if (initialYvals) {
            $("#yvals").val(initialYvals);
            updateYvals(false);
            initialYvals = null;
        }
        if (initialYvalsSpecificTaxonomy) {
            initialYvalsSpecificTaxonomy.forEach(function(val) {
                if ($("#yvals").val() === "mian-taxonomy-abundance") {
                    $("#specific-taxonomy-typeahead").tagsinput('add', val);
                } else if ($("#yvals").val() === "mian-gene") {
                    $("#gene-typeahead-1").tagsinput('add', val);
                }
            });
            initialYvalsSpecificTaxonomy = null;
        }
    });
}

function loadOTUTableHeaders() {
    if ($("#yvals").val() === "mian-taxonomy-abundance") {
        $("#specific-taxonomy-typeahead").empty();
        var level = taxonomyLevels[$("#taxonomy").val()];
        var headersPromise = $.ajax({
            url: getSharedPrefixIfNeeded() + "/otu_table_headers_at_level?pid=" +
                $("#project").val() +
                "&level=" +
                level +
                getSharedUserSuffixIfNeeded(),
            success: function(result) {
                var typeAheadSource = JSON.parse(result);
                if (tagsInput) {
                    $("#specific-taxonomy-typeahead").tagsinput("removeAll");
                    $("#specific-taxonomy-typeahead").tagsinput("destroy");
                }

                tagsInput = $("#specific-taxonomy-typeahead").tagsinput({
                    typeahead: {
                        source: typeAheadSource,
                        afterSelect: function() {
                            $("#specific-taxonomy-typeahead")
                                .tagsinput("input")
                                .val("");
                        }
                    },
                    freeInput: false
                });
                $("#taxonomy-specific-typeahead-wrapper .bootstrap-tagsinput").css(
                    "width",
                    "320px"
                );
            }
        });
        return headersPromise;
    }
    return null;
}

