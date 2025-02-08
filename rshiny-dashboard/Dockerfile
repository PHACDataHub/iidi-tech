FROM r-base:4.3.1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libcurl4-openssl-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && R -e 'install.packages(c(\
        "shiny", \
        "shinydashboard", \
        "ggplot2", \
        "dplyr", \
        "httr", \
        "jsonlite", \
        "DT", \
        "tidyr", \
        "scales"), \
        repos="https://cloud.r-project.org/")' \
    && rm -rf /tmp/downloaded_packages/

COPY app.R /app.R

EXPOSE 3838

CMD ["R", "-e", "shiny::runApp('/app.R', host='0.0.0.0', port=3838)"]
