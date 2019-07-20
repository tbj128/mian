
// Shows a quantile picker box when the user tries to apply the catvar on a numeric variable
function showQuantileForNumeric(pid, quantile_type, metadata_name, hide_if_possible) {
    $.ajax({
        url: "/quantile_metadata_info",
        type: "get",
        data: {
            pid: pid,
            metadata_name: metadata_name,
            quantile_type: quantile_type
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
                    type: "q_2", // Default type
                    quantile_type: quantile_type,
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
            hideLoading();
        },
        error: function(xhr) {
            hideQuantileForNumeric();
            hideLoading();
        }
    });
    return true;
}

$(document).ready(function() {
    var quantileType = getParameterByName("quantileType");
    if (quantileType === "gene") {
        $("#quantile-type-selector-numeric").hide();
        $("#quantile-type-selector-gene").show();
        $("#quantile-type-selector").val("gene");
    } else if (quantileType === "numeric") {
        $("#quantile-type-selector-numeric").show();
        $("#quantile-type-selector-gene").hide();
        $("#quantile-type-selector").val("numeric");
    }

    $("#quantile-type-selector").change(function() {
        if ($(this).val() === "numeric") {
            $("#quantile-type-selector-numeric").show();
            $("#quantile-type-selector-gene").hide();
        } else if ($(this).val() === "gene") {
            $("#quantile-type-selector-numeric").hide();
            $("#quantile-type-selector-gene").show();
        } else {
            $("#quantile-type-selector-numeric").hide();
            $("#quantile-type-selector-gene").hide();
        }
    });

    $("#quantile-new").click(function() {
        showLoading();
        var metadataName = $("#quantile-type-selector").val() === "gene" ? $("#gene-typeahead").val() : $("#quantile-new-select").val();
        showQuantileForNumeric($("#pid").val(), $("#quantile-type-selector").val(), metadataName, false);
    });

    $(".quantile-edit").click(function() {
        showLoading();
        showQuantileForNumeric($("#pid").val(), $(this).data("type"), $(this).data("metadata"), false);
    });

    $(".quantile-delete").click(function() {
        deleteQuantileRange($("#pid").val(), $(this).data("metadata"));
    });

    $("#quantile-save").click(function() {
        saveQuantileRange($("#pid").val());
    });

    loadGeneOptions();

    function loadGeneOptions() {
        showLoading();
        $("#quantile-new").prop("disabled", true);
        $.ajax({
            url: "/genes",
            type: "get",
            data: {
                pid: $("#pid").val(),
                type: "Gene",
            },
            success: function(response) {
                var result = JSON.parse(response);
                genes = result;

                if (geneRenderedTypeahead["genebox"]) {
                    $("#gene-typeahead").tagsinput("destroy");
                }

                $("#gene-typeahead").tagsinput({
                    freeInput: false,
                    placeholderText: "Enter",
                    maxTags: 1,
                    typeahead: {
                        source: genes,
                        afterSelect: function() {
                            $("#gene-typeahead")
                                .tagsinput("input")
                                .val("");
                        }
                    }
                });

                // Workaround for typeahead bug where the destroy call can prevent the
                // tagsinput from displaying properly on the first load
                geneRenderedTypeahead["genebox"] = true;

                hideLoading();

                $("#quantile-new").prop("disabled", false);
            },
            error: function(xhr) {
                hideLoading();
                $("#quantile-new").prop("disabled", false);
            }
        });
        return true;
    }
});