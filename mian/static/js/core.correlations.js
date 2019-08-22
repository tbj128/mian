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
var initialSizeVarSpecificTaxonomies = getParameterByName("sizevarSpecificTaxonomies") ? JSON.parse(getParameterByName("sizevarSpecificTaxonomies")) : [];
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
            showTaxonomyInput(1);
            $.when(loadOTUTableHeaders("corrvar1")).done(function() {
                updateAnalysis();
            });
        } else if ($("#corrvar1").val() === "mian-gene") {
            showGeneInput(1);
            $.when(loadGeneSelector(1)).done(function() {
                updateAnalysis();
            });
        } else if ($("#corrvar1").val() === "mian-alpha") {
            showAlphaInput(1);
            updateAnalysis();
        } else {
            hideInput(1);
            updateAnalysis();
        }
    });

    $("#corrvar2").change(function() {
        if ($("#corrvar2").val() === "mian-taxonomy-abundance") {
            showTaxonomyInput(2);
            $.when(loadOTUTableHeaders("corrvar2")).done(function() {
                updateAnalysis();
            });
        } else if ($("#corrvar2").val() === "mian-gene") {
            showGeneInput(2);
            $.when(loadGeneSelector(2)).done(function() {
                updateAnalysis();
            });
        } else if ($("#corrvar2").val() === "mian-alpha") {
            showAlphaInput(2);
            updateAnalysis();
        } else {
            hideInput(2);
            updateAnalysis();
        }
    });

    $("#colorvar").change(function() {
        updateAnalysis();
    });

    $("#sizevar").change(function() {
        if ($("#sizevar").val() === "mian-alpha") {
            $("#alpha-diversity-container-3").show();
        } else {
            $("#alpha-diversity-container-3").hide();
        }
        updateAnalysis();
    });

    $("#samplestoshow").change(function() {
        updateAnalysis();
    });

    $(".alpha-context").change(function() {
        updateAnalysis();
    });

    $(".alpha-type").change(function() {
        updateAnalysis();
    });

    $("#specific-taxonomy-typeahead-1").change(function() {
        if (initialCorrvar1SpecificTaxonomies == null) {
            // Avoids unnecessary updateAnalysis calls during the initial set-up
            updateAnalysis();
        }
    });

    $("#specific-taxonomy-typeahead-2").change(function() {
        if (initialCorrvar2SpecificTaxonomies == null) {
            // Avoids unnecessary updateAnalysis calls during the initial set-up
            updateAnalysis();
        }
    });

    $("#gene-typeahead-1").change(function() {
        if (initialCorrvar1SpecificTaxonomies == null) {
            // Avoids unnecessary updateAnalysis calls during the initial set-up
            updateAnalysis();
        }
    });

    $("#gene-typeahead-2").change(function() {
        if (initialCorrvar2SpecificTaxonomies == null) {
            // Avoids unnecessary updateAnalysis calls during the initial set-up
            updateAnalysis();
        }
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
        downloadSVG("correlations." + $("#corrvar1").val() + "." + $("#corrvar2").val());
    });
}

//
// Analysis Specific Methods
//

function customCatVarCallback(json) {
    updateCorrVar(json);
}

function customCatVarValueLoading() {
    return $.when(loadOTUTableHeaders(), loadGeneSelector(1)).then(function() {
        // To prevent two requests for the gene selector file, we call the second load only after the
        // genes have been cached
        loadGeneSelector(2);

        if (initialCorrvar1SpecificTaxonomies) {
            initialCorrvar1SpecificTaxonomies.forEach(function(val, i) {
                if ($("#corrvar1").val() === "mian-taxonomy-abundance") {
                    $("#specific-taxonomy-typeahead-1").tagsinput('add', val);
                } else if ($("#corrvar1").val() === "mian-gene") {
                    $("#gene-typeahead-1").tagsinput('add', val);
                } else if ($("#corrvar1").val() === "mian-alpha") {
                    if (i == 0) {
                        $("#alphaContext1").val(val);
                    } else {
                        $("#alphaType1").val(val);
                    }
                }
            });
            initialCorrvar1SpecificTaxonomies = null;
        }

        if (initialCorrvar2SpecificTaxonomies) {
            initialCorrvar2SpecificTaxonomies.forEach(function(val, i) {
                if ($("#corrvar2").val() === "mian-taxonomy-abundance") {
                    $("#specific-taxonomy-typeahead-2").tagsinput('add', val);
                } else if ($("#corrvar2").val() === "mian-gene") {
                    $("#gene-typeahead-2").tagsinput('add', val);
                } else if ($("#corrvar2").val() === "mian-alpha") {
                    if (i == 0) {
                        $("#alphaContext2").val(val);
                    } else {
                        $("#alphaType2").val(val);
                    }
                }
            });
            initialCorrvar2SpecificTaxonomies = null;
        }

        if (initialSizeVarSpecificTaxonomies) {
            initialSizeVarSpecificTaxonomies.forEach(function(val, i) {
                if ($("#sizevar").val() === "mian-alpha") {
                    if (i == 0) {
                        $("#alphaContext3").val(val);
                    } else {
                        $("#alphaType3").val(val);
                    }
                }
            });
            initialSizeVarSpecificTaxonomies = null;
        }
    });
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

    var corrvar1SpecificTaxonomies = "";
    if (corrvar1 === "mian-gene") {
        corrvar1SpecificTaxonomies = $("#gene-typeahead-1").val();
    } else if (corrvar1 === "mian-taxonomy-abundance") {
        corrvar1SpecificTaxonomies = $("#specific-taxonomy-typeahead-1").val();
    } else if (corrvar1 === "mian-alpha") {
        corrvar1SpecificTaxonomies = $("#alphaContext1").val() + "," + $("#alphaType1").val();
    }

    var corrvar2SpecificTaxonomies = "";
    if (corrvar2 === "mian-gene") {
        corrvar2SpecificTaxonomies = $("#gene-typeahead-2").val();
    } else if (corrvar2 === "mian-taxonomy-abundance") {
        corrvar2SpecificTaxonomies = $("#specific-taxonomy-typeahead-2").val();
    } else if (corrvar2 === "mian-alpha") {
        corrvar2SpecificTaxonomies = $("#alphaContext2").val() + "," + $("#alphaType2").val();
    }

    var sizevarSpecificTaxonomies = "";
    if (sizevar === "mian-alpha") {
        sizevarSpecificTaxonomies = $("#alphaContext3").val() + "," + $("#alphaType3").val();
    }


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

    if (sizevarSpecificTaxonomies === "") {
        sizevarSpecificTaxonomies = JSON.stringify([]);
    } else {
        sizevarSpecificTaxonomies = JSON.stringify(
            sizevarSpecificTaxonomies.split(",")
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
        corrvar2SpecificTaxonomies: corrvar2SpecificTaxonomies,
        sizevarSpecificTaxonomies: sizevarSpecificTaxonomies
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

                renderCorrelations(abundancesObj, getInputValsAsFormattedString(1), getInputValsAsFormattedString(2));
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

    addCorrOption("corrvar1", "mian-taxonomy-abundance", "OTU or Taxonomic Group Abundance");
    addCorrOption("corrvar2", "mian-taxonomy-abundance", "OTU or Taxonomic Group Abundance");

    addCorrOption("corrvar1", "mian-gene", "Gene Expression");
    addCorrOption("corrvar2", "mian-gene", "Gene Expression");

    addCorrOption("corrvar1", "mian-alpha", "Alpha Diversity");
    addCorrOption("corrvar2", "mian-alpha", "Alpha Diversity");

    for (var i = 0; i < numericHeaders.length; i++) {
        if (i != 0) {
            addCorrOption("corrvar1", numericHeaders[i], numericHeaders[i]);
            addCorrOption("corrvar2", numericHeaders[i], numericHeaders[i]);
        }
        addCorrOption("sizevar", numericHeaders[i], numericHeaders[i]); // Optional field so includes the "None"
    }
    addCorrOption("sizevar", "mian-alpha", "Alpha Diversity");

    for (var i = 0; i < allHeaders.length; i++) {
        addCorrOption("colorvar", allHeaders[i], allHeaders[i]);
    }

    addCorrGroup("mian-abundance", "Aggregate OTU or Taxonomic Group Abundance");
    addCorrGroup("mian-max", "Max OTU or Taxonomic Group Abundance");

    if (initialCorrvar1) {
        $("#corrvar1").val(initialCorrvar1);
        if ($("#corrvar1").val() === "mian-taxonomy-abundance") {
            showTaxonomyInput(1);
        } else if ($("#corrvar1").val() === "mian-gene") {
            showGeneInput(1);
        } else if ($("#corrvar1").val() === "mian-alpha") {
            showAlphaInput(1);
        } else {
            hideInput(1);
        }
        initialCorrvar1 = null;
    }

    if (initialCorrvar2) {
        $("#corrvar2").val(initialCorrvar2);
        if ($("#corrvar2").val() === "mian-taxonomy-abundance") {
            showTaxonomyInput(2);
        } else if ($("#corrvar2").val() === "mian-gene") {
            showGeneInput(2);
        } else if ($("#corrvar2").val() === "mian-alpha") {
            showAlphaInput(2);
        } else {
            hideInput(2);
        }
        initialCorrvar2 = null;
    }

    if (initialColorVar) {
        $("#colorvar").val(initialColorVar);
        initialColorVar = null;
    }

    if (initialSizeVar) {
        $("#sizevar").val(initialSizeVar);
        if ($("#sizevar").val() === "mian-alpha") {
            $("#alpha-diversity-container-3").show();
        }
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

function showTaxonomyInput(index) {
    $("#specific-taxonomy-container-" + index).show();
    $("#gene-input-container-" + index).hide();
    $("#taxonomic-level-container").show();
    $("#alpha-diversity-container-" + index).hide();
}

function showGeneInput(index) {
    $("#specific-taxonomy-container-" + index).hide();
    $("#gene-input-container-" + index).show();
    $("#taxonomic-level-container").hide();
    $("#alpha-diversity-container-" + index).hide();
}

function showAlphaInput(index) {
    $("#specific-taxonomy-container-" + index).hide();
    $("#gene-input-container-" + index).hide();
    $("#taxonomic-level-container").hide();
    $("#alpha-diversity-container-" + index).show();
}

function hideInput(index) {
    $("#specific-taxonomy-container-" + index).hide();
    $("#gene-input-container-" + index).hide();
    $("#taxonomic-level-container").hide();
    $("#alpha-diversity-container-" + index).hide();
}

function getInputValsAsFormattedString(index) {
    var val = $("#corrvar" + index).val();
    if ($("#corrvar" + index).val() === "mian-taxonomy-abundance") {
        val = $("#specific-taxonomy-typeahead-" + index).val();
    } else if ($("#corrvar" + index).val() === "mian-gene") {
        val = $("#gene-typeahead-" + index).val();
    } else if ($("#corrvar" + index).val() === "mian-alpha") {
        val = $("#corrvar" + index + " option:selected").text();
    }
    if (val.length > 36) {
        return val.substring(0, 36) + "...";
    } else {
        return val;
    }
}
