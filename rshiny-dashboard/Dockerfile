FROM r-base:4.3.1

# Install system dependencies
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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all files
COPY . /app

# Install R dependencies
RUN R -e 'install.packages(c("shiny", "shinydashboard", "ggplot2", "dplyr", "httr", "jsonlite", "DT", "tidyr", "scales"))'

# Expose the Shiny app port
EXPOSE 3838

# Run the Shiny app
CMD ["R", "-e", "shiny::runApp(\"/app/app.R\", host=\"0.0.0.0\", port=3838)"]
