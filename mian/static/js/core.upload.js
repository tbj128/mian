$(document).ready(function() {
    // Hides loading bar
    $("#loading").hide();

    // Global variables
    var isNameValid = false;
    var biomUploaded = false;
    var otuTableUploaded = false;
    var otuTaxonomyMappingUploaded = false;
    var otuMetadataUploaded = false;

    // Event listener for main create button
    $("#upload-submit").click(function() {
        $("#loading").show();
    });

    // Event listeners to switch tabs
    $("#upload-biom-tab").click(function() {
        $(this)
            .removeClass("btn-default")
            .addClass("btn-primary");
        $("#upload-otu-tab")
            .removeClass("btn-primary")
            .addClass("btn-default");
        $("#otu-upload-container").fadeOut(250);
        $("#biom-upload-container").fadeIn(250);
        $("#projectUploadType").val("biom");
    });
    $("#upload-otu-tab").click(function() {
        $(this)
            .removeClass("btn-primary")
            .addClass("btn-primary");
        $("#upload-biom-tab")
            .removeClass("btn-primary")
            .addClass("btn-default");
        $("#otu-upload-container").fadeIn(250);
        $("#biom-upload-container").fadeOut(250);
        $("#projectUploadType").val("otu");
    });

    // The event listener for the file upload
    document
        .getElementById("inputName")
        .addEventListener("change", nameChange, false);
    document
        .getElementById("biomInput")
        .addEventListener("change", uploadBiom, false);
    document
        .getElementById("otuTable")
        .addEventListener("change", uploadOTUTable, false);
    document
        .getElementById("otuTaxonomyMapping")
        .addEventListener("change", uploadTaxonomyMapping, false);
    document
        .getElementById("otuMetadata")
        .addEventListener("change", uploadMetadata, false);

    document.getElementById("subsampleType").addEventListener(
        "change",
        function() {
            $("#subsampleTo").hide();
            $("#auto-prompt").hide();
            $("#manual-prompt").hide();
            $("#no-prompt").hide();

            var type = $("#subsampleType").val();
            if (type === "manual") {
                $("#subsampleTo").show();
                $("#manual-prompt").show();
            } else if (type === "auto") {
                $("#auto-prompt").show();
            } else {
                $("#subsampleTo").hide();
                $("#no-prompt").show();
            }

            $("#projectSubsampleType").val(type);
        },
        false
    );

    document.getElementById("biomSubsampleType").addEventListener(
        "change",
        function() {
            $("#biomSubsampleTo").hide();
            $("#biom-auto-prompt").hide();
            $("#biom-manual-prompt").hide();
            $("#biom-no-prompt").hide();

            var type = $("#biomSubsampleType").val();
            if (type === "manual") {
                $("#biomSubsampleTo").show();
                $("#biom-manual-prompt").show();
            } else if (type === "auto") {
                $("#biom-auto-prompt").show();
            } else {
                $("#biomSubsampleTo").hide();
                $("#biom-no-prompt").show();
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

    document.getElementById("biomSubsampleTo").addEventListener(
        "change",
        function() {
            $("#projectSubsampleTo").val($("#biomSubsampleTo").val());
        },
        false
    );

    function nameChange() {
        $("#projectName").val($("#inputName").val());
        checkComplete();
    }

    function checkComplete() {
        if ($("#projectName").val() !== "") {
            isNameValid = true;
        } else {
            isNameValid = false;
        }

        if (
            isNameValid &&
            (biomUploaded ||
                (otuTableUploaded && otuTaxonomyMappingUploaded && otuMetadataUploaded))
        ) {
            $("#upload-submit").prop("disabled", false);
        } else {
            $("#upload-submit").prop("disabled", true);
        }
    }

    function uploadBiom() {
        upload("biomForm");
    }

    function uploadOTUTable() {
        upload("otuTableForm");
    }

    function uploadTaxonomyMapping() {
        upload("otuTaxonomyMappingForm");
    }

    function uploadMetadata() {
        upload("otuMetadataForm");
    }

    // Catch the form submit and upload the files
    function upload(formID) {
        var form = $("#" + formID)[0];
        var filename = "";
        var formData = new FormData(form);

        if (formID == "biomForm") {
            $("#biomLoading").show();
            filename = $("#biomInput").val();
        }
        if (formID == "otuTableForm") {
            $("#otuTableLoading").show();
            filename = $("#otuTable").val();
        }
        if (formID == "otuTaxonomyMappingForm") {
            $("#otuTaxonomyMappingLoading").show();
            filename = $("#otuTaxonomyMapping").val();
        }
        if (formID == "otuMetadataForm") {
            $("#otuMetadataLoading").show();
            filename = $("#otuMetadata").val();
        }
        if (formID == "phylogeneticForm") {
            $("#phylogeneticLoading").show();
            filename = $("#phylogenetic").val();
        }

        filename = filename.split(/(\\|\/)/g).pop();

        $.ajax({
            url: "/upload",
            type: "POST",
            data: formData,
            cache: false,
            processData: false, // Don't process the files
            contentType: false, // Set content type to false as jQuery will tell the server its a query string request
            success: function(data, textStatus, jqXHR) {
                console.log("Success");
                if (formID == "biomForm") {
                    $("#biomLoading").hide();
                    $("#biomOK").show();
                    $("#biomText").text("Replace");
                    $("#projectBiomName").val(filename);
                    biomUploaded = true;
                }
                if (formID == "otuTableForm") {
                    $("#otuTableLoading").hide();
                    $("#otuTableOK").show();
                    $("#otuTableText").text("Replace");
                    $("#projectOTUTableName").val(filename);
                    otuTableUploaded = true;
                }
                if (formID == "otuTaxonomyMappingForm") {
                    $("#otuTaxonomyMappingLoading").hide();
                    $("#otuTaxonomyMappingOK").show();
                    $("#otuTaxonomyMappingText").text("Replace");
                    $("#projectTaxaMapName").val(filename);
                    otuTaxonomyMappingUploaded = true;
                }
                if (formID == "otuMetadataForm") {
                    $("#otuMetadataLoading").hide();
                    $("#otuMetadataOK").show();
                    $("#otuMetadataText").text("Replace");
                    $("#projectSampleIDName").val(filename);
                    otuMetadataUploaded = true;
                }
                if (formID == "phylogeneticForm") {
                    $("#phylogeneticLoading").hide();
                    $("#phylogeneticOK").show();
                    $("#phylogeneticText").text("Replace");
                    $("#projectPhylogeneticName").val(filename);
                }

                checkComplete();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log("Error: " + textStatus);
                alert("An error occurred");
            }
        });
    }
});
