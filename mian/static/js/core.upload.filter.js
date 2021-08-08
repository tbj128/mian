
var MINIMUM_FOR_TYPEAHEAD_MODE = 300;

$(document).ready(function() {
    // Hides loading bar
    $("#loading").hide();

    // Event listener for main create button
    $("#upload-submit").click(function() {
        $("#loading").show();
    });

    $("#subsampleType").change(function() {
        getFilteringInfo();
    });

    $("#subsampleTo").change(function() {
        getFilteringInfo();
    });

    $("#low-expression-filter").change(function() {
        if ($("#low-expression-filter").val() === "none") {
            $("#low-expression-filter-none-prompt").show();
            $("#low-expression-filter-details").hide();
        } else {
            $("#low-expression-filter-none-prompt").hide();
            $("#low-expression-filter-details").show();
        }
    });

    $("#low-expression-filter").change(function() {
        $("#lowExpressionFilteringType").val($("#low-expression-filter").val());
    });

    $("#low-expression-count").change(function() {
        $("#lowExpressionFilteringCount").val($("#low-expression-count").val());
    });

    $("#low-expression-prevalence").change(function() {
        $("#lowExpressionFilteringPrevalence").val($("#low-expression-prevalence").val());
    });

    $("#filter-sample").change(function() {
        if ($("#filter-sample").val() === "none") {
            $("#filter-sample-none-prompt").show();
        } else {
            $("#filter-sample-none-prompt").hide();
        }

        updateFilterSamplesOptions();
        getFilteringInfo();
    });

    $("#filter-sample-specific").change(function() {
        getFilteringInfo();
    });

    $("#sample-typeahead-btn a").on("click", function() {
        var intent = $(this).data("intent");
        $("#sample-typeahead-btn .typeahead-role").text(intent);
        getFilteringInfo();
    });

    $("#sample-typeahead-filter").change(function() {
        getFilteringInfo();
    });

    document.getElementById("subsampleType").addEventListener(
        "change",
        function() {
            $(".normalize-info").hide();

            var type = $("#subsampleType").val();
            if (type === "manual") {
                $("#subsampleTo").show();
                $("#manual-prompt").show();
            } else if (type === "auto") {
                $("#auto-prompt").show();
            } else if (type === "uq") {
                $("#uq-prompt").show();
            } else if (type === "tss") {
                $("#tss-prompt").show();
            } else if (type === "css") {
                $("#css-prompt").show();
            } else {
                $("#subsampleTo").hide();
                $("#no-prompt").show();
            }

            $("#projectSubsampleType").val(type);
        },
        false
    );

    document.getElementById("subsampleTo").addEventListener(
        "change",
        function() {
            $("#projectSubsampleTo").val($("#subsampleTo").val());
        },
        false
    );

    loadSampleFiltering();
    getFilteringInfo();


    //
    // FUNCTIONS BEGIN HERE
    //

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
            url: "/metadata_vals?pid=" +
                $("#project").val() +
                "&catvar=" +
                $("#filter-sample").val(),
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
                            value: json[i]
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
                    $("#sample-specific-typeahead-wrapper").show();
                }
            }
        });
    }

    function loadSampleFiltering() {
        $.ajax({
            url: "/metadata_headers_with_type?pid=" + $("#project").val(),
            success: function(result) {
                var jsonBody = JSON.parse(result);
                var json = jsonBody["headers"];
                var filteringHeaders = json.map(function(obj) { return obj.name; });

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
            }
        });
    }

    function getFilteringInfo() {
        $("#loading").show();
        var sampleFilter = getSelectedSampleFilter();
        var sampleFilterRole = getSelectedSampleFilterRole();
        var sampleFilterVals = getSelectedSampleFilterVals();
        $("#sampleFilter").val(sampleFilter);
        $("#sampleFilterRole").val(sampleFilterRole);
        $("#sampleFilterVals").val(sampleFilterVals);

        var data = {
            pid: $("#project").val(),
            sampleFilter: sampleFilter,
            sampleFilterRole: sampleFilterRole,
            sampleFilterVals: sampleFilterVals
        };

        $.ajax({
            type: "POST",
            url: "/get_filtering_info",
            data: data,
            success: function(result) {
                $("#loading").hide();
                var obj = JSON.parse(result);
                var samples = obj["samples"];
                var minSampleVal = obj["min_sample_val"];
                var hasFloat = obj["has_float"];
                var numRemoved = 0;
                $("#samples").empty();
                Object.keys(samples).forEach(sample => {
                    var classStr = samples[sample]["removed"] ? "removed" : "included";
                    if ($("#subsampleType").val() === "manual") {
                        if (samples[sample]["row_sum"] < parseInt($("#subsampleTo").val())) {
                            classStr = "removed";
                        }
                    }

                    if (classStr === "removed") {
                        numRemoved++;
                    }

                    $("#samples").append("<tr class=\"" + classStr + "\"><td>" + sample + "</td><td>" + samples[sample]["row_sum"] + "</td></tr>");
                });

                var kept = (Object.keys(samples).length - numRemoved);
                $("#kept").text(kept + "/" + Object.keys(samples).length);

                if (hasFloat) {
                    $("#subsamplingToContainer").hide();
                    $(".normalize-info").hide();
                    $("#has-float").show();
                    $("#subsampleType").val("no");
                    $("#subsampleType").prop('disabled', true);
                } else if ($("#subsampleType").val() === "auto") {
                    $("#subsamplingTo").text(minSampleVal + " (auto)");
                    $("#subsamplingToContainer").show();
                    $("#subsampleType").prop('disabled', false);
                } else if ($("#subsampleType").val() === "manual") {
                    $("#subsamplingTo").text($("#subsampleTo").val());
                    $("#subsamplingToContainer").show();
                    $("#subsampleType").prop('disabled', false);
                } else if ($("#subsampleType").val() === "uq") {
                    $("#subsamplingTo").text("N/A (upper quantile scaling)");
                    $("#subsamplingToContainer").show();
                    $("#subsampleType").prop('disabled', false);
                } else if ($("#subsampleType").val() === "tss") {
                    $("#subsamplingTo").text("1 (total row sum)");
                    $("#subsamplingToContainer").show();
                    $("#subsampleType").prop('disabled', false);
                } else if ($("#subsampleType").val() === "css") {
                    $("#subsamplingTo").text("N/A (cumulative sum scaling)");
                    $("#subsamplingToContainer").show();
                    $("#subsampleType").prop('disabled', false);
                } else {
                    $("#subsamplingToContainer").hide();
                    $("#subsampleType").prop('disabled', false);
                }
            },
            error: function(err) {
                $("#loading").hide();
                console.log(err);
            }
        });
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
});
