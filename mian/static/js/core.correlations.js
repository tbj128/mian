// ============================================================
// Boxplot JS Component
// ============================================================
var tagsInput;
var abundancesObj = {};
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
var initialCorrvar1 = getParameterByName("corrvar1");
var initialCorrvar2 = getParameterByName("corrvar2");
var initialCorrvar1SpecificTaxonomies = getParameterByName("corrvar1SpecificTaxonomies") ? JSON.parse(getParameterByName("corrvar1SpecificTaxonomies")) : [];
var initialCorrvar2SpecificTaxonomies = getParameterByName("corrvar2SpecificTaxonomies") ? JSON.parse(getParameterByName("corrvar2SpecificTaxonomies")) : [];
var initialColorVar = getParameterByName("colorvar");
var initialSizeVar = getParameterByName("sizevar");
function initializeFields() {
    if (getParameterByName("samplestoshow") !== null) {
        $("#samplestoshow").val(getParameterByName("samplestoshow"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#corrvar2 option:eq(1)").attr("selected", "selected");

    $("#corrvar1").change(function() {
        if ($("#corrvar1").val() === "mian-taxonomy-abundance") {
            $("#specific-taxonomy-container-1").show();
            $("#taxonomic-level-container").show();
            $.when(loadOTUTableHeaders("corrvar1")).done(function() {
                updateAnalysis();
            });
        } else {
            $("#specific-taxonomy-container-1").hide();
            updateAnalysis();
        }
    });

    $("#corrvar2").change(function() {
        if ($("#corrvar2").val() === "mian-taxonomy-abundance") {
            $("#specific-taxonomy-container-2").show();
            $("#taxonomic-level-container").show();
            $.when(loadOTUTableHeaders("corrvar2")).done(function() {
                updateAnalysis();
            });
        } else {
            $("#specific-taxonomy-container-2").hide();
            updateAnalysis();
        }
    });

    $("#colorvar").change(function() {
        updateAnalysis();
    });

    $("#sizevar").change(function() {
        updateAnalysis();
    });

    $("#samplestoshow").change(function() {
        updateAnalysis();
    });

    $("#specific-taxonomy-typeahead-1").change(function() {
        updateAnalysis();
    });

    $("#specific-taxonomy-typeahead-2").change(function() {
        updateAnalysis();
    });

    $("#taxonomy").change(function() {
        if (
            $("#corrvar1").val() === "mian-taxonomy-abundance" ||
            $("#corrvar2").val() === "mian-taxonomy-abundance"
        ) {
            $.when(loadOTUTableHeaders()).done(function() {
                updateAnalysis();
            });
        } else {
            updateAnalysis();
        }
    });

    $("#download-svg").click(function() {
        downloadSVG("corrleations." + $("#corrvar1").val() + "." + $("#corrvar2").val());
    });
}

//
// Analysis Specific Methods
//

function customCatVarCallback(json) {
    updateCorrVar(json);
}

function customCatVarValueLoading() {
    return loadOTUTableHeaders();
}

function loadOTUTableHeaders(corrvarType) {
    if (
        $("#corrvar1").val() === "mian-taxonomy-abundance" ||
        $("#corrvar2").val() === "mian-taxonomy-abundance"
    ) {
        $("#specific-taxonomy-typeahead-1").empty();
        $("#specific-taxonomy-typeahead-2").empty();
        var level = taxonomyLevels[$("#taxonomy").val()];
        var headersPromise = $.ajax({
            url: getSharedPrefixIfNeeded() + "/otu_table_headers_at_level?pid=" +
                $("#project").val() +
                "&level=" +
                level +
                getSharedUserSuffixIfNeeded(),
            success: function(result) {
                var typeAheadSource = JSON.parse(result);
                if (!corrvarType || corrvarType === "corrvar1") {
                    if (tagsInput) {
                        $("#specific-taxonomy-typeahead-1").tagsinput("removeAll");
                        $("#specific-taxonomy-typeahead-1").tagsinput("destroy");
                    }

                    tagsInput = $("#specific-taxonomy-typeahead-1").tagsinput({
                        typeahead: {
                            source: typeAheadSource,
                            afterSelect: function() {
                                $("#specific-taxonomy-typeahead-1")
                                    .tagsinput("input")
                                    .val("");
                            }
                        },
                        freeInput: false
                    });
                    $("#taxonomy-specific-typeahead-wrapper-1 .bootstrap-tagsinput").css(
                        "width",
                        "320px"
                    );

                    if (initialCorrvar1SpecificTaxonomies) {
                        initialCorrvar1SpecificTaxonomies.forEach(function(val) {
                            $("#specific-taxonomy-typeahead-1").tagsinput('add', val);
                        });
                        initialCorrvar1SpecificTaxonomies = null;
                    }
                }
                if (!corrvarType || corrvarType === "corrvar2") {
                    if (tagsInput) {
                        $("#specific-taxonomy-typeahead-2").tagsinput("removeAll");
                        $("#specific-taxonomy-typeahead-2").tagsinput("destroy");
                    }

                    tagsInput = $("#specific-taxonomy-typeahead-2").tagsinput({
                        typeahead: {
                            source: typeAheadSource,
                            afterSelect: function() {
                                $("#specific-taxonomy-typeahead-2")
                                    .tagsinput("input")
                                    .val("");
                            }
                        },
                        freeInput: false
                    });
                    $("#taxonomy-specific-typeahead-wrapper-2 .bootstrap-tagsinput").css(
                        "width",
                        "320px"
                    );

                    if (initialCorrvar2SpecificTaxonomies) {
                        initialCorrvar2SpecificTaxonomies.forEach(function(val) {
                            $("#specific-taxonomy-typeahead-2").tagsinput('add', val);
                        });
                        initialCorrvar2SpecificTaxonomies = null;
                    }
                }
            }
        });
        return headersPromise;
    }
    return null;
}

function updateAnalysis() {
    showLoading(expectedLoadFactor);

    var level = taxonomyLevels[$("#taxonomy").val()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var corrvar1 = $("#corrvar1").val();
    var corrvar2 = $("#corrvar2").val();
    var colorvar = $("#colorvar").val();
    var sizevar = $("#sizevar").val();
    var samplestoshow = $("#samplestoshow").val();
    var corrvar1SpecificTaxonomies = $("#specific-taxonomy-typeahead-1").val();
    var corrvar2SpecificTaxonomies = $("#specific-taxonomy-typeahead-2").val();

    if (corrvar1SpecificTaxonomies === "") {
        corrvar1SpecificTaxonomies = JSON.stringify([]);
    } else {
        corrvar1SpecificTaxonomies = JSON.stringify(
            corrvar1SpecificTaxonomies.split(",")
        );
    }

    if (corrvar2SpecificTaxonomies === "") {
        corrvar2SpecificTaxonomies = JSON.stringify([]);
    } else {
        corrvar2SpecificTaxonomies = JSON.stringify(
            corrvar2SpecificTaxonomies.split(",")
        );
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
        corrvar1: corrvar1,
        corrvar2: corrvar2,
        colorvar: colorvar,
        sizevar: sizevar,
        samplestoshow: samplestoshow,
        corrvar1SpecificTaxonomies: corrvar1SpecificTaxonomies,
        corrvar2SpecificTaxonomies: corrvar2SpecificTaxonomies
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/correlations" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            abundancesObj = JSON.parse(result);
            if (abundancesObj["corrArr"] && abundancesObj["corrArr"].length > 0) {
                loadSuccess();
                renderCorrelations(abundancesObj, $("#corrvar1").val(), $("#corrvar2").val());
                renderCorrelationsTable(abundancesObj);
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

function updateCorrVar(result) {
    var allHeaders = ["None"];
    allHeaders = allHeaders.concat(result.map(function(obj) { return obj.name; }));
    var numericHeaders = [
        "None"
    ];
    numericHeaders = numericHeaders.concat(result.filter(function(obj) { return obj.type === "numeric" || obj.type === "both"; }).map(function(obj) { return obj.name; }));
    var categoricalHeaders = [
        "None"
    ];
    categoricalHeaders = categoricalHeaders.concat(result.filter(function(obj) { return obj.type === "categorical" || obj.type === "both"; }).map(function(obj) { return obj.name; }));

    addCorrGroup("mian-none", "None Selected");

    $("#corrvar1").empty();
    $("#corrvar2").empty();
    $("#sizevar").empty();
    $("#colorvar").empty();

    addCorrOption("corrvar1", "mian-taxonomy-abundance", "Taxonomy Abundance");
    addCorrOption("corrvar2", "mian-taxonomy-abundance", "Taxonomy Abundance");

    for (var i = 0; i < numericHeaders.length; i++) {
        if (i != 0) {
            addCorrOption("corrvar1", numericHeaders[i], numericHeaders[i]);
            addCorrOption("corrvar2", numericHeaders[i], numericHeaders[i]);
        }
        addCorrOption("sizevar", numericHeaders[i], numericHeaders[i]); // Optional field so includes the "None"
    }

    for (var i = 0; i < allHeaders.length; i++) {
        addCorrOption("colorvar", allHeaders[i], allHeaders[i]);
    }

    addCorrGroup("mian-abundance", "Aggregate Abundance");
    addCorrGroup("mian-max", "Max Abundance");

    if (initialCorrvar1) {
        $("#corrvar1").val(initialCorrvar1);
        initialCorrvar1 = null;
    }
    if (initialCorrvar2) {
        $("#corrvar2").val(initialCorrvar2);
        initialCorrvar2 = null;
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

function addCorrGroup(val, text) {
    addCorrOption("corrvar1", val, text);
    addCorrOption("corrvar2", val, text);
    addCorrOption("sizevar", val, text);
    addCorrOption("colorvar", val, text);
}

function addCorrOption(elemID, val, text) {
    var o = document.createElement("option");
    o.setAttribute("value", val);
    var t = document.createTextNode(text);
    if (val == "Abundances") {
        t = document.createTextNode("Aggregate Abundances");
    }
    o.appendChild(t);
    document.getElementById(elemID).appendChild(o);
}
