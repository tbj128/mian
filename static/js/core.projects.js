$(document).ready(function() {
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
});