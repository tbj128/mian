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
initializeFields();
initializeComponent({
    hasCatVar: true,
    hasCatVarNoneOption: true
});
createSpecificListeners();

//
// Initializes fields based on the URL params
//
var initialYvalsSpecificTaxonomy = getParameterByName("yvalsSpecificTaxonomy") ? JSON.parse(getParameterByName("yvalsSpecificTaxonomy")) : [];
function initializeFields() {
    if (getParameterByName("yvals") !== null) {
        $("#yvals").val(getParameterByName("yvals"));
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

    $("#specific-taxonomy-typeahead").change(function() {
        updateAnalysis();
    });

    $("#statisticalTest").change(function() {
        $("#stats-type").text(statsTypes[$("#statisticalTest").val()]);
        updateAnalysis();
    });

    $("#yvals").change(function() {
        var val = $("#yvals").val();
        if (val === "mian-taxonomy-abundance") {
            $("#specific-taxonomy-container").show();
            $("#taxonomic-level-label").text("Taxonomic Level");
            $("#taxonomic-level-container").show();
            $.when(loadOTUTableHeaders()).done(function() {
                updateAnalysis();
            });
        } else {
            $("#specific-taxonomy-container").hide();
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
            updateAnalysis();
        }
    });

    $("#taxonomy-level").change(function() {
        var val = $("#yvals").val();
        if (val === "mian-taxonomy-abundance") {
            $.when(loadOTUTableHeaders()).done(function() {
                updateAnalysis();
            });
        }
    });

    $("#download-svg").click(function() {
        downloadSVG("boxplots." + $("#catvar").val() + "." + $("#yvals").val());
    });
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
    var yvals = $("#yvals").val();
    var statisticalTest = $("#statisticalTest").val();

    var yvalsSpecificTaxonomy = $("#specific-taxonomy-typeahead").val();
    if (yvalsSpecificTaxonomy === "") {
        yvalsSpecificTaxonomy = JSON.stringify([]);
    } else {
        yvalsSpecificTaxonomy = JSON.stringify(yvalsSpecificTaxonomy.split(","));
    }
    var level = taxonomyLevels[$("#taxonomy-level").val()];

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

function customCatVarCallback(result) {
    var allHeaders = result.filter(obj => obj.type === "both" || obj.type === "numeric").map(obj => obj.name);

    $("#yvals").empty();
    $("#yvals").append(
        '<option value="mian-taxonomy-abundance">Taxonomy Abundance</option><option value="mian-abundance">Aggregate Abundance</option><option value="mian-max">Max Abundance</option><option value="mian-min">Min Abundance</option><option value="mian-mean">Mean Abundance</option><option value="mian-median">Median Abundance</option>'
    );
    for (var i = 0; i < allHeaders.length; i++) {
        $("#yvals").append(
            '<option value="' + allHeaders[i] + '">' + allHeaders[i] + "</option>"
        );
    }
}

function customCatVarValueLoading() {
    return loadOTUTableHeaders();
}

function loadOTUTableHeaders() {
    if ($("#yvals").val() === "mian-taxonomy-abundance") {
        $("#specific-taxonomy-typeahead").empty();
        var level = taxonomyLevels[$("#taxonomy-level").val()];
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
                        afterSelect: () => {
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

                if (initialYvalsSpecificTaxonomy) {
                    initialYvalsSpecificTaxonomy.forEach(val => {
                        $("#specific-taxonomy-typeahead").tagsinput('add', val);
                    });
                    initialYvalsSpecificTaxonomy = null;
                }
            }
        });
        return headersPromise;
    }
    return null;
}
