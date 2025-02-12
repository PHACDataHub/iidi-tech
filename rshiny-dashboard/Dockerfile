FROM r-base:4.3.1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libcurl4-openssl-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY DESCRIPTION /DESCRIPTION
RUN R -e 'install.packages("remotes")' \
    && R -e 'remotes::install_deps("/", dependencies=TRUE)' \
    && rm -rf /tmp/downloaded_packages/

COPY app.R /app.R

EXPOSE 3838

CMD ["R", "-e", "shiny::runApp('/app.R', host='0.0.0.0', port=3838)"]
