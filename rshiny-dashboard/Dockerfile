FROM r-base:4.3.1

RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN R -e 'install.packages(c("ggplot2", "shinydashboard", "httr", "jsonlite", "shinythemes", "dplyr"), repos="https://cloud.r-project.org/")'

COPY app.R /app.R

EXPOSE 3838

CMD ["R", "-e", "shiny::runApp('/app.R', host='0.0.0.0', port=3838)"]