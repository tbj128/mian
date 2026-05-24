# rocker/r-ver:3.6.3 is based on Ubuntu 18.04 (Bionic) and ships R 3.6.3,
# which has full CRAN package support — avoiding the R 3.5.2 package availability issues.
FROM rocker/r-ver:3.6.3

WORKDIR /usr/src/app

# Fix apt sources for EOL Buster
RUN sed -i 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' /etc/apt/sources.list \
    && sed -i 's|http://security.debian.org/debian-security|http://archive.debian.org/debian-security|g' /etc/apt/sources.list \
    && sed -i '/buster-updates/d' /etc/apt/sources.list

# Install Python 3 and build tools (Buster archive provides python3.7)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
         python3 python3-dev python3-pip \
       gfortran libblas-dev liblapack-dev \
     && update-alternatives --install /usr/bin/python python /usr/bin/python3 1 \
    && rm -rf /var/lib/apt/lists/*

# Install system libs needed by R packages (png, jpeg, XML, RCurl).
# Uses retry logic because archive.debian.org can be slow/flaky.
RUN for attempt in 1 2 3; do \
      apt-get update \
      && apt-get install -y --no-install-recommends \
           libpng-dev libjpeg-dev libxml2-dev libcurl4-openssl-dev \
      && rm -rf /var/lib/apt/lists/* \
      && break \
      || (echo "apt attempt $attempt failed, retrying in 30s..." && sleep 30); \
    done

# Install R packages deterministically for legacy R 3.6.3.
# Use a frozen CRAN snapshot from when R 3.6 was current.
ENV CRAN_REPO=https://packagemanager.posit.co/cran/2020-04-24

# Layer 1: All required CRAN packages (from frozen snapshot, before BiocManager touches CRAN)
RUN R -e "options(repos=c(CRAN=Sys.getenv('CRAN_REPO'))); install.packages(c( \
    'BiocManager', \
    'RColorBrewer', 'permute', 'lattice', 'vegan', 'ranger', 'Boruta', \
    'XML', 'RCurl', 'locfit', 'matrixStats', 'survival', 'Formula', \
    'Hmisc', 'RSQLite', 'DBI', 'xtable', 'RcppArmadillo', 'ggplot2' \
))"

# Layer 2: Bioconductor core base packages (from bioconductor.org, no CRAN deps needed)
RUN R -e "BiocManager::install(version='3.10', ask=FALSE, update=FALSE); \
    BiocManager::install(c('BiocGenerics','Biobase','S4Vectors','IRanges', \
        'GenomeInfoDbData','GenomeInfoDb','XVector','zlibbioc','BiocParallel'), \
        ask=FALSE, update=FALSE)"

# Layer 3: Genomic infrastructure
RUN R -e "BiocManager::install(c('GenomicRanges','DelayedArray','SummarizedExperiment'), \
    ask=FALSE, update=FALSE)"

# Layer 4: Annotation and DESeq2 CRAN/Bioc dependencies
RUN R -e "BiocManager::install(c('AnnotationDbi','annotate','genefilter','geneplotter'), \
    ask=FALSE, update=FALSE)"

# Layer 5: DESeq2 itself
RUN R -e "BiocManager::install('DESeq2', ask=FALSE, update=FALSE)"

# Ensure libR.so is visible to the runtime linker for rpy2.
RUN echo "/usr/local/lib/R/lib" > /etc/ld.so.conf.d/r.conf \
    && ldconfig

# Install Python packages (rpy2 requires R to be present)
# PIP_DEFAULT_TIMEOUT guards against dropped connections on large downloads (tensorflow is ~450 MB).
ENV PIP_DEFAULT_TIMEOUT=300

COPY requirements.txt /
RUN python -m pip install --upgrade pip \
    && pip install "setuptools<60" "wheel<0.38" "Cython<3" cffi

# tensorflow is ~450 MB — keep it in its own layer so a timeout only retries this step.
RUN grep '^tensorflow' /requirements.txt | xargs pip install

# Remaining packages (excluding the two that need --no-build-isolation).
RUN grep -v '^scikit-bio' /requirements.txt | grep -v '^biom-format' | grep -v '^tensorflow' \
    > /tmp/requirements-no-skbio.txt \
    && pip install -r /tmp/requirements-no-skbio.txt

# biom-format and scikit-bio require --no-build-isolation due to their C extensions.
RUN pip install --no-build-isolation biom-format \
    && pip install --no-build-isolation scikit-bio==0.5.7

# Copy application source
COPY run.py /usr/src/app/
COPY logging.json /usr/src/app/
COPY mian/ /usr/src/app/mian/

# Use the example config as a default if no real config.ini was provided
RUN if [ ! -f /usr/src/app/mian/config.ini ]; then \
        cp /usr/src/app/mian/config.ini.example /usr/src/app/mian/config.ini && \
        sed -i 's/^LDAP_ACTIVE = True/LDAP_ACTIVE = False/' /usr/src/app/mian/config.ini; \
    fi

EXPOSE 5000
CMD ["python", "run.py"]
