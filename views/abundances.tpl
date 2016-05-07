
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

    <title>OTUViz Abundances</title>

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

    <div id="editor" class="editor">
      <h3>Abundances Analysis</h3>
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

      <label class="control-label">Categorical Variable</label>
      <select id="catvar" name="catvar" class="form-control">
      </select>
    </div>

    <div id="analysis-container" class="analysis-container" style="min-height:500px;">
    </div><!-- /.container -->
    <hr style="margin-top:0px; margin-bottom:0px;" />
    <div id="stats-container" class="analysis-container" style="display:none;">
      <h4>Welch's T-Test Summary</h4>
      <table class="table table-hover"> 
        <thead> 
          <tr> 
            <th>Category 1</th> 
            <th>Category 2</th> 
            <th>P-Value</th> 
          </tr> 
        </thead> 
        <tbody id="stats-rows"> 
        </tbody>
      </table>
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
    <script src="static/js/core.correlations.js"></script>

    <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
    <!--<script src="static/js/ie10-viewport-bug-workaround.js"></script>-->

  </body>
</html>
