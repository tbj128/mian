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
## Install on modern OS with Python > 3.6.x
## Method 1: Docker

The repository includes a `Dockerfile`, `docker-compose.yml`, and `requirements.txt`. This is the recommended approach for running Mian on a modern OS without having to manage Python or R dependencies manually.

**Requirements:** Docker Engine 20.10+. Docker Compose V2 (`docker compose` with a space) is recommended. V1 (`docker-compose` with a hyphen) works with the workaround described below.

**First-time setup**

```
git clone https://github.com/tbj128/mian.git
cd mian
docker compose up --build -d
```

The first build will take a while — R packages are compiled from source. Subsequent starts are fast. Once running, open `http://localhost:5000` in your browser.

**Starting and stopping**

With Docker Compose V2:
```
# Start (after code or config changes)
docker compose up --build -d

# Start (no changes since last run)
docker compose up -d

# Stop (data is preserved)
docker compose down

# View logs
docker compose logs -f
```

With Docker Compose V1 (`docker-compose` with a hyphen) — V1 has a known bug with modern Docker Engine that causes a crash when recreating an existing container. Always run `down` before `up` to avoid it:
```
docker-compose down && docker-compose up --build -d
docker-compose down && docker-compose up -d
```
Upgrading to V2 is strongly recommended: `sudo apt-get install docker-compose-plugin`

**Configuration**

Runtime settings are controlled via the `environment:` section of `docker-compose.yml`:

| Variable | Docker default | Description |
|---|---|---|
| `FLASK_HOST` | `0.0.0.0` | Interface to bind to |
| `FLASK_DEBUG` | `0` | Set to `1` to enable Flask debug mode |
| `FLASK_PROCESSES` | `5` | Number of worker processes (each loads R into memory ~200-400 MB) |
| `MIAN_RUNTIME_R_INSTALL` | `0` | Set to `1` to allow missing R packages to be installed at runtime |

**LDAP**

By default the Docker image runs without LDAP (the "Try Demo", "Signup", and "Continue Without Signup" buttons are shown on the homepage). To enable LDAP, copy `mian/config.ini.example` to `mian/config.ini`, fill in your LDAP settings, and rebuild the image.

**Persistence**

User data is stored in a named Docker volume (`mian_data`) mounted at `/usr/src/app/mian/data`. It survives container restarts and image rebuilds. The volume name is fixed and does not depend on the directory you launch from.

To remove the volume and all stored data permanently:
```
docker compose down -v
```
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