### Local Installation
The following instructions are for an example installation of Mian on an Apache web server. However, because Mian uses Flask as the WSGI web application framework, any compatible web server can be used instead.

- Install the `apache2`, `pipenv`, and `git` packages.
- Install `Python 3` globally
- Install `R` globally (any recent version >= 3.6.1 should work)
  - For instance, if you were installing onto an Ubuntu server, you would use `sudo apt-get install r-base-dev`
  - May need to install 'data.table' package manually using R.
- Navigate to the folder on the server where you want to install Mian. In this example, we will just install into the `/var/www/html/` directory
- Within the `/var/www/html/` directory, retrieve the Mian repository from Github using: `git clone https://github.com/tbj128/mian.git`
- Give Apache permissions to the Mian directory: `sudo chown -R www-data:www-data mian`
- Within the `/var/www/html/mian` directory, create a new Python 3 virtualenv through `pipenv --three`
- Install the Python dependencies by running `pipenv install`
- Set up the Apache web server by configuring the Virutal Host configuration file. Refer to [this file](https://gist.github.com/tbj128/e998b01f5a03d5c7d49bd056f153e7a6) for an example.
- Run `sudo a2ensite <your web address>`
- Restart the Apache server: `sudo apachectl restart`. Note that the required R dependencies will be installed when the page is first loaded.

#### Python Notes
- Mian must be run with Python < 3.7 due to limitations in how the function timeout works. The multiprocessing library in these newer versions appears to trigger infinite reloading of the main file.

#### Tensorflow Notes
- On M1 ARM64 Macbooks, Mian was tested under Rosetta 2. Tensorflow must be built from source (without AVX or GPU) to achieve a version compatible with Python 3.6 (following instructions from https://www.tensorflow.org/install/source )  
___  
## Install on modern OS with python > 3.6.x
## Method 1: Docker
- You can use the procedure and Dockerfile below to create a docker image that runs mian.
```
mkdir main_docker
cd mian_docker
git clone https://github.com/tbj128/mian.git
```
- Create a file called **requirements.txt** filled with:
```
biom-format
flask==1.1.1
flask-login==0.4.0
Flask-Mail==0.9.1
h5py
rpy2==3.1.0
scikit-learn
scipy
werkzeug==1.0.1
scikit-bio
pandas==1.0.3
Keras==2.3.1
Boruta
tensorflow==2.5.0
traitlets==4.3.3
numpy
cython
```
- Dockerfile
```
FROM python:3.6.7

# set working directory in container
WORKDIR /usr/src/app

# Copy and install packages
COPY requirements.txt /
RUN pip install --upgrade pip
RUN pip install -r /requirements.txt


# Install needed system tools
RUN apt-get update \
        && apt-get install -y --no-install-recommends \
        software-properties-common apt-transport-https gfortran libblas-dev liblapack-dev \
        && rm -rf /var/lib/apt/lists/*

# Install R
RUN gpg --batch --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys E19F5F87128899B192B1A2C2AD5F960A256A04AF && gpg -a --export E19F5F87128899B192B1A2C2AD5F960A256A04AF | apt-key add -
RUN add-apt-repository 'deb https://cloud.r-project.org/bin/linux/debian stretch-cran35/'
RUN apt-get update \
        && apt-get install -y --no-install-recommends --allow-unauthenticated \
        r-base \
        && rm -rf /var/lib/apt/lists/*

# Install R packages
RUN R -e "install.packages(c('vegan', 'RColorBrewer', 'ranger', 'Boruta', 'BiocManager', 'remotes'), repos='https://cloud.r-project.org/')"
RUN R -e "library('remotes'); install_version('locfit', '1.5.9.4'); install_version('Hmisc', '4.4')"
RUN R -e "BiocManager::install('DESeq2')"

# Copy app folder to app folder in container
COPY /mian /usr/src/app/

# Run app
CMD python run.py
```
- Build the image and run. The first step will take a while.
```
docker build -t mian .
docker run -d --name mian -p 5000:5000 mian
```
- This is good for testing, but there is no persistence. You will have to make sure the database and data dirs (/usr/src/app/mian/mian.db and /usr/src/app/mian/data) are not inside the container.
___  

## Method 2: Conda
Follow the procedure below to install inside a conda environment. This procedure also installs and uses apache mod_wsgi that is controlled by systemd.  
This example was developed on ALmaLinux 9.1

- Donwload conda with python==3.6.5 https://repo.anaconda.com/miniconda/Miniconda3-4.5.4-Linux-x86_64.sh
- Install conda into **/opt/miniconda3**:
```
bash Miniconda3-4.5.4-Linux-x86_64.sh
```
- Activate conda with:
```
echo ". /opt/miniconda3/etc/profile.d/conda.sh" >> ~/.bashrc
. /opt/miniconda3/etc/profile.d/conda.sh
conda create -n mian gxx_linux-64
conda activate mian
```
- upgrade pip:
```
conda install pip=9
pip install --upgrade pip
```

- create a requirements.txt file and paste the following:
```
biom-format
flask==1.1.1
flask-login==0.4.0
Flask-Mail==0.9.1
flask-ldap3-login
h5py
rpy2==3.1.0
scikit-learn
scipy
werkzeug==1.0.1
scikit-bio
pandas==1.0.3
Keras==2.3.1
Boruta
tensorflow==2.5.0
traitlets==4.3.3
numpy
cython
configparser
```
- Install requirements:
```
pip install -r requirements.txt
```
- Optionally set compile threads to speed up R package compilation a bit.
```
export MAKE="make -j$(nproc)"
```
- Install R packages:
```
conda install r-base r-RColorBrewer r-ranger r-Boruta r-Hmisc r-XML r-remotes r-BiocManager r-permute
R -e "library('remotes'); install_version('locfit', '1.5-9.4', repos='https://cloud.r-project.org/')"
R -e "install.packages('vegan', repos='https://cloud.r-project.org/')"
R -e "BiocManager::install('DESeq2')"
```
- Setup apache
```
dnf install httpd httpd-devel
pip install mod_wsgi
```
- Clone the mian repo and set permissions  
I'm using user webdev here, but it can be any other user
```
cd /opt
git clone https://github.com/tbj128/mian.git
chown -R webdev:apache /opt/mian
chown -R webdev:apache /opt/miniconda3
```	
- Create the file **/opt/mian/mian.wsgi** for mod_wsgi:
```
import sys

sys.path.insert(0, '/opt/mian')

print("App Startup")

from mian.main import app as application

application.secret_key = 'Twilight Sparkle'
application.config['SESSION_TYPE'] = 'filesystem'
```
- Create the config files for the webserver (replace variables with your actual values).
```
mkdir /etc/mian
mod_wsgi-express setup-server /opt/mian/mian.wsgi --user webdev --group apache --https-port 443 --https-only --server-name 10.5.87.61 --ssl-certificate-key-file /etc/pki/tls/private/vlan87.key --ssl-certificate-file /etc/pki/tls/certs/vlan87.pem --server-root=/etc/mian/mod_wsgi-express-443
```
- Add the following two lines directly after the shebang (#!/usr/bin/bash) in **/etc/mian/mod_wsgi-express-443/apachectl**
```
source /opt/miniconda3/etc/profile.d/conda.sh
conda activate mian
```
- Change the following in /etc/mian/mod_wsgi-express-443/httpd.conf  
  The first enables slightly more verbose logging, the second enables uploads of files larger than 10MB
```
LogLevel info
LimitRequestBody 2073741824
```
- You can now start, stop or restart the server with:
```
/etc/mian/mod_wsgi-express-443/apachectl start
```
- If you want to use systemd so you can have it automatically start at system startup, create a systemd file. Create **/etc/systemd/system/mian.service** that contains the following.
```
[Unit]
Description=The Mian app
After=network.target remote-fs.target nss-lookup.target

[Service]
Type=forking
ExecStart=/etc/mian/mod_wsgi-express-443/apachectl -k start
ExecReload=/etc/mian/mod_wsgi-express-443/apachectl -k graceful
ExecStop=/etc/mian/mod_wsgi-express-443/apachectl -k graceful-stop
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```
- First reload systemd, then you can start and stop the app with:
```
systemctl daemon-reload
systemctl start mian.service
```
- To make the app start at boot:
```
systemctl enable mian.service
```