# Use official R base image
FROM r-base:4.3.1

# Install system dependencies required for R packages
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

# Set working directory
WORKDIR /app

# Copy DESCRIPTION file separately to leverage Docker layer caching
COPY DESCRIPTION /app/DESCRIPTION

# Install required R packages (optimize caching)
RUN R -e 'install.packages("remotes", repos="https://cloud.r-project.org")' \
    && R -e 'remotes::install_deps("/app", dependencies=TRUE)'

# Copy remaining app files
COPY . /app

# Expose the Shiny app port
EXPOSE 3838

# Set environment variables for stability
ENV R_REMOTES_NO_ERRORS_FROM_WARNINGS=true
ENV R_LIBS_USER=/usr/local/lib/R/site-library

# Run the Shiny app
CMD ["R", "-e", "shiny::runApp(\"/app/app.R\", host=\"0.0.0.0\", port=3838)"]
