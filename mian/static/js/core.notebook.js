$(document).ready(function() {
    $(".notebook .editable-title").on('focusout', function() {
        var data = {
            pid: $(this).data("pid"),
            key: $(this).data("key"),
            title: $(this).text(),
        };

        $.ajax({
            type: "POST",
            url: "/update_notebook_section_title",
            data: data,
            success: function(result) {
            },
            error: function(err) {
                console.log(err);
            }
        });
    });

    $(".notebook .editable-description").on('focusout', function() {
        var data = {
            pid: $(this).data("pid"),
            key: $(this).data("key"),
            description: $(this).text(),
        };

        $.ajax({
            type: "POST",
            url: "/update_notebook_section_description",
            data: data,
            success: function(result) {
            },
            error: function(err) {
                console.log(err);
            }
        });
    });

    $(".notebook .section-delete").click(function() {
        var data = {
            pid: $(this).data("pid"),
            key: $(this).data("key")
        };
        var sectionKey = $(this).data("key");

        $.ajax({
            type: "POST",
            url: "/delete_notebook_section",
            data: data,
            success: function(result) {
                $("#section-" + sectionKey).remove();
            },
            error: function(err) {
                console.log(err);
            }
        });
    });
});
