$(document).ready(function() {
  var changeProject = "";
  var changeSubsamplingAnchor = null;

  $(".project-delete").click(function() {
    var project = $(this).data("project");
    bootbox.confirm("Are you sure you want to delete " + project + "?", function(result) {
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

  $(".project-change-subsampling").click(function() {
    var project = $(this).data("project");
    var subsampled = $(this).data("subsampled");
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
        if (result == 0) {
          $("#subsampleDisplayContainer-" + changeProject).text("Not Subsampled");
        } else {
          $("#subsampleDisplayContainer-" + changeProject).html("Subsampled to <b id=\"subsampleDisplayVal-" + changeProject + "\">" + result + "</b> Seqs");
        }

        changeSubsamplingAnchor.data("subsampled", result);
        $(".project-change-subsampling")
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
});