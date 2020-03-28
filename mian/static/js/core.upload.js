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
        $(".biom-only").show();
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
        $(".biom-only").hide();
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
    document
        .getElementById("phylogenetic")
        .addEventListener("change", uploadPhylogenetic, false);
    document
        .getElementById("gene")
        .addEventListener("change", uploadGene, false);

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

    function uploadPhylogenetic() {
        upload("phylogeneticForm");
    }

    function uploadGene() {
        upload("geneForm");
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
        if (formID == "geneForm") {
            $("#geneLoading").show();
            filename = $("#gene").val();
        }

        filename = filename.split(/(\\|\/)/g).pop();

        $.ajax({
            url: "/upload",
            type: "POST",
            xhr: function() {
                var xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener("progress", function(evt) {
                    if (evt.lengthComputable) {
                        var percentComplete = (evt.loaded / evt.total) * 100;

                        if (formID == "biomForm") {
                            $("#biomLoadingProgress").text(percentComplete);
                        }
                        if (formID == "otuTableForm") {
                            $("#otuTableLoadingProgress").text(percentComplete);
                        }
                        if (formID == "otuTaxonomyMappingForm") {
                            $("#otuTaxonomyMappingLoadingProgress").text(percentComplete);
                        }
                        if (formID == "otuMetadataForm") {
                            $("#otuMetadataLoadingProgress").text(percentComplete);
                        }
                        if (formID == "phylogeneticForm") {
                            $("#phylogeneticLoadingProgress").text(percentComplete);
                        }
                        if (formID == "geneForm") {
                            $("#geneLoadingProgress").text(percentComplete);
                        }
                    }
               }, false);
               return xhr;
            },
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
                if (formID == "geneForm") {
                    $("#geneLoading").hide();
                    $("#geneOK").show();
                    $("#geneText").text("Replace");
                    $("#projectGeneName").val(filename);
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
