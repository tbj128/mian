// ============================================================
// Boxplot JS Component
// ============================================================

var tagsInput;

//
// Initialization
//
initializeComponent({
    hasCatVar: true,
    hasCatVarNoneOption: true,
});
createSpecificListeners();

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#catvar").change(function () {
      updateAnalysis();
    });

    $("#specific-taxonomy-typeahead").change(function () {
      updateAnalysis();
    });

    $("#yvals").change(function () {
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

    $("#taxonomy-level").change(function () {
        var val = $("#yvals").val();
        if (val === "mian-taxonomy-abundance") {
            $.when(loadOTUTableHeaders()).done(function() {
                updateAnalysis();
            });
        }
    });
}


//
// Analysis Specific Methods
//

// Required analysis entry-point method
function updateAnalysis() {
    console.log("Updating analysis");

    showLoading();
    $("#stats-container").hide();

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var yvals = $("#yvals").val();
    var yvalsSpecificTaxonomy = $("#specific-taxonomy-typeahead").val()
    if (yvalsSpecificTaxonomy === "") {
        yvalsSpecificTaxonomy = JSON.stringify([]);
    } else {
        yvalsSpecificTaxonomy = JSON.stringify(yvalsSpecificTaxonomy.split(","));
    }
    var level = taxonomyLevels[$("#taxonomy-level").val()];

    var data = {
      "pid": $("#project").val(),
      "taxonomyFilter": taxonomyFilter,
      "taxonomyFilterRole": taxonomyFilterRole,
      "taxonomyFilterVals": taxonomyFilterVals,
      "sampleFilter": sampleFilter,
      "sampleFilterRole": sampleFilterRole,
      "sampleFilterVals": sampleFilterVals,
      "catvar": catvar,
      "yvals": yvals,
      "level": level,
      "yvalsSpecificTaxonomy": yvalsSpecificTaxonomy,
    };

    $.ajax({
      type: "POST",
      url: "boxplots",
      data: data,
      success: function(result) {
        $("#display-error").hide();
        hideLoading();
        $("#analysis-container").show();
        $("#stats-container").show();

        var abundancesObj = JSON.parse(result);
        if ($.isEmptyObject(abundancesObj["abundances"])) {
            $("#display-error").show();
            $("#analysis-container").hide();
            $("#stats-container").hide();
        } else {
            renderBoxplots(abundancesObj);
            renderPvaluesTable(abundancesObj);
        }
      },
      error: function(err) {
        hideLoading();
        $("#analysis-container").hide();
        $("#stats-container").show();
        $("#display-error").show();
        console.log(err);
      }
    });
}

function customCatVarCallback(result) {
    var allHeaders = result.map(obj => obj.name);

    $("#yvals").empty();
    $("#yvals").append('<option value="mian-taxonomy-abundance">Taxonomy Abundance</option><option value="mian-abundance">Aggregate Abundance</option><option value="mian-max">Max Abundance</option><option value="mian-min">Min Abundance</option><option value="mian-mean">Mean Abundance</option><option value="mian-median">Median Abundance</option>');
    for (var i = 0; i < allHeaders.length; i++) {
      $("#yvals").append('<option value="' + allHeaders[i] + '">' + allHeaders[i] + '</option>')
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
          url: "otu_table_headers_at_level?pid=" + $("#project").val() + "&level=" + level,
          success: function(result) {
              var typeAheadSource = JSON.parse(result);
              if (tagsInput) {
                  $('#specific-taxonomy-typeahead').tagsinput('removeAll');
                  $('#specific-taxonomy-typeahead').tagsinput('destroy');
              }

              tagsInput = $('#specific-taxonomy-typeahead').tagsinput({
                typeahead: {
                    source: typeAheadSource,
                    afterSelect: () => {
                        $('#specific-taxonomy-typeahead').tagsinput('input').val('');
                    }
                },
                freeInput: false
              });
              $("#taxonomy-specific-typeahead-wrapper .bootstrap-tagsinput").css("width", "320px");

          }
        });
        return headersPromise;
    }
    return null;
}