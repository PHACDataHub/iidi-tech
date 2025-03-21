# IIDI Dashboard Documentation

## Overview

The **IIDI Dashboard** is intended as a mock consumer that displayes a dashboard for the immunization summaries from all provinces returned by the [federator API](https://phacdatahub.github.io/iidi-tech/api/federator/). It is an Shiny web application designed to analyze and visualize immunization coverage trends using aggregated data from the **Interoperable Immunization Data Initiative (IIDI)**. The dashboard provides interactive visualizations, metrics, and data exploration tools to help users gain insights into immunization trends across different jurisdictions, age groups, sexes, and years.

### Key Objectives

- **Data Visualization**: Provide interactive charts and graphs to visualize immunization trends and dose distributions.
- **Data Exploration**: Enable users to explore raw data through dynamic filters and a data table.
- **Metrics Display**: Show key metrics such as total immunizations and average dose coverage.

---

## Technology Stack

### Shiny Framework

The dashboard is built using the **Shiny** framework for R, which enables the creation of interactive web applications directly from R scripts. It leverages **shinydashboard** for the layout and UI components, ensuring a clean and organized interface.

### R Libraries

The application uses the following R libraries for data processing, visualization, and interactivity:

- **ggplot2**: For creating visualizations such as histograms and line charts.
- **dplyr**: For data manipulation and filtering.
- **httr** and **jsonlite**: For fetching and parsing data from the API.
- **DT**: For rendering interactive data tables.
- **tidyr** and **scales**: For data wrangling and formatting.

---

## Key Features

1. **Interactive Filters**:

   - Users can filter data by jurisdiction, age group, sex, year, and dose count.
   - Filters dynamically update visualizations and metrics.

2. **Visualizations**:

   - **Dose Count Distribution**: A histogram showing the distribution of dose counts.
   - **Vaccination Coverage Trends**: A line chart displaying trends in vaccination coverage over time.

3. **Metrics**:

   - **Total Immunizations**: Displays the total number of immunizations based on the selected filters.
   - **Average Dose Coverage**: Shows the average dose coverage as a percentage.

4. **Data Table**:

   - Provides a raw data view with pagination and sorting capabilities.

---

## Local Setup

### Prerequisites

- **R (>= 4.3.1)**: Ensure R is installed on your system.
- **Docker**: Optional, for containerized deployment.

### Steps to Run the Dashboard Locally

1. **Clone the Repository**:
   Clone the repo and navigate to the project directory:
   ```bash
   cd rshiny-dashboard
   ```
2. **Install R Dependencies**:
   Open R (or RStudio) and run the following commands to install the required packages:
   ```r
   install.packages("shiny")
   install.packages("shinydashboard")
   install.packages("ggplot2")
   install.packages("dplyr")
   install.packages("httr")
   install.packages("jsonlite")
   install.packages("DT")
   install.packages("tidyr")
   install.packages("scales")
   ```
3. **Run the Application**:
   In the same R session, run the following command to start the Shiny app:

   ```R
   shiny::runApp("app.R")
   ```

4. **Access the Dashboard**:
   Open a web browser and navigate to:
   ```
   http://127.0.0.1:3838
   ```

### Docker Setup (Optional)

1. **Build the Docker Image**:
   From the project root directory, run:
   ```bash
   docker build -t iidi-dashboard .
   ```
2. **Run the Docker Container**:
   Start the container with:
   ```bash
   docker run -p 3838:3838 iidi-dashboard
   ```
3. **Access the Dashboard**:
   Open a web browser and navigate to:
   ```
   Open a web browser and navigate to:
   ```

---

## API Integration

The dashboard fetches aggregated immunization data from an API endpoint defined by the `AGGREGATOR_URL` environment variable. If the variable is not set, it defaults to: `http://federator:3000/aggregated-data` which is the [federator API](https://phacdatahub.github.io/iidi-tech/api/federator/)'s URL inside the federal network of the local docker compose setup.

The API returns summarized vaccination data grouped by jurisdiction, age group, sex, year, and dose count. The expected JSON structure is similar to that of the [federator API](https://phacdatahub.github.io/iidi-tech/api/federator/):

```json
{
  "data": [
    {
      "Age": "string",
      "Count": "numeric",
      "Dose": "numeric",
      "Jurisdiction": "string",
      "OccurrenceYear": "numeric",
      "ReferenceDate": "string",
      "Sex": "string"
    }
  ]
}
```
