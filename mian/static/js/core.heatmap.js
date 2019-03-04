// ============================================================
// Heatmap JS Component
// ============================================================

var expectedLoadFactor = 300;

//
// Initialization
//
initializeFields();
initializeComponent({
    hasCatVar: true,
    hasCatVarNoneOption: true
});
createSpecificListeners();

//
// Initializes fields based on the URL params
//
function initializeFields() {
    if (getParameterByName("corrvar1") !== null) {
        $("#corrvar1").val(getParameterByName("corrvar1"));
    }
    if (getParameterByName("corrvar2") !== null) {
        $("#corrvar2").val(getParameterByName("corrvar2"));
    }
    if (getParameterByName("cluster") !== null) {
        $("#cluster").val(getParameterByName("cluster"));
    }
    if (getParameterByName("showlabels") !== null) {
        $("#showlabels").val(getParameterByName("showlabels"));
    }
    if (getParameterByName("minSamplesPresent") !== null) {
        $("#minSamplesPresent").val(getParameterByName("minSamplesPresent"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#corrvar1").change(function() {
        updateAnalysis();
    });
    $("#corrvar2").change(function() {
        updateAnalysis();
    });
    $("#cluster").change(function() {
        updateAnalysis();
    });
    $("#showlabels").change(function() {
        updateAnalysis();
    });
    $("#minSamplesPresent").change(function() {
        updateAnalysis();
    });
    $("#download-svg").click(function() {
        downloadSVG("heatmap." + $("#corrvar1").val() + "." + $("#corrvar2").val());
    });
}

//
// Analysis Specific Methods
//
function customLoading() {}

function uncompress(base64data) {
    compressData = atob(base64data);
    compressData = compressData.split('').map(function(e) {
        return e.charCodeAt(0);
    });
    binData = new Uint8Array(compressData);
    data = pako.inflate(binData);

    var bufView = new Uint16Array(data);
    var length = bufView.length;
    var result = '';
    var addition = Math.pow(2, 16) - 1;

    for (var i = 0; i < length; i += addition) {
        if (i + addition > length) {
            addition = length - i;
        }
        result += String.fromCharCode.apply(null, bufView.subarray(i, i + addition));
    }

    return result;
}

function updateAnalysis() {
    showLoading(expectedLoadFactor);

    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var corrvar1 = $("#corrvar1").val();
    var corrvar2 = $("#corrvar2").val();
    var cluster = $("#cluster").val();
    var minSamplesPresent = $("#minSamplesPresent").val();

    var data = {
        pid: $("#project").val(),
        taxonomyFilterCount: getLowCountThreshold(),
        taxonomyFilterPrevalence: getPrevalenceThreshold(),
        taxonomyFilter: taxonomyFilter,
        taxonomyFilterRole: taxonomyFilterRole,
        taxonomyFilterVals: taxonomyFilterVals,
        sampleFilter: sampleFilter,
        sampleFilterRole: sampleFilterRole,
        sampleFilterVals: sampleFilterVals,
        level: level,
        corrvar1: corrvar1,
        corrvar2: corrvar2,
        cluster: cluster,
        minSamplesPresent: minSamplesPresent
    };

    setGetParameters(data);

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/heatmap" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            var abundancesObj = JSON.parse(uncompress(result));
            var rowHeaders = abundancesObj["row_headers"];
            var colHeaders = abundancesObj["col_headers"];

            if (rowHeaders.length === 0 || colHeaders.length === 0) {
                loadNoResults();
            } else {
                loadSuccess();
                var corrvar1 = $("#corrvar1").val();
                var corrvar2 = $("#corrvar2").val();
                renderHeatmap(abundancesObj, -1, 1, corrvar1, corrvar2);
            }
        },
        error: function(err) {
            loadError();
            console.log(err);
        }
    });
}
