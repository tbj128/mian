
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- The above 3 meta tags *must* come first in the head; any other head content must come *after* these tags -->
    <meta name="description" content="">
    <meta name="author" content="">
    <link rel="icon" href="favicon.ico">

    <title>OTUViz</title>

    <!-- Bootstrap core CSS -->
    <link href="static/css/bootstrap.min.css" rel="stylesheet">

    <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
    <!--<link href="static/css/ie10-viewport-bug-workaround.css" rel="stylesheet">-->

    <!-- Custom styles for this template -->
    <link href="static/css/mian_custom.css" rel="stylesheet">
    <link href="static/css/plugins/bootstrap-multiselect.css" rel="stylesheet">
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.6.2/css/font-awesome.min.css">

    <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
      <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->
  </head>

  <body>
    <nav class="navbar navbar-fixed-top">
      <div class="container">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar" aria-expanded="false" aria-controls="navbar">
            <span class="sr-only">Toggle navigation</span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="#">mian</a>
        </div>
        <div id="navbar" class="collapse navbar-collapse">
          <ul class="nav navbar-nav">
            <li class="dropdown">
              <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Analyze <span class="caret"></span></a>
              <ul class="dropdown-menu">
                <li><a href="analyze_correlations.php">Correlations</a></li>
                <li><a href="analyze_experiments.php">Experiments</a></li>
              </ul>
            </li>
            <li class="dropdown">
              <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Data <span class="caret"></span></a>
              <ul class="dropdown-menu">
                <li><a href="add_otus.php">OTUs</a></li>
                <li><a href="add_samples.php">Samples</a></li>
                <li role="separator" class="divider"></li>
                <li><a href="add_experiments.php">Experiments</a></li>
              </ul>
            </li>
            <li><a href="#">About</a></li>
          </ul>
        </div><!--/.nav-collapse -->
      </div>
    </nav>

    <div class="highlight">
      <h2><i class="fa fa-bar-chart"></i> Visualize OTU tables in your browser. </h2>
      <h4>Start by uploading the following files below. <a href="#" style="color:#FFF;">Learn more...</a></h4>
      <h2><i class="fa fa-chevron-down"></i></h2>
    </div>

    <div id="welcome" class="container">
      <div id="welcome-container" class="row welcome-container">
        <div class="row upload-item">
          <div class="col-md-9">
            <h3 style="margin-top:0px">OTU Table</h3>
            <h5>CSV-formatted file with OTUs across the top header and sample/group IDs as rows</h5>
          </div>
          <div class="col-md-3 upload-status">
            <form id="otuTableForm" action="/upload" method="post" enctype="multipart/form-data">
              <input type="hidden" name="category" value="otuTable" />
              % if otuTable == 1:
                <span id="otuTableOK" style="font-size:24px;margin:0 20px 0 0;vertical-align: middle;"><i class="glyphicon glyphicon-ok"></i></span>
                <span id="otuTableWrapper" class="btn btn-default btn-file">
                    <span id="otuTableText">Replace</span> <input type="file" name="upload" id="otuTable" accept=".csv" />
                </span>
              % else:
                <span id="otuTableOK" style="display:none;font-size:24px;margin:0 20px 0 0;vertical-align: middle;"><i class="glyphicon glyphicon-ok"></i></span>
                <span id="otuTableWrapper" class="btn btn-default btn-file">
                    <span id="otuTableText">Upload</span> <input type="file" name="upload" id="otuTable" accept=".csv" />
                </span>
              % end
            </form>
          </div>
        </div>

        <div class="row upload-item">
          <div class="col-md-9">
            <h3 style="margin-top:0px">OTU Taxonomy Mapping</h3>
            <h5>CSV-formatted file with each row representing an OTU and its corresponding taxonomy information</h5>
          </div>
          <div class="col-md-3 upload-status">
            <form id="otuTaxonomyMappingForm" action="/upload" method="post" enctype="multipart/form-data">
              <input type="hidden" name="category" value="otuTaxonomyMapping" />
              % if taxaMap == 1:
                <span id="otuTaxonomyMappingOK" style="font-size:24px;margin:0 20px 0 0;vertical-align: middle;"><i class="glyphicon glyphicon-ok"></i></span>
                <span id="otuTaxonomyMappingWrapper" class="btn btn-default btn-file">
                    <span id="otuTaxonomyMappingText">Replace</span> <input type="file" name="upload" id="otuTaxonomyMapping" accept=".csv" />
                </span>
              % else:
                <span id="otuTaxonomyMappingOK" style="display:none;font-size:24px;margin:0 20px 0 0;vertical-align: middle;"><i class="glyphicon glyphicon-ok"></i></span>
                <span id="otuTaxonomyMappingWrapper" class="btn btn-default btn-file">
                    <span id="otuTaxonomyMappingText">Upload</span> <input type="file" name="upload" id="otuTaxonomyMapping" accept=".csv" />
                </span>
              % end
            </form>
          </div>
        </div>

        <div class="row upload-item">
          <div class="col-md-9">
            <h3 style="margin-top:0px">Sample ID Mapping</h3>
            <h5>CSV-formatted file with each row representing an sample/group ID and its corresponding metadata</h5>
          </div>
          <div class="col-md-3 upload-status">
            <form id="otuMetadataForm" action="/upload" method="post" enctype="multipart/form-data">
              <input type="hidden" name="category" value="otuMetadata" />
              % if metadata == 1:
                <span id="otuMetadataOK" style="font-size:24px;margin:0 20px 0 0;vertical-align: middle;"><i class="glyphicon glyphicon-ok"></i></span>
                <span id="otuMetadataWrapper" class="btn btn-default btn-file">
                    <span id="otuMetadataText">Replace</span> <input type="file" name="upload" id="otuMetadata" accept=".csv" />
                </span>
              % else:
                <span id="otuMetadataOK" style="display:none;font-size:24px;margin:0 20px 0 0;vertical-align: middle;"><i class="glyphicon glyphicon-ok"></i></span>
                <span id="otuMetadataWrapper" class="btn btn-default btn-file">
                    <span id="otuMetadataText">Upload</span> <input type="file" name="upload" id="otuMetadata" accept=".csv" />
                </span>
              % end
            </form>
          </div>
        </div>
      </div>
    </div><!-- /.container -->


    <div id="editor" class="editor" style="display:none;">
      <h3>Correlation Analysis</h3>
      <label class="control-label">Taxonomic Level</label>
      <select id="taxonomy" name="taxonomy" class="form-control pad-bottom">
        <option value="Kingdom">Kingdom</option>
        <option value="Phylum">Phylum</option>
        <option value="Class">Class</option>
        <option value="Order">Order</option>
        <option value="Family">Family</option>
        <option value="Genus">Genus</option>
        <option value="Species">Species</option>
        <option value="OTU">OTU</option>
      </select>

      <select style="display:none;" id="taxonomy-specific" name="taxonomy-specific" class="form-control pad-bottom" multiple="multiple">
      </select>

      <hr />

      <label class="control-label">Correlation Variable</label>
      <select id="corrvar" name="corrvar" class="form-control">
        <option value="SAV">SAV</option>
        <option value="VvCD68">CD68</option>
        <option value="VvCD79a">CD79a</option>
        <option value="VvCD4">CD4</option>
      </select>

      <label class="control-label">Color Variable</label>
      <select id="colorvar" name="colorvar" class="form-control">
        <option value="None">None</option>
        <option value="Disease">Disease</option>
        <option value="Location">Location</option>
        <option value="Individual">Individual</option>
        <option value="Core">Core</option>
        <option value="Fibrosis">Fibrosis</option>
        <option value="Batch">Batch</option>
      </select>

      <label class="control-label">Size Variable</label>
      <select id="sizevar" name="sizevar" class="form-control">
        <option value="None">None</option>
        <option value="SAV">SAV</option>
        <option value="VvCD68">CD68</option>
        <option value="VvCD79a">CD79a</option>
        <option value="VvCD4">CD4</option>
      </select>
    </div>

    <div id="analysis-container" class="analysis-container" style="display:none;">
    </div><!-- /.container -->


    <!-- Bootstrap core JavaScript
    ================================================== -->
    <!-- Placed at the end of the document so the pages load faster -->
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
    <script>window.jQuery || document.write('<script src="static/js/vendor/jquery.min.js"><\/script>')</script>
    <script src="static/js/bootstrap.min.js"></script>
    <script src="static/js/d3.js"></script>
    <script src="static/js/jquery.csv.js"></script>
    <script src="static/js/plugins/bootstrap-multiselect.js"></script>
    <script src="static/js/core.js"></script>

    <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
    <!--<script src="static/js/ie10-viewport-bug-workaround.js"></script>-->

  </body>
</html>
