// ============================================================
// Beta Diversity Boxplot JS Component
// ============================================================

var expectedLoadFactor = 100;

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
var initialColorVar = getParameterByName("colorvar");
var initialStrata = getParameterByName("strata") ? getParameterByName("strata") : "";
function initializeFields() {
    if (getParameterByName("betaType") !== null) {
        $("#betaType").val(getParameterByName("betaType"));
    }
    if (getParameterByName("numPermutations") !== null) {
        $("#numPermutations").val(getParameterByName("numPermutations"));
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

    $("#strata").change(function() {
        updateAnalysis();
    });

    $("#betaType").change(function() {
        updateAnalysis();
    });

    $("#numPermutations").change(function() {
        updateAnalysis();
    });

    $("#download-svg").click(function() {
        downloadSVG("beta.diversity." + $("#catvar").val() + "." + $("#strata").val() + "." + $("#betaType").val());
    });

    $("#save-to-notebook").click(function() {
        saveSVGToNotebook("Beta Diversity (" + $("#catvar").val() + ")", "Taxonomic Level: " + $("#taxonomy option:selected").text() + "\n" + "Strata Variable: " + $("#strata").val() + "\n" + "Diversity Type: " + $("#betaType option:selected").text() + "\n");
    });
}

//
// Analysis Specific Methods
//
function updateAnalysis() {
    if (!loaded) {
        return;
    }
    showLoading(expectedLoadFactor);
    $("#permanova-loading").show();
    $("#permanova").empty();
    $("#betadisper").empty();

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
    var numPermutations = $("#numPermutations").val();
    var colorvar = $("#colorvar").val();

    if (!catvar || catvar === "none") {
        loadNoResults();
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
        strata: strata,
        betaType: betaType,
        numPermutations: numPermutations,
        colorvar: colorvar
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/beta_diversity" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            var abundancesObj = JSON.parse(result);
            if (abundancesObj["timeout"]) {
                loadError("This can occur if your data set is very large. Consider using a file with fewer OTUs or samples, or by using fewer permutations. <a href='#'>Learn more here.</a>", "Maximum Running Time Exceeded");
            } else if (abundancesObj["no_tree"]) {
                loadNoTree();
            } else if (abundancesObj["has_float"]) {
                loadFloatDataWarning();
            } else if ($.isEmptyObject(abundancesObj.abundances)) {
                loadNoResults();
            } else {
                loadSuccess();

                renderBoxplots(abundancesObj, "", "Beta Diversity (Distance to Centroid)");
                renderBetadisper(abundancesObj);
                $("#permanova-container").show();
            }
        },
        error: function(err) {
            loadError();
            console.log(err);
        }
    });

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/beta_diversity_permanova" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            var abundancesObj = JSON.parse(result);
            if (abundancesObj["timeout"]) {
                $("#permanova-container").hide();
                $("#permanova-loading").hide();
            } else {
                renderPERMANOVA(abundancesObj);
            }
        },
        error: function(err) {
            $("#permanova-container").hide();
            $("#permanova-loading").hide();
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
    $("#permanova-loading").hide();
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


function customCatVarCallback(result) {
    var allHeaders = ["None"].concat(result.map(function(obj) { return obj.name; }));

    var categoricalHeaders = [
        "None"
    ];
    categoricalHeaders = categoricalHeaders.concat(result.filter(function(obj) { return obj.type === "categorical" || obj.type === "both"; }).map(function (obj) { return obj.name; }));

    $("#strata").empty();

    for (var i = 0; i < categoricalHeaders.length; i++) {
        if (initialStrata && categoricalHeaders[i] == initialStrata) {
            $("#strata").append('<option value="' + categoricalHeaders[i] + '" selected>' + categoricalHeaders[i] + '</option>');
            initialStrata = null;
        } else {
            $("#strata").append('<option value="' + categoricalHeaders[i] + '">' + categoricalHeaders[i] + '</option>');
        }
    }

    //
    // Renders the experimental variable
    //
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
