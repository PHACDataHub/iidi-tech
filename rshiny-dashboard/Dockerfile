FROM rocker/shiny:4.3.1

ENV R_REMOTES_NO_ERRORS_FROM_WARNINGS=true
ENV R_LIBS_USER=/usr/local/lib/R/site-library

RUN apt-get update && apt-get install -y --no-install-recommends \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libfontconfig1-dev \
    libfreetype6-dev \
    libpng-dev \
    libtiff5-dev \
    libjpeg-dev \
    g++ \
    make \
    libbz2-dev \
    liblzma-dev \
    libicu-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY DESCRIPTION /app/DESCRIPTION

RUN Rscript -e 'install.packages("remotes", repos="https://cloud.r-project.org")' \
    && Rscript -e 'remotes::install_deps("/app", dependencies=TRUE)'

COPY . /app

EXPOSE 3838

CMD ["R", "-e", "shiny::runApp(\"/app/app.R\", host=\"0.0.0.0\", port=3838)"]
