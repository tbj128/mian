$(document).ready(function() {
  var changeProject = "";
  var changeSubsamplingAnchor = null;
  hideLoading();

  // Popovers on the create page
  $('[data-toggle="popover"]').popover();

  $(".project-delete").click(function() {
    var project_name = $(this).data("projectname");
    var project = $(this).data("project");
    bootbox.confirm(
      "Are you sure you want to delete " + project_name + "?",
      function(result) {
        if (result) {
          var data = {
            project: project,
            delete: "delete"
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
              console.log(err);
            }
          });
        }
      }
    );
  });

  $(".project-trig-biom").click(function() {
    var project = $(this).data("project");
    $(this)
      .siblings(".project-replace-biom")
      .trigger("click");
  });
  $(".project-trig-otu").click(function() {
    var project = $(this).data("project");
    $(this)
      .siblings(".project-replace-otu")
      .trigger("click");
  });
  $(".project-trig-tax").click(function() {
    var project = $(this).data("project");
    $(this)
      .siblings(".project-replace-taxonomy")
      .trigger("click");
  });
  $(".project-trig-metadata").click(function() {
    var project = $(this).data("project");
    $(this)
      .siblings(".project-replace-metadata")
      .trigger("click");
  });

  $(".project-replace-biom").change(function() {
    upload($(this));
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
    $("#change-subsampling").val(subsampled);
    $("#change-box").show();
    $("#blackout").show();
    changeProject = project;
    changeSubsamplingAnchor = $(this);
  });

  $("#change-close").click(function() {
    $("#change-box").hide();
    $("#blackout").hide();
  });

  $(".change-cancel").click(function() {
    $("#change-box").hide();
    $("#blackout").hide();
  });

  $(".change-confirm").click(function() {
    $("#change-box").hide();
    $("#blackout").hide();

    showLoading();
    var subsampleTo = $("#change-subsampling").val();

    var data = {
      pid: changeProject,
      subsampleType: "manual",
      subsampleTo: subsampleTo
    };

    changeSubsampling(data);
  });

  $(".change-auto").click(function() {
    $("#change-box").hide();
    $("#blackout").hide();

    showLoading();

    var data = {
      pid: changeProject,
      subsampleType: "auto",
      subsampleTo: 0
    };
    changeSubsampling(data);
  });

  $(".change-reset").click(function() {
    $("#change-box").hide();
    $("#blackout").hide();

    showLoading();

    var data = {
      pid: changeProject,
      subsampleType: "no",
      subsampleTo: 0
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
        window.location.reload(true);
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
