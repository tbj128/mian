// ================================================================================
// Global Variables
//

var MINIMUM_FOR_TYPEAHEAD_MODE = 300;

var taxonomyLevels = {
  "Kingdom": 0,
  "Phylum": 1,
  "Class": 2,
  "Order": 3,
  "Family": 4,
  "Genus": 5,
  "Species": 6,
  "OTU": -1
};
var taxonomiesMap = [];

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
    $('[data-toggle="popover"]').popover({
        'html': true,
        'placement': 'right',
        'container': 'body',
        'trigger': 'manual',
        'animation': false,
    })
    .on("mouseenter", function () {
        var _this = this;
        $(this).popover("show");
        $(".popover").on("mouseleave", function () {
            $(_this).popover('hide');
        });
    }).on("mouseleave", function () {
        var _this = this;
        setTimeout(function () {
            if (!$(".popover:hover").length) {
                $(_this).popover("hide");
            }
        }, 300);
    });;

    hasCatVar = catVarOptions ? catVarOptions.hasCatVar : false;
    hasCatVarNoneOption = catVarOptions ? catVarOptions.hasCatVarNoneOption : false;

    createGlobalSidebarListeners();
    handleGlobalURLParams();

    resetProject();
}


// ================================================================================
// Globally Accessible Helper Methods
//

function showLoading() {
  $("#loading").show();
}

function hideLoading() {
  $("#loading").hide();
}

function setExtraNavLinks(attr) {
  $(".nav-link").each(function() {
    var currHref = $(this).attr("href");
    var currHrefArr = currHref.split("?");
    if (currHrefArr.length > 1) {
      currHref = currHrefArr[0];
    }
    $(this).attr("href", currHref + "?pid=" + attr);
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
  var taxTypeaheadFilterVisible = $("#taxonomy-specific-typeahead-wrapper").is(":visible");
  if (!taxTypeaheadFilterVisible) {
    // We are not using typeahead so we are always an "include" filter
    return "Include";
  } else {
    var typeaheadRole = $("#taxonomy-typeahead-btn .typeahead-role").text();
    return typeaheadRole;
  }
}

function getSelectedTaxFilterVals() {
    var taxTypeaheadFilterVisible = $("#taxonomy-specific-typeahead-wrapper").is(":visible");
    if (taxTypeaheadFilterVisible) {
      var taxTypeaheadFilter = $("#taxonomy-typeahead-filter").val();
      return taxTypeaheadFilter;
    } else {
      var taxonomy = $("#taxonomy-specific").val();
      if (taxonomy == null) {
        taxonomy = [];
      }

      var taxLevel = $("#filter-otu").val();
      if (taxLevel === "none") {
        taxonomy = [];
      }

      if ($("#taxonomy-specific option").size() === taxonomy.length) {
        // Select all is enabled
        return "mian-select-all";
      }

      return taxonomy.join(",");
    }
}

function getSelectedSampleFilter() {
  var filter = $("#filter-sample").val();
  return filter;
}

function getSelectedSampleFilterRole() {
  var sampleTypeaheadFilterVisible = $("#sample-specific-typeahead-wrapper").is(":visible");
  if (!sampleTypeaheadFilterVisible) {
    // We are not using typeahead so we are always an "include" filter
    return "Include";
  } else {
    var typeaheadRole = $("#sample-typeahead-btn .typeahead-role").text();
    return typeaheadRole;
  }
}

function getSelectedSampleFilterVals() {
    var sampleTypeaheadFilterVisible = $("#sample-specific-typeahead-wrapper").is(":visible");
    if (sampleTypeaheadFilterVisible) {
        var sampleTypeaheadFilter = $("#sample-typeahead-filter").val();
        return sampleTypeaheadFilter;
    } else {
        var samples = $("#filter-sample-specific").val();
        if (samples == null) {
            samples = []
        }
        return samples.join(",");
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

function getSampleFilteringOptions() {
    $.ajax({
      url: "metadata_vals?pid=" + $("#project").val() + "&catvar=" + $("#filter-sample").val(),
      success: function(result) {
        var json = JSON.parse(result);

        var $filterSampleSpecific = $("#filter-sample-specific");

        var options = [];

        console.log(json);

        if (json.length < MINIMUM_FOR_TYPEAHEAD_MODE) {
            $('#sample-specific-typeahead-wrapper').hide();
            $('#sample-typeahead-filter').val("");

            for (var i = 0; i < json.length; i++) {
              var option = {
                "label": json[i],
                "title": json[i],
                "value": json[i],
                // "selected": true
              };
              options.push(option);
            }
            var outWidth = $("#project").outerWidth();
            $filterSampleSpecific.multiselect({
              buttonWidth: outWidth ? outWidth + 'px' : '320px',
              includeSelectAllOption: true,
              enableFiltering: true,
              maxHeight: 400
            });

            $filterSampleSpecific.multiselect('dataprovider', options);
        } else {
            console.log("Loading typeahead sample filter");
            $('#sample-typeahead-filter').tagsinput('destroy');
            $("#filter-sample-specific").multiselect("destroy");
            $("#filter-sample-specific").hide();

            $('#sample-typeahead-filter').tagsinput({
              freeInput: false,
              placeholderText: "Enter",
              typeahead: {
                source : json,
                afterSelect: () => {
                  $('#sample-typeahead-filter').tagsinput('input').val('');
                }
              }
            });
            $('#sample-specific-typeahead-wrapper').show();
        }
      }
    });
}

function resetProject() {
    // We must wait for all the sidebar components to finish updating before we can render the analysis component
    if (hasCatVar && typeof customLoading === "function") {
        $.when(updateTaxonomicLevel(true, function() {}), updateCatVar(function() {}), customLoading()).done(function(a1, a2, a3) {
            updateProject();
        });
    } else if (hasCatVar) {
        $.when(updateTaxonomicLevel(true, function() {}), updateCatVar(function() {})).done(function(a1, a2, a3) {
            updateProject();
        });
    } else if (typeof customLoading === "function") {
        $.when(updateTaxonomicLevel(true, function() {}), customLoading()).done(function(a1, a2, a3) {
            updateProject();
        });
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
    $("#project").change(function () {
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

    $("#taxonomy").change(function () {
        updateAnalysis();
    });

    $("#taxonomy-specific").change(function () {
      updateAnalysis();
    });

    $("#taxonomy-typeahead-btn a").on("click", function() {
        var intent = $(this).data("intent");
        $("#taxonomy-typeahead-btn .typeahead-role").text(intent);
        updateAnalysis();
    });

    $("#taxonomy-typeahead-filter").change(function () {
      updateAnalysis();
    });

    $("#filter-sample-specific").change(function () {
      updateAnalysis();
    });

    $("#sample-typeahead-btn a").on("click", function() {
        var intent = $(this).data("intent");
        $("#sample-typeahead-btn .typeahead-role").text(intent);
        updateAnalysis();
    });

    $("#sample-typeahead-filter").change(function () {
        updateAnalysis();
    });
}

function updateCatVar(isNumeric) {
  return $.ajax({
    url: "metadata_headers_with_type?pid=" + $("#project").val(),
    success: function(result) {
      var json = JSON.parse(result);
      var headers = isNumeric === true ? json.filter(obj => obj.type === "numeric").map(obj => obj.name) :
          json.filter(obj => obj.type === "categorical").map(obj => obj.name);

      var $catvar = $("#catvar");

      if ($catvar.length > 0) {
          var $filterSample = $("#filter-sample");

          $catvar.empty();
          if (hasCatVarNoneOption) {
            $catvar.append("<option value='none'>None</option>");
          }

          $filterSample.empty();
          $filterSample.append("<option value='none'>Don't Filter</option>");
          $filterSample.append("<option value='mian-sample-id'>Sample ID</option>");

          var options = [];
          for (var i = 0; i < headers.length; i++) {
            var option = {
              "label": headers[i],
              "title": headers[i],
              "value": headers[i]
            };
            options.push(option);
          }

          for (var i = 0; i < headers.length; i++) {
            $catvar.append("<option value='" + headers[i] + "'>" + headers[i] + "</option>");
            $filterSample.append("<option value='" + headers[i] + "'>" + headers[i] + "</option>");
          }
      }

      if (typeof customCatVarCallback === "function") {
        // Callback used to load any additional filtering parameters
        customCatVarCallback(json);
      }

      catVars = json;
    }
  });
}

function updateTaxonomicLevel(firstLoad, callback) {
  console.log("Updating taxonomic level")
  if (taxonomiesMap.length == 0) {
    // Load taxonomy map
    return $.ajax({
      url: "taxonomies?pid=" + $("#project").val(), 
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

  if (taxasArr.length < MINIMUM_FOR_TYPEAHEAD_MODE) {
      console.log("Loading regular taxonomy multiselect filter");

      $('#taxonomy-specific-typeahead-wrapper').hide();
      $('#taxonomy-typeahead-filter').val("");

      var $filterOTUSpecific = $("#taxonomy-specific");
      var options = [];
      for (var i = 0; i < taxasArr.length; i++) {
        var option = {
          "label": taxasArr[i],
          "title": taxasArr[i],
          "value": taxasArr[i],
          // "selected": true
        };
        options.push(option);
      }

      var outWidth = $("#project").outerWidth();
      $filterOTUSpecific.multiselect({
        buttonWidth: outWidth ? outWidth + 'px' : '320px',
        includeSelectAllOption: true,
        enableFiltering: true,
        maxHeight: 400
      });

      $filterOTUSpecific.multiselect('dataprovider', options);
  } else {
      console.log("Loading typeahead taxonomy filter");
      $('#taxonomy-typeahead-filter').val("");
      $('#taxonomy-typeahead-filter').tagsinput('destroy');
      $("#taxonomy-specific").multiselect("destroy");
      $("#taxonomy-specific").hide();

      $('#taxonomy-typeahead-filter').tagsinput({
          freeInput: false,
          typeahead: {
            source : taxasArr,
            afterSelect: () => {
              $('#taxonomy-typeahead-filter').tagsinput('input').val('');
            }
          }
      });
      $('#taxonomy-specific-typeahead-wrapper').show();
  }

  console.log("Finished rendering taxonomic level");
}


function updateSamples(firstLoad) {
  return $.ajax({
    url: "samples?pid=" + $("#project").val(), 
    success: function(result) {
      var json = JSON.parse(result);
      renderSamples(json, firstLoad);
    }
  });
}

function renderSamples(json, firstLoad) {
  $("#samples").empty();
  options = ""
  for (var i = 0; i < json.length; i++) {
    options += "<option value='" + json[i] + "'>" + json[i] + "</option>";
  }
  $("#samples").append(options)

  if (firstLoad) {
    var outWidth = $("#project").outerWidth();
    $('#samples').multiselect({
      buttonWidth: outWidth ? outWidth + 'px' : '320px',
      enableFiltering: true,
      includeSelectAllOption: true,
      maxHeight: 200
    });
  } else {
    $('#samples').multiselect('rebuild');
  }
  $('#samples').multiselect('selectAll', false);
  $('#samples').multiselect('updateButtonText');
}



// 
// Statistics Container Shared
// 

function renderPvaluesTable(abundancesObj) {
  $("#stats-container").hide();

  if ($.isEmptyObject(abundancesObj)) {
    return;
  }

  $('#stats-rows').empty();
  var statsArr = abundancesObj["stats"];
  if (statsArr.length == 0) {
    $('#stats-rows').append('<tr><td colspan=3>No p-values could be generated. Try adjusting the search parameters. <br /><i style="color:#999">Try changing the Category Breakdown on the left.</i></td></tr>');
  } else {
    for (var i = 0; i < statsArr.length; i++) {
       $('#stats-rows').append('<tr><td>' + statsArr[i]["c1"] + '</td> <td>' + statsArr[i]["c2"] + '</td> <td>' + statsArr[i]["pval"] + '</td> </tr>');
    }
  }
  
  $("#stats-container").fadeIn(250);
}
