### Local Installation
The following instructions are for an example installation of Mian on an Apache web server. However, because Mian uses Flask as the WSGI web application framework, any compatible web server can be used instead.

- Install the `apache2`, `pipenv`, and `git` packages.
- Install `Python 3` globally
- Install `R` globally (any recent version >= 3.6.1 should work)
  - For instance, if you were installing onto an Ubuntu server, you would use `sudo apt-get install r-base-dev`
- Navigate to the folder on the server where you want to install Mian. In this example, we will just install into the `/var/www/html/` directory
- Within the `/var/www/html/` directory, retrieve the Mian repository from Github using: `git clone https://github.com/tbj128/mian.git`
- Give Apache permissions to the Mian directory: `sudo chown -R www-data:www-data mian`
- Within the `/var/www/html/mian` directory, create a new Python 3 virtualenv through `pipenv --three`
- Install the Python dependencies by running `pipenv install`
- Set up the Apache web server by configuring the Virutal Host configuration file. Refer to [this file](https://gist.github.com/tbj128/e998b01f5a03d5c7d49bd056f153e7a6) for an example.
- Run `sudo a2ensite <your web address>`
- Restart the Apache server: `sudo apachectl restart`. Note that the required R dependencies will be installed when the page is first loaded.

