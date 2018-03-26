$(document).ready(function() {
  var changeProject = "";
  var changeSubsamplingAnchor = null;
  hideLoading();

  $(".project-delete").click(function() {
    var project_name = $(this).data("projectname");
    var project = $(this).data("project");
    bootbox.confirm("Are you sure you want to delete " + project_name + "?", function(result) {
      if (result) {
        var data = {
          "project": project,
          "delete": "delete"
        };

        $.ajax({
          type: "POST",
          url: "deleteProject",
          data: data,
          success: function(result) {
            // TODO: Fix to use IDs
            $("#p-" + project).remove();
          },
          error: function(err) {
            console.log(err)
          }
        });
      }
    });
  });

  $(".project-trig-otu").click(function() {
    var project = $(this).data("project");
    $(this).siblings('.project-replace-otu').trigger('click');
  });

  $(".project-trig-tax").click(function() {
    var project = $(this).data("project");
    $(this).siblings('.project-replace-taxonomy').trigger('click');
  });

  $(".project-trig-metadata").click(function() {
    var project = $(this).data("project");
    $(this).siblings('.project-replace-metadata').trigger('click');
  });

  $(".project-replace-otu").change(function() {
    upload($(this));
  });

  $(".project-replace-taxonomy").change(function() {
    upload($(this));
  });

  $(".project-replace-metadata").change(function() {
    upload($(this));
  });

  $(".project-change-subsampling").click(function() {
    var project = $(this).data("project");
    var subsampled = $(this).data("subsampleval");
    $('#change-subsampling').val(subsampled);
    $('#change-box').show();
    $('#blackout').show();
    changeProject = project;
    changeSubsamplingAnchor = $(this);
  });

  $("#change-close").click(function() {
    $("#change-box").hide();
    $('#blackout').hide();
  });

  $(".change-cancel").click(function() {
    $("#change-box").hide();
    $('#blackout').hide();
  });

  $(".change-confirm").click(function() {
    $("#change-box").hide();
    $('#blackout').hide();

    showLoading();
    var subsampleTo = $("#change-subsampling").val();

    var data = {
      "pid": changeProject,
      "subsampleType": "manual",
      "subsampleTo": subsampleTo
    };

    changeSubsampling(data);
  });

  $(".change-auto").click(function() {
    $("#change-box").hide();
    $('#blackout').hide();

    showLoading();

    var data = {
      "pid": changeProject,
      "subsampleType": "auto",
      "subsampleTo": 0
    };
    changeSubsampling(data);
  });

  $(".change-reset").click(function() {
    $("#change-box").hide();
    $('#blackout').hide();

    showLoading();

    var data = {
      "pid": changeProject,
      "subsampleType": "no",
      "subsampleTo": 0
    };
    changeSubsampling(data);
  });

  function changeSubsampling(data) {
    $.ajax({
      type: "POST",
      url: "changeSubsampling",
      data: data,
      success: function(result) {
        hideLoading();
        var subsampleType = data.subsampleType;
        if (result == 0) {
          $("#subsampleDisplayContainer-" + changeProject).text("Not Subsampled");
        } else {
          if (subsampleType == "auto") {
            $("#subsampleDisplayContainer-" + changeProject).html("Subsampled to <b id=\"subsampleDisplayVal-" + changeProject + "\">" + result + " (auto)</b>");
          } else {
            $("#subsampleDisplayContainer-" + changeProject).html("Subsampled to <b id=\"subsampleDisplayVal-" + changeProject + "\">" + result + "</b>"); 
          }
        }

        changeSubsamplingAnchor.data("subsampletype", data.subsampleType);
        changeSubsamplingAnchor.data("subsampleval", result);

        $("#otu-table-modified").show();
        setTimeout(function() {
          $("#otu-table-modified").hide();
        }, 2000);
      },
      error: function(err) {
        hideLoading();
        console.log(err);
        $("#otu-table-modified-error").show();
        setTimeout(function() {
          $("#otu-table-modified-error").hide();
        }, 2000);
      }
    });
  }

  function upload($selected) {
    var fileType = $selected.siblings(".replace-fileType").val();
    if (fileType === "otuTable") {
      var changeSubsampleButton = $selected.parent().parent().parent().find(".project-change-subsampling");
      var subsampleType = changeSubsampleButton.data("subsampletype");
      var subsampleTo = changeSubsampleButton.data("subsampleval");
      $selected.siblings(".replace-subsampleType").val(subsampleType);
      $selected.siblings(".replace-subsampleTo").val(subsampleTo);
    }

    var $formQ = $selected.parent();

    var form = $formQ[0];
    var formData = new FormData(form);

    showLoading();

    $.ajax({
        url: 'uploadReplace',
        type: 'POST',
        data: formData,
        cache: false,
        dataType: "json",
        processData: false, // Don't process the files
        contentType: false, // Set content type to false as jQuery will tell the server its a query string request
        success: function(data, textStatus, jqXHR) {
          hideLoading();

          var status = data["status"];
          var fn = data["fn"];

          if (status === "OK") {
            $selected.parent().parent().siblings(".project-fn").text(fn);
          }
          
          if (fileType === "otuTable") {
            if (status === "OK") {
              var subsampleResultType = data["subsampleType"];
              var subsampleResultTo = data["subsampleTo"];
              var displayContainer = $selected.parent().parent().parent().find(".subsampleDisplaySpan");

              if (subsampleResultTo == 0) {
                displayContainer.text("Not Subsampled");
              } else {
                if (subsampleResultType == "auto") {
                  displayContainer.html("Subsampled to <b id=\"subsampleDisplayVal-" + changeProject + "\">" + subsampleResultTo + " (auto)</b>");
                } else {
                  displayContainer.html("Subsampled to <b id=\"subsampleDisplayVal-" + changeProject + "\">" + subsampleResultTo + "</b>");
                }
              }

              $selected.parent().parent().parent().find(".project-change-subsampling").data("subsampletype", subsampleResultType);
              $selected.parent().parent().parent().find(".project-change-subsampling").data("subsampleval", subsampleResultTo);
            }
          }

          $selected.replaceWith($selected = $selected.clone(true));

          if (status === "OK") {
            $("#otu-table-modified").show();
            setTimeout(function() {
              $("#otu-table-modified").hide();
            }, 2000);
          } else {
            $("#otu-table-modified-error").show();
            setTimeout(function() {
              $("#otu-table-modified-error").hide();
            }, 2000);
          }
        },
        error: function(jqXHR, textStatus, errorThrown) {
          console.log('Error: ' + textStatus);
          alert("An error occurred")
        }
    });
  }
});