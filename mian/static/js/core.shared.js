// ================================================================================
// Global Variables
//
var MINIMUM_FOR_TYPEAHEAD_MODE = 300;

var taxonomyLevels = {
    Kingdom: 0,
    Phylum: 1,
    Class: 2,
    Order: 3,
    Family: 4,
    Genus: 5,
    Species: 6,
    OTU: -1
};
var taxonomyLevelsReverseLookup = {
    "0": "Kingdom",
    "1": "Phylum",
    "2": "Class",
    "3": "Order",
    "4": "Family",
    "5": "Genus",
    "6": "Species",
    "-1": "OTU",
    "-2": "none"
};
var taxonomiesMap = {};
var headersWithType = {};
var headersWithQuantileStatus = {};
var quantiles = {};
var quantileStaging = {};
var quantileResultStaging = {};
var loaded = false;

//
// Sets the initial field values based on the URL
//
if (getParameterByName("taxonomyFilter")) {
    $("#filter-otu").val(taxonomyLevelsReverseLookup[getParameterByName("taxonomyFilter")]);
    if ($("#filter-otu").val() === "none") {
        $("#filter-otu-wrapper").hide();
    } else {
        $("#filter-otu-wrapper").show();
        $('#dataFiltering').collapse('show');
    }
}

// Set the "Include" or "Exclude" role from the URL params
if (getParameterByName("taxonomyFilterRole")) {
    $("#taxonomy-typeahead-btn .typeahead-role").text(getParameterByName("taxonomyFilterRole"));
}

if (getParameterByName("taxonomyFilterCount")) {
    $("#taxonomyFilterCount").val(getParameterByName("taxonomyFilterCount"));
}

if (getParameterByName("taxonomyFilterPrevalence")) {
    $("#taxonomyFilterPrevalence").val(getParameterByName("taxonomyFilterPrevalence"));
}

if (getParameterByName("level") !== null) {
    $("#taxonomy").val(taxonomyLevelsReverseLookup[getParameterByName("level")]);
}
if (getParameterByName("pid") !== null) {
    $("#project").val(getParameterByName("pid"));
}

var initialCatvar = getParameterByName("catvar");
var initialSampleFilter = getParameterByName("sampleFilter");
var initialSampleFilterVals = getParameterByName("sampleFilterVals") ? JSON.parse(getParameterByName("sampleFilterVals")) : [];
if (getParameterByName("sampleFilterRole")) {
    $("#sample-typeahead-btn .typeahead-role").text(getParameterByName("sampleFilterRole"));
    initialSampleFilterRole = null;
}

// Global cache of the "Category Breakdown" values
var catVars = [];
var hasCatVar;
var hasCatVarNoneOption;

// ================================================================================
// Global Initialization
//
//
function initializeComponent(catVarOptions) {
    console.log("Initializing component");

    // Popovers
    $('[data-toggle="popover"]')
        .popover({
            html: true,
            placement: "right",
            container: "body",
            trigger: "manual",
            animation: false
        })
        .on("mouseenter", function() {
            var _this = this;
            $(this).popover("show");
            $(".popover").on("mouseleave", function() {
                $(_this).popover("hide");
            });
        })
        .on("mouseleave", function() {
            var _this = this;
            setTimeout(function() {
                if (!$(".popover:hover").length) {
                    $(_this).popover("hide");
                }
            }, 300);
        });

    hasCatVar = catVarOptions ? catVarOptions.hasCatVar : false;
    hasCatVarNoneOption = catVarOptions ?
        catVarOptions.hasCatVarNoneOption :
        false;

    createGlobalSidebarListeners();
    createGlobalVisualizationListeners();
    handleGlobalURLParams();

    resetProject();
}

// ================================================================================
// Globally Accessible Helper Methods
//

function getSharedPrefixIfNeeded() {
    if ($("#isShared").val() === "True") {
        return "/share"
    } else {
        return "";
    }
}

function getSharedUserSuffixIfNeeded() {
    if ($("#isShared").val() === "True") {
        return "&uid=" + getParameterByName("uid")
    } else {
        return "";
    }
}

function getSharedUserProjectSuffixIfNeeded() {
    if ($("#isShared").val() === "True") {
        return "?uid=" + getParameterByName("uid") + "&pid=" + getParameterByName("pid")
    } else {
        return "";
    }
}

function shareToBoxplotLink(otu_name) {
    var specificTaxonomy = getSpecificTaxonomy(otu_name);
    return "/boxplots?pid=" + getParameterByName("pid") + "&taxonomyFilter=" + getParameterByName("taxonomyFilter") + "&taxonomyFilterRole=" + getParameterByName("taxonomyFilterRole") + "&taxonomyFilterVals=" + getParameterByName("taxonomyFilterVals") + "&sampleFilter=" + getParameterByName("sampleFilter") + "&sampleFilterRole=" + getParameterByName("sampleFilterRole") + "&sampleFilterVals=" + getParameterByName("sampleFilterVals") + "&catvar=" + (getParameterByName("expvar") ? getParameterByName("expvar") : getParameterByName("catvar")) + "&yvals=mian-taxonomy-abundance&level=" + getParameterByName("level") + "&yvalsSpecificTaxonomy=[\"" + specificTaxonomy + "\"]";
}

function shareToCorrelationsLink(otu_name1, otu_name2) {
    var specificTaxonomy1 = getSpecificTaxonomy(otu_name1);
    var specificTaxonomy2 = otu_name2;
    return "/correlations?pid=" + getParameterByName("pid") + "&taxonomyFilter=" + getParameterByName("taxonomyFilter") + "&taxonomyFilterRole=" + getParameterByName("taxonomyFilterRole") + "&taxonomyFilterVals=" + getParameterByName("taxonomyFilterVals") + "&sampleFilter=" + getParameterByName("sampleFilter") + "&sampleFilterRole=" + getParameterByName("sampleFilterRole") + "&sampleFilterVals=" + getParameterByName("sampleFilterVals") + "&catvar=" + (getParameterByName("expvar") ? getParameterByName("expvar") : getParameterByName("catvar")) + "&corrvar1=mian-taxonomy-abundance&corrvar2=" + specificTaxonomy2 + "&level=" + getParameterByName("level") + "&corrvar1SpecificTaxonomies=[\"" + specificTaxonomy1 + "\"]" + "&corrvar2SpecificTaxonomies=[\"" + specificTaxonomy2 + "\"]";
}

function getSpecificTaxonomy(otu_name) {
    var otuArr = otu_name.split("; ");
    if (otuArr.length === 1) {
        otuArr = otu_name.split("..");
    }
    var specificTaxonomy = otuArr[otuArr.length - 1];
    return specificTaxonomy;
}

function getNumSamplesCurrentProject() {
    return parseInt($("#num_samples-" + $("#project").val()).val());
}

function getNumOTUsCurrentProject() {
    return parseInt($("#num_otus-" + $("#project").val()).val());
}

function showLoading(expectedLoadFactor, useTaxonomicOnly) {
    showFilteringAppliedNotification();

    loaded = false;
    var numSamples = getNumSamplesCurrentProject();
    var numOTUs = getNumOTUsCurrentProject();
    if (expectedLoadFactor) {
        var expectedLoadTime = numSamples * numOTUs / expectedLoadFactor;
        if (useTaxonomicOnly) {
            expectedLoadTime = numOTUs / expectedLoadFactor;
        }

        if (expectedLoadTime > 1000 ) {
            console.log("Expected load time is " + expectedLoadTime);
            $('#progress').css('width',  "0%");
            $("#progress").show();
            $({property: 0}).animate({property: 75}, {
                duration: expectedLoadTime,
                step: function() {
                    if (!loaded) {
                        var p = Math.round(this.property);
                        $('#progress').css('width',  p + "%");
                    }
                },
                complete: function() {
                }
            });
        }
    }

    $("#loading").show();
    $("#editor :input").prop("disabled", true);
}

function hideLoading() {
    loaded = true;
    $("#loading").hide();
    $("#editor :input").prop("disabled", false);

    var currentProgress = ($("#progress").width() / $('#progress').parent().width()) * 100;
    $({property: currentProgress}).animate({property: 105}, {
        duration: 500,
        step: function() {
            var p = Math.round(this.property);
            $('#progress').css('width',  p + "%");
        },
        complete: function() {
            setTimeout(function() {
                $("#progress").hide();
            }, 1000);
        }
    });
}

function showFilteringAppliedNotification() {
    if (($("#countthreshold").length > 0 && $("#countthreshold").val() > 0)
        || ($("#prevalence").length > 0 && $("#prevalence").val() > 0)
        || $("#filter-otu").val() !== "none"
        || $("#filter-sample").val() !== "none") {
        $(".applied-indicator").show();
    } else {
        $(".applied-indicator").hide();
    }
}

function hideNotifications() {
    $(".display-notification").hide();
}

function showNoCatvar() {
    $("#display-no-catvar").show();
}

function loadError(details) {
    hideLoading();
    $("#display-error").show();
    $("#display-error-details").empty();
    $("#display-no-results").hide();
    $("#display-no-catvar").hide();
    $("#display-no-tree").hide();
    $("#display-float-data").hide();
    $("#download-container").hide();
    $("#analysis-container").hide();
    $("#stats-container").hide();

    if (details) {
        $("#display-error-details").html(details + " ");
    }
}

function loadNoResults() {
    hideLoading();
    $("#display-error").hide();
    $("#display-no-results").show();
    $("#display-no-catvar").hide();
    $("#display-no-tree").hide();
    $("#display-float-data").hide();
    $("#download-container").hide();
    $("#analysis-container").hide();
    $("#stats-container").hide();
}

function loadSuccess() {
    hideLoading();
    $("#display-error").hide();
    $("#display-no-results").hide();
    $("#display-no-catvar").hide();
    $("#display-no-tree").hide();
    $("#display-float-data").hide();
    $("#download-container").show();
    $("#analysis-container").show();
    $("#stats-container").show();
}

function loadNoCatvar() {
    hideLoading();
    $("#display-error").hide();
    $("#display-no-results").hide();
    $("#display-no-catvar").show();
    $("#display-no-tree").hide();
    $("#display-float-data").hide();
    $("#download-container").hide();
    $("#analysis-container").hide();
    $("#stats-container").hide();
}

function loadNoTree() {
    hideLoading();
    $("#display-error").hide();
    $("#display-no-results").hide();
    $("#display-no-catvar").hide();
    $("#display-no-tree").show();
    $("#display-float-data").hide();
    $("#download-container").hide();
    $("#analysis-container").hide();
    $("#stats-container").hide();
}

function loadFloatDataWarning() {
    hideLoading();
    $("#display-error").hide();
    $("#display-no-results").hide();
    $("#display-no-catvar").hide();
    $("#display-no-tree").hide();
    $("#display-float-data").show();
    $("#download-container").hide();
    $("#analysis-container").hide();
    $("#stats-container").hide();
}

function showNoResults() {
    $("#display-no-results").show();
}

function setExtraNavLinks(attr) {
    $(".nav-link").each(function() {
        var currHref = $(this).attr("href");
        var currHrefArr = currHref.split("?");
        if (currHrefArr.length > 1) {
            currHref = currHrefArr[0];
        }
        var uid = getParameterByName("uid");
        if (uid) {
            $(this).attr("href", currHref + "?pid=" + attr + "&uid=" + uid);
        } else {
            $(this).attr("href", currHref + "?pid=" + attr);
        }
    });
}

function getTaxonomicLevel() {
    return $("#taxonomy").val();
}

function getSelectedTaxFilter() {
    var taxLevel = $("#filter-otu").val();
    if (taxLevel === "none") {
        return -2;
    }
    return taxonomyLevels[taxLevel];
}

function getSelectedTaxFilterRole() {
    var taxTypeaheadFilterVisible = $("#taxonomy-specific-typeahead-wrapper").is(
        ":visible"
    );
    if (!taxTypeaheadFilterVisible) {
        // We are not using typeahead so we are always an "include" filter
        return "Include";
    } else {
        var typeaheadRole = $("#taxonomy-typeahead-btn .typeahead-role").text();
        return typeaheadRole;
    }
}

function getSelectedTaxFilterVals() {
    var taxLevel = $("#filter-otu").val();
    if (taxLevel === "none") {
        // Filtering is not enabled
        return JSON.stringify([]);
    }

    var taxTypeaheadFilterVisible = $("#taxonomy-specific-typeahead-wrapper").is(
        ":visible"
    );
    if (taxTypeaheadFilterVisible) {
        var taxTypeaheadFilter = $("#taxonomy-typeahead-filter").val();
        return JSON.stringify(taxTypeaheadFilter.split(","));
    } else {
        var taxonomy = $("#taxonomy-specific").val();
        if (taxonomy == null) {
            taxonomy = [];
        }

        if ($("#taxonomy-specific option").size() === taxonomy.length) {
            // Select all is enabled
            return JSON.stringify(["mian-select-all"]);
        }

        return JSON.stringify(taxonomy);
    }
}

function getLowCountThreshold() {
    return $("#countthreshold").val();
}

function getPrevalenceThreshold() {
    return $("#prevalence").val();
}

function getSelectedSampleFilter() {
    var filter = $("#filter-sample").val();
    return filter;
}

function getSelectedSampleFilterRole() {
    var sampleTypeaheadFilterVisible = $("#sample-specific-typeahead-wrapper").is(
        ":visible"
    );
    if (!sampleTypeaheadFilterVisible) {
        // We are not using typeahead so we are always an "include" filter
        return "Include";
    } else {
        var typeaheadRole = $("#sample-typeahead-btn .typeahead-role").text();
        return typeaheadRole;
    }
}

function getSelectedSampleFilterVals() {
    if ($("filter-sample").val() === "none") {
        // Filtering not enabled
        return JSON.stringify([]);
    }

    var sampleTypeaheadFilterVisible = $("#sample-specific-typeahead-wrapper").is(
        ":visible"
    );
    if (sampleTypeaheadFilterVisible) {
        var sampleTypeaheadFilter = $("#sample-typeahead-filter").val();
        return JSON.stringify(sampleTypeaheadFilter.split(","));
    } else {
        var samples = $("#filter-sample-specific").val();
        if (samples == null) {
            samples = [];
        }

        return JSON.stringify(samples);
    }
}

function updateFilterOTUOptions() {
    console.log("Detected filter OTU change");
    var filterVal = $("#filter-otu").val();
    if (filterVal === "none") {
        $("#filter-otu-wrapper").hide();
    } else {
        $("#filter-otu-wrapper").show();
        updateTaxonomicLevel(false);
    }
}

function updateFilterSamplesOptions() {
    var filterVal = $("#filter-sample").val();
    if (filterVal === "none") {
        $("#filter-sample-wrapper").hide();
    } else {
        $("#filter-sample-wrapper").show();
        getSampleFilteringOptions();
    }
}

function getSampleFilteringOptions(isSync) {
    $.ajax({
        url: getSharedPrefixIfNeeded() + "/metadata_vals?pid=" +
            $("#project").val() +
            "&catvar=" +
            $("#filter-sample").val() +
            getSharedUserSuffixIfNeeded(),
        async: isSync ? false : true,
        success: function(result) {
            var json = JSON.parse(result);

            var $filterSampleSpecific = $("#filter-sample-specific");

            var options = [];

            if (json.length < MINIMUM_FOR_TYPEAHEAD_MODE) {
                $("#sample-specific-typeahead-wrapper").hide();
                $("#sample-typeahead-filter").val("");

                for (var i = 0; i < json.length; i++) {
                    var option = {
                        label: json[i],
                        title: json[i],
                        value: json[i],
                        selected: initialSampleFilterVals && (initialSampleFilterVals.indexOf("mian-select-all") > -1 || initialSampleFilterVals.indexOf(json[i]) > -1)
                    };
                    options.push(option);
                }
                var outWidth = $("#project").outerWidth();
                $filterSampleSpecific.multiselect({
                    buttonWidth: outWidth ? outWidth + "px" : "320px",
                    includeSelectAllOption: true,
                    enableFiltering: true,
                    maxHeight: 400
                });

                $filterSampleSpecific.multiselect("dataprovider", options);

                // Resets the params from the URL
                if (initialSampleFilterVals) {
                    initialSampleFilterVals = null;
                }
            } else {
                console.log("Loading typeahead sample filter");
                $("#sample-typeahead-filter").tagsinput("destroy");
                $("#filter-sample-specific").multiselect("destroy");
                $("#filter-sample-specific").hide();

                $("#sample-typeahead-filter").tagsinput({
                    freeInput: false,
                    placeholderText: "Enter",
                    typeahead: {
                        source: json,
                        afterSelect: function() {
                            $("#sample-typeahead-filter")
                                .tagsinput("input")
                                .val("");
                        }
                    }
                });

                // Add default selected based on URL
                if (initialSampleFilterVals) {
                    initialSampleFilterVals.forEach(function(val) {
                        $("#taxonomy-typeahead-filter").tagsinput('add', val);
                    });
                }
                $("#sample-specific-typeahead-wrapper").show();
            }
        }
    });
}

function resetProject() {
    taxonomiesMap = {};

    // We must wait for all the sidebar components to finish updating before we can render the analysis component
    if (hasCatVar && typeof customLoading === "function") {
        $.when(
            updateTaxonomicLevel(true, function() {}),
            updateCatVar(function() {}),
            customLoading()
        ).done(function(a1, a2, a3) {
            updateProject();
        });
    } else if (hasCatVar) {
        $.when(
            updateTaxonomicLevel(true, function() {}),
            updateCatVar(function() {})
        ).done(function(a1, a2, a3) {
            updateProject();
        });
    } else if (typeof customLoading === "function") {
        $.when(updateTaxonomicLevel(true, function() {}), customLoading()).done(
            function(a1, a2, a3) {
                updateProject();
            }
        );
    } else {
        updateTaxonomicLevel(true, function() {
            updateProject();
        });
    }
}

function updateProject() {
    if (typeof customLoadingCallback === "function") {
        customLoadingCallback(catVars);
    }
    showOrHideQuantileManageContainer();
    updateAnalysis();
}

// ===========================================================================
// URL Shared
//
function handleGlobalURLParams() {
    var params = decodeURIComponent(window.location.search.substring(1));
    if (params != undefined && params != "") {
        var paramsArr = params.split("&");
        for (var i = 0; i < paramsArr.length; i++) {
            var param = paramsArr[i];
            var paramSplit = param.split("=");
            if (paramSplit.length == 2 && paramSplit[0] === "pid") {
                setExtraNavLinks(paramSplit[1]);
            }
        }
    }
}

// ===========================================================================
// Sidebar Shared
//

// Sidebar Common Listeners
function createGlobalSidebarListeners() {
    $("#project").change(function() {
        resetProject();
        setExtraNavLinks($("#project").val());
    });

    $("#filter-sample").change(function() {
        updateFilterSamplesOptions();
        updateAnalysis();
    });

    $("#filter-otu").change(function() {
        updateFilterOTUOptions();
        updateAnalysis();
    });

    $("#taxonomy").change(function() {
        updateAnalysis();
    });

    $("#taxonomy-specific").change(function() {
        updateAnalysis();
    });

    $("#countthreshold").change(function() {
        updateAnalysis();
    });

    $("#prevalence").change(function() {
        updateAnalysis();
    });

    $("#taxonomy-typeahead-btn a").on("click", function() {
        var intent = $(this).data("intent");
        $("#taxonomy-typeahead-btn .typeahead-role").text(intent);
        updateAnalysis();
    });

    $("#taxonomy-typeahead-filter").change(function() {
        updateAnalysis();
    });

    $("#filter-sample-specific").change(function() {
        updateAnalysis();
    });

    $("#sample-typeahead-btn a").on("click", function() {
        var intent = $(this).data("intent");
        $("#sample-typeahead-btn .typeahead-role").text(intent);
        updateAnalysis();
    });

    $("#sample-typeahead-filter").change(function() {
        updateAnalysis();
    });
}

function createGlobalVisualizationListeners() {
    $("#share").click(function() {
        setGetParameters({
            "uid": $("#uid").val()
        });

        $.ajax({
            url: "/get_sharing_status?pid=" + $("#project").val(),
            success: function(result) {
                var obj = JSON.parse(result);
                if (obj["share"] === "yes") {
                    $("#sharing-switch input").prop('checked', true);
                    $("#sharing-link-container").show();
                    $("#sharing-switch-text").text("Link sharing is on");
                } else {
                    $("#sharing-switch input").prop('checked', false);
                    $("#sharing-link-container").hide();
                    $("#sharing-switch-text").text("Link sharing is off");
                }
            }
        });
        $("#sharing-link-input").val(window.location.protocol + "//" + window.location.host + "/share" + window.location.pathname + window.location.search);
    });
    $("#sharing-link-input").focus(function() {
        this.select();
    });
    $("#sharing-switch input").change(function() {
        if ($("#sharing-switch input").is(':checked')) {
            $("#sharing-link-container").show();
            $("#sharing-switch-text").text("Link sharing is on");

            $.ajax({
                url: "/toggle_sharing?pid=" + $("#project").val() + "&share=yes",
                success: function(result) {
                    console.log("Sharing enabled")
                }
            });
        } else {
            $("#sharing-link-container").hide();
            $("#sharing-switch-text").text("Link sharing is off");

            $.ajax({
                url: "/toggle_sharing?pid=" + $("#project").val() + "&share=no",
                success: function(result) {
                    console.log("Sharing enabled")
                }
            });
        }
    });
}

function updateCatVar(isNumeric) {
    var catVarPromise = $.ajax({
        url: getSharedPrefixIfNeeded() + "/metadata_headers_with_type?pid=" + $("#project").val() +
            getSharedUserSuffixIfNeeded(),
        success: function(result) {
            var json = JSON.parse(result);

            headersWithType = {};
            json.forEach(header => {
                headersWithType[header.name] = header.type;
                headersWithQuantileStatus[header.name] = header.quantileStatus;
            });

            var headers =
                isNumeric === true ?
                json
                .filter(function(obj) { return obj.type === "numeric" || obj.type === "both"; })
                .map(function(obj) { return obj.name; }) :
                json
                .filter(function(obj) { return obj.type === "categorical" || obj.type === "both" || obj.quantileStatus; })
                .map(function(obj) { return obj.name; });
            var filteringHeaders = json.map(function(obj) { return obj.name});

            var $catvar = $("#catvar");

            if ($catvar.length > 0) {
                $catvar.empty();
                if (hasCatVarNoneOption) {
                    $catvar.append("<option value='none'>None</option>");
                }

                for (var i = 0; i < headers.length; i++) {
                    $catvar.append(
                        "<option value='" + headers[i] + "'>" + headers[i] + "</option>"
                    );
                }
            }

            var $filterSample = $("#filter-sample");
            if ($filterSample.length > 0) {
                $filterSample.empty();
                $filterSample.append("<option value='none'>Don't Filter</option>");
                $filterSample.append(
                    "<option value='mian-sample-id'>Sample ID</option>"
                );

                for (var i = 0; i < filteringHeaders.length; i++) {
                    $filterSample.append(
                        "<option value='" +
                        filteringHeaders[i] +
                        "'>" +
                        filteringHeaders[i] +
                        "</option>"
                    );
                }
            }

            // Set the selected option based on the URL params
            if (initialSampleFilter) {
                $("#filter-sample").val(initialSampleFilter);

                // Reset the initial sample filter (we only want to load it during the first page load)
                initialSampleFilter = null;

                var filterVal = $("#filter-sample").val();
                if (filterVal === "none") {
                    $("#filter-sample-wrapper").hide();
                } else {
                    $("#filter-sample-wrapper").show();
                    $('#dataFiltering').collapse('show');

                    // Make synchronous so that on first load, the updateAnalysis call waits until we have loaded this filter
                    getSampleFilteringOptions(true);
                }
            }

            if (typeof customCatVarCallback === "function") {
                // Callback used to load any additional filtering parameters
                customCatVarCallback(json);
            }

            if (initialCatvar) {
                $("#catvar").val(initialCatvar);
                showOrHideQuantileManageContainer();

                // Reset the initial catvar (we only want to load it during the first page load)
                initialCatvar = null;
            }

            catVars = json;
        }
    });

    if (typeof customCatVarValueLoading === "function") {
        // Loads any additional catvar values
        return catVarPromise.then(customCatVarValueLoading);
    } else {
        return catVarPromise;
    }
}

function updateTaxonomicLevel(firstLoad, callback) {
    console.log("Updating taxonomic level");
    if ($.isEmptyObject(taxonomiesMap)) {
        // Load taxonomy map
        return $.ajax({
            url: getSharedPrefixIfNeeded() + "/taxonomies?pid=" + $("#project").val() +
            getSharedUserSuffixIfNeeded(),
            success: function(result) {
                var json = JSON.parse(result);
                taxonomiesMap = json;
                renderTaxonomicLevel(firstLoad);
                if (callback != null && callback != undefined) {
                    callback();
                }
            }
        });
    } else {
        renderTaxonomicLevel(firstLoad);
        if (callback != null && callback != undefined) {
            callback();
        }
        return null;
    }
}

function renderTaxonomicLevel(firstLoad) {
    console.log("Rendering taxonomic level");
    var taxas = {};

    var level = getSelectedTaxFilter();

    if (getSelectedTaxFilter() < 0) {
        $.each(taxonomiesMap, function(otu, classification) {
            taxas[otu] = true;
        });
    } else {
        $.each(taxonomiesMap, function(otu, classification) {
            if (!taxas.hasOwnProperty(classification[level])) {
                taxas[classification[level]] = true;
            }
        });
    }

    var taxasArr = Object.keys(taxas);
    taxasArr = taxasArr.sort();

    console.log("Number of taxonomies is " + taxasArr.length);

    // Get the taxonomies to filter from the URL params
    var taxonomyFilterVals = getParameterByName("taxonomyFilterVals") ? JSON.parse(getParameterByName("taxonomyFilterVals")) : [];

    if (taxasArr.length < MINIMUM_FOR_TYPEAHEAD_MODE) {
        console.log("Loading regular taxonomy multiselect filter");

        $("#taxonomy-specific-typeahead-wrapper").hide();
        $("#taxonomy-typeahead-filter").val("");

        var $filterOTUSpecific = $("#taxonomy-specific");
        var options = [];
        for (var i = 0; i < taxasArr.length; i++) {
            var option = {
                label: taxasArr[i],
                title: taxasArr[i],
                value: taxasArr[i],
                "selected": firstLoad && (taxonomyFilterVals.indexOf("mian-select-all") > -1 || taxonomyFilterVals.indexOf(taxasArr[i]) > -1)
            };
            options.push(option);
        }

        var outWidth = $("#project").outerWidth();
        $filterOTUSpecific.multiselect({
            buttonWidth: outWidth ? outWidth + "px" : "320px",
            includeSelectAllOption: true,
            enableFiltering: true,
            maxHeight: 400
        });

        $filterOTUSpecific.multiselect("dataprovider", options);
    } else {
        console.log("Loading typeahead taxonomy filter");
        $("#taxonomy-typeahead-filter").val("");
        $("#taxonomy-typeahead-filter").tagsinput("destroy");
        $("#taxonomy-specific").multiselect("destroy");
        $("#taxonomy-specific").hide();

        $("#taxonomy-typeahead-filter").tagsinput({
            freeInput: false,
            typeahead: {
                source: taxasArr,
                afterSelect: function() {
                    $("#taxonomy-typeahead-filter")
                        .tagsinput("input")
                        .val("");
                }
            }
        });

        // Grab the initial values from the URL, if applicable
        if (firstLoad) {
            taxonomyFilterVals.forEach(function(val) {
                $("#taxonomy-typeahead-filter").tagsinput('add', val);
            });
        }

        $("#taxonomy-specific-typeahead-wrapper").show();
    }

    console.log("Finished rendering taxonomic level");
}


//
// Statistics Container Shared
//

function renderPvaluesTable(abundancesObj) {
    $("#stats-container").hide();

    if ($.isEmptyObject(abundancesObj)) {
        return;
    }

    $("#stats-rows").empty();
    var statsArr = abundancesObj["stats"];
    if (statsArr.length == 0) {
        $("#stats-rows").append(
            '<tr><td colspan=3>No p-values could be generated. Try adjusting the search parameters. <br /><i style="color:#999">Try changing the Categorical Variable on the left.</i></td></tr>'
        );
    } else {
        for (var i = 0; i < statsArr.length; i++) {
            $("#stats-rows").append(
                "<tr><td>" +
                statsArr[i]["c1"] +
                "</td> <td>" +
                statsArr[i]["c2"] +
                "</td> <td>" +
                statsArr[i]["pval"] +
                "</td> </tr>"
            );
        }
    }

    $("#stats-container").fadeIn(250);
}


// Shared function used to manipulate the URL params
function setGetParameters(data) {
    var url = window.location.href;
    var hash = location.hash;
    url = url.replace(hash, '');

    Object.keys(data).forEach(function(key) {
        var paramName = key;
        var paramValue = data[key];
        if (paramValue === null || paramValue === undefined) {
            return;
        } else if (typeof paramValue === "object") {
            paramValue = JSON.stringify(paramValue);
        }

        if (url.indexOf(paramName + "=") >= 0) {
            var prefix = url.substring(0, url.indexOf(paramName));
            var suffix = url.substring(url.indexOf(paramName));
            suffix = suffix.substring(suffix.indexOf("=") + 1);
            suffix = (suffix.indexOf("&") >= 0) ? suffix.substring(suffix.indexOf("&")) : "";
            url = prefix + paramName + "=" + paramValue + suffix;
        } else {
            if (url.indexOf("?") < 0)
                url += "?" + paramName + "=" + paramValue;
            else
                url += "&" + paramName + "=" + paramValue;
        }
    });

    url = "?" + url.split(/\?(.+)/)[1];

    var state = {},
        title = document.title,
        path = url + hash;

    history.pushState(state, title, path);
}

// Shared function used to get the URL parameters
function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, '\\$&');
    var regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)'),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, ' '));
}

function downloadSVG(name) {
    $("#donwload-canvas").empty();
    var svgsElems = $("#analysis-container").children();
    var svgElemWidth = $("#analysis-container svg").width();
    var svgContainerWidth = svgElemWidth;

    var pixelRatio = window.devicePixelRatio || 1;

    var $tmpCanvas = $("#donwload-canvas");
    var currHeight = $("#analysis-container svg").height();
    if ($("#canvas").length > 0) {
        currHeight = Math.max(currHeight, $("#canvas").height());
    }
    $tmpCanvas.height(currHeight);
    $tmpCanvas.width(svgContainerWidth);

    var svgContainer = document.createElement("svg");
    $svgContainer = $(svgContainer);
    $svgContainer.attr("id", "analysis-group");
    $svgContainer.attr("width", svgContainerWidth * pixelRatio);
    $svgContainer.attr("height", currHeight * pixelRatio);

    var index = 0;
    var svg = "";
    for (var i = 0; i < svgsElems.length; i++) {
        if (svgsElems[i].tagName === "svg") {
            var e = svgsElems[i];
            var eClone = $(e).clone();
            eClone[0].setAttribute("width", $(e).width() * pixelRatio)
            eClone[0].setAttribute("height", $(e).height() * pixelRatio)
            eClone[0].setAttribute("viewBox", "0 0 " + $(e).width() + " " + $(e).height())
            $svgContainer.append(eClone);
            index++;
        }
    }

    canvg($tmpCanvas[0], $svgContainer[0].outerHTML, {
        renderCallback: function() {
            var ctx = $tmpCanvas[0].getContext("2d");
            if ($("#canvas").length > 0) {
                var outerPaddingX = parseInt($("#analysis-container").css("padding-left")) * pixelRatio;
                var outerPaddingY = parseInt($("#analysis-container").css("padding-top")) * pixelRatio;
                ctx.drawImage(document.getElementById('canvas'), 0, 0, $("#canvas").width(), $("#canvas").height(), $("#canvas").position().left * pixelRatio - outerPaddingX, $("#canvas").position().top * pixelRatio - outerPaddingY, $("#canvas").width() * pixelRatio, $("#canvas").height() * pixelRatio);
            }

            var filename = name + ".png";

            $tmpCanvas[0].toBlob(function(blob) {
                saveAs(blob, filename);
            });

            $tmpCanvas.empty();
        }
    });
}

function downloadCSV(table) {
    var csvContent = "data:text/csv;charset=utf-8," + table.map(function(e) { return e.join(","); }).join("\n");
    var encodedUri = encodeURI(csvContent);
    window.open(encodedUri);
}

// Provides a simple hashing (non-secure)
String.prototype.hashCode = function() {
    var hash = 0;
    if (this.length == 0) {
        return hash;
    }
    for (var i = 0; i < this.length; i++) {
        var char = this.charCodeAt(i);
        hash = ((hash<<5)-hash)+char;
        hash = hash & hash; // Convert to 32bit integer
    }
    return hash;
}

//
// Quantile Box Section
//

var quantileColors = ["blue", "yellow", "green", "red", "purple"];

$("#catvar").change(function() {
    showOrHideQuantileManageContainer();
});

function saveQuantileRange(pid) {
    $.ajax({
        url: "/save_quantile",
        type: "POST",
        data: {
            pid: pid,
            quantileStaging: JSON.stringify(quantileStaging)
        },
        success: function(response) {
            hideQuantileForNumeric();
            window.location.reload(true);
        },
        error: function(xhr) {
            hideQuantileForNumeric();
        }
    });
}

$("#quantile-cancel").click(function() {
    hideQuantileForNumeric();
});

$("#quantile-exit").click(function() {
    hideQuantileForNumeric();
});

$(".blackout").click(function() {
    hideQuantileForNumeric();
});

function deleteQuantileRange(pid, sample_metadata) {
    $.ajax({
        url: "/remove_quantile",
        type: "POST",
        data: {
            pid: pid,
            sample_metadata: sample_metadata
        },
        success: function(response) {
            delete headersWithQuantileStatus[sample_metadata]
            hideQuantileForNumeric();
            window.location.reload(true);
        },
        error: function(xhr) {
            hideQuantileForNumeric();
        }
    });
}

function showOrHideQuantileManageContainer() {
    if ($('#catvar').length) {
        if (headersWithType[$("#catvar").val()] === "numeric" || headersWithType[$("#catvar").val()] === "both") {
            $(".quantile-manage-container").show();
            if (headersWithQuantileStatus[$("#catvar").val()]) {
                $(".quantile-using").show();
            } else {
                $(".quantile-using").hide();
            }
        } else {
            $(".quantile-manage-container").hide();
        }
    }
}

// Shows a quantile picker box when the user tries to apply the catvar on a numeric variable
function showQuantileForNumeric(pid, metadata_name, hide_if_possible) {
//    if (headersWithType[metadata_name] !== "numeric" && headersWithType[metadata_name] !== "both") {
//        return false;
//    }

    $.ajax({
        url: "/quantile_metadata_info",
        type: "get",
        data: {
            pid: pid,
            metadata_name: metadata_name
        },
        success: function(response) {
            var result = JSON.parse(response);
            quantileResultStaging = result.context;
            if (hide_if_possible && result.existing_quantile) {
                updateAnalysis();
                return;
            }

            if (result.existing_quantile) {
                // Load previous settings
                quantileStaging = result.existing_quantile;
                quantileStaging.metadata_name = metadata_name;
                $("#quantile-min").text(quantileStaging.min);
                $("#quantile-max").text(quantileStaging.max);

                $(".quantile-type-btn").removeClass("btn-primary");
                $(".quantile-type-btn").addClass("btn-link");
                if (quantileStaging.type === "q_2") {
                    $("#quantile-2").removeClass("btn-link");
                    $("#quantile-2").addClass("btn-primary");
                } else if (quantileStaging.type === "q_3") {
                    $("#quantile-3").removeClass("btn-link");
                    $("#quantile-3").addClass("btn-primary");
                } else if (quantileStaging.type === "q_4") {
                    $("#quantile-4").removeClass("btn-link");
                    $("#quantile-4").addClass("btn-primary");
                } else if (quantileStaging.type === "q_custom") {
                    $("#quantile-custom").removeClass("btn-link");
                    $("#quantile-custom").addClass("btn-primary");
                }

                var isNotLocked = quantileStaging.type === "q_custom";
                renderQuantileRange(metadata_name, !isNotLocked);
            } else {
                // Create a new default quantile staging
                var quantileArray = [
                    {
                        min: quantileResultStaging.q_0,
                        max: quantileResultStaging.q_50,
                        displayName: "Low Prevalence"
                    },
                    {
                        min: quantileResultStaging.q_50,
                        max: quantileResultStaging.q_100,
                        displayName: "High Prevalence"
                    }
                ];
                quantileStaging = {
                    type: "q_2",
                    quantiles: quantileArray,
                    metadata_name: metadata_name,
                    min: quantileResultStaging.q_0,
                    max: quantileResultStaging.q_100
                };
                $("#quantile-min").text(quantileResultStaging.q_0);
                $("#quantile-max").text(quantileResultStaging.q_100);
                renderQuantileRange(metadata_name, true);
            }

            renderQuantileBar();

            if (quantileStaging.quantiles.length <= 2) {
                $(".quantile-remove").remove();
            }

            $("#quantile-add").data("metadata", metadata_name);
            $("#quantile-metadata").text(metadata_name);
            $("#quantile-treat-as-categorical").data("metadata", metadata_name);
            $("#quantile-box").show();
            $("#blackout").show();
        },
        error: function(xhr) {
            hideQuantileForNumeric();
        }
    });
    return true;
}

// Hides a quantile picker box
function hideQuantileForNumeric() {
    $("#quantile-box").hide();
    $("#blackout").hide();
}

$(".quantile-type-btn").click(function() {
    $(".quantile-type-btn").removeClass("btn-primary");
    $(".quantile-type-btn").addClass("btn-link");
    $(this).removeClass("btn-link");
    $(this).addClass("btn-primary");
});

$("#quantile-2").click(function() {
    var quantileArray = [
        {
            min: quantileResultStaging.q_0,
            max: quantileResultStaging.q_50,
            displayName: "Low Prevalence"
        },
        {
            min: quantileResultStaging.q_50,
            max: quantileResultStaging.q_100,
            displayName: "High Prevalence"
        }
    ];
    quantileStaging.quantiles = quantileArray;
    quantileStaging.type = "q_2";
    renderQuantileRange(quantileStaging.metadata_name, true);
    renderQuantileBar();
});


$("#quantile-3").click(function() {
    var quantileArray = [
        {
            min: quantileResultStaging.q_0,
            max: quantileResultStaging.q_33,
            displayName: "Low Prevalence"
        },
        {
            min: quantileResultStaging.q_33,
            max: quantileResultStaging.q_66,
            displayName: "Mid Prevalence"
        },
        {
            min: quantileResultStaging.q_66,
            max: quantileResultStaging.q_100,
            displayName: "High Prevalence"
        }
    ];
    quantileStaging.quantiles = quantileArray;
    quantileStaging.type = "q_3";
    renderQuantileRange(quantileStaging.metadata_name, true);
    renderQuantileBar();
});


$("#quantile-4").click(function() {
    var quantileArray = [
        {
            min: quantileResultStaging.q_0,
            max: quantileResultStaging.q_25,
            displayName: "Low Prevalence"
        },
        {
            min: quantileResultStaging.q_25,
            max: quantileResultStaging.q_50,
            displayName: "Low-Mid Prevalence"
        },
        {
            min: quantileResultStaging.q_50,
            max: quantileResultStaging.q_75,
            displayName: "Mid-High Prevalence"
        },
        {
            min: quantileResultStaging.q_75,
            max: quantileResultStaging.q_100,
            displayName: "High Prevalence"
        }
    ];
    quantileStaging.quantiles = quantileArray;
    quantileStaging.type = "q_4";
    renderQuantileRange(quantileStaging.metadata_name, true);
    renderQuantileBar();
});

$("#quantile-custom").click(function() {
    var quantileArray = [
        {
            min: quantileResultStaging.q_0,
            max: quantileResultStaging.q_50,
            displayName: "Low Prevalence"
        },
        {
            min: quantileResultStaging.q_50,
            max: quantileResultStaging.q_100,
            displayName: "High Prevalence"
        }
    ];
    quantileStaging.quantiles = quantileArray;
    quantileStaging.type = "q_custom";
    renderQuantileRange(quantileStaging.metadata_name, false);
    renderQuantileBar();
});

$("#quantile-box #quantile-add").click(function() {
    var sampleMetadata = $(this).data('metadata');
    var quantileArray = quantileStaging.quantiles;
    quantileArray.push({
        min: "",
        max: "",
        displayName: ""
    });
    quantileStaging.quantiles = quantileArray;
    renderQuantileRange(sampleMetadata);
    renderQuantileBar();
});

$("#quantile-box").on('click', '.quantile-remove', function() {
    var sampleMetadata = $(this).data('metadata');
    var index = parseInt($(this).data('index'));
    var quantileArray = quantileStaging.quantiles;
    quantileArray.splice(index, 1);
    quantileStaging.quantiles = quantileArray;

    renderQuantileRange(sampleMetadata);
    renderQuantileBar();

    if (quantileArray.length <= 2) {
        $(".quantile-remove").remove();
    }
});

$("#quantile-box").on('#catvar', '.quantile-display-name', function() {
    var sampleMetadata = $(this).data('metadata');
    var index = parseInt($(this).data('index'));
    quantileStaging.quantiles[index].displayName = $(this).val();
    renderQuantileBar();
});

$("#quantile-box").on('change', '.quantile-min', function() {
    var sampleMetadata = $(this).data('metadata');
    var index = parseInt($(this).data('index'));
    quantileStaging.quantiles[index].min = $(this).val();
    renderQuantileBar();
});

$("#quantile-box").on('change', '.quantile-max', function() {
    var sampleMetadata = $(this).data('metadata');
    var index = parseInt($(this).data('index'));
    quantileStaging.quantiles[index].max = $(this).val();
    renderQuantileBar();
});

function renderQuantileRange(sampleMetadata, lock) {
    $("#quantile-container").empty();
    var quantileArray = quantileStaging.quantiles;

    for (var i = 0; i < quantileArray.length; i++) {
        var quantileRange = quantileArray[i];
        $("#quantile-container").append(getQuantileRangeHTML(sampleMetadata, i, quantileRange.displayName, quantileRange.min, quantileRange.max));
    }

    if (lock) {
        $(".quantile-input").attr("disabled", true);
        $("#quantile-add").hide();
        $(".quantile-remove").hide();
    } else {
        $(".quantile-input").attr("disabled", false);
        $("#quantile-add").show();
        $(".quantile-remove").show();
    }

    if (quantileArray.length >= 5) {
        $("#quantile-add").attr("disabled", true);
    } else {
        $("#quantile-add").attr("disabled", false);
    }

    if (quantileArray.length <= 2) {
        $(".quantile-remove").remove();
    }
}

function renderQuantileBar() {
    $("#quantile-progress").empty();
    var quantileArray = quantileStaging.quantiles;
    var min = quantileStaging.min;
    var max = quantileStaging.max;
    var range = (max - min);

    if (quantileArray[0].min !== "") {
        var percent = 100 * (parseFloat(quantileArray[0].min) - min) / range;
        $("#quantile-progress").append(getQuantileBarHTML(percent, "transparent", "Not Assigned to a Quantile", min, quantileArray[0].min));
    }

    for (var i = 0; i < quantileArray.length; i++) {
        if (quantileArray[i].min !== "" && quantileArray[i].max !== "") {

            if (i > 0 && (parseFloat(quantileArray[i].min) - parseFloat(quantileArray[i - 1].max)) > 0) {
                var percent = 100 * (parseFloat(quantileArray[i].min) - parseFloat(quantileArray[i - 1].max)) / range;
                $("#quantile-progress").append(getQuantileBarHTML(percent, "transparent", "Not Assigned to a Quantile", parseFloat(quantileArray[i - 1].max), parseFloat(quantileArray[i].min)));
            }

            var percent = 100 * (parseFloat(quantileArray[i].max) - parseFloat(quantileArray[i].min)) / range;
            $("#quantile-progress").append(getQuantileBarHTML(percent, quantileColors[i], quantileArray[i].displayName, parseFloat(quantileArray[i].min), parseFloat(quantileArray[i].max)));
        }
    }

    if (quantileArray[quantileArray.length - 1].max !== "") {
        var percent = 100 * (max - parseFloat(quantileArray[quantileArray.length - 1].max)) / range;
        $("#quantile-progress").append(getQuantileBarHTML(percent, "transparent", "Not Assigned to a Quantile", quantileArray[quantileArray.length - 1].min, max));
    }

    $('[data-toggle="popover"]').popover();
}

function getQuantileBarHTML(percent, color, title, min, max) {
    return `<div class="progress-bar" style="width: ${percent}%;background-color:${color}" data-toggle="popover" data-placement="bottom"
             data-title="${title}" data-content="Range: ${min} - ${max}" data-trigger="hover">
        </div>`;
}

function getQuantileRangeHTML(sampleMetadata, index, displayName, min, max) {
    var placeholderForDisplayName = index == 0 ? "eg. Low Expression" : "eg. High Expression";
    var placeholderForMin = index == 0 ? "eg. 0" : "eg. 10";
    var placeholderForMax = index == 0 ? "eg. 10" : "eg. 20";

    return `<div>
        <div class="row">
            <div class="col-md-12">
                <h5>Quantile Range ${index + 1} <a data-metadata="${sampleMetadata}" data-index="${index}" class="quantile-remove" href="#">(remove)</a></h5>
                <div class="row">
                    <div class="col-md-6">
                        <div class="input-group">
                            <span class="input-group-addon">Display Name</span>
                            <input data-metadata="${sampleMetadata}" data-index="${index}" type="text" class="form-control quantile-display-name" placeholder="${placeholderForDisplayName}" value="${displayName}">
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="input-group">
                            <span class="input-group-addon">Min</span>
                            <input data-metadata="${sampleMetadata}" data-index="${index}" type="number" class="form-control quantile-input quantile-min" placeholder="${placeholderForMin}" value="${min}">
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="input-group">
                            <span class="input-group-addon">Max</span>
                            <input data-metadata="${sampleMetadata}" data-index="${index}" type="number" class="form-control quantile-input quantile-max" placeholder="${placeholderForMax}" value="${max}">
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <hr/>
    </div>`;
}

