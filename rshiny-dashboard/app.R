library(shiny)
library(shinydashboard)
library(ggplot2)
library(dplyr)
library(httr)
library(jsonlite)
library(DT)
library(tidyr)
library(scales)

# API endpoint
api_url <- Sys.getenv("AGGREGATOR_URL", "http://federator:3000/aggregated-data")

# UI
ui <- dashboardPage(
  dashboardHeader(title = "Immunization Coverage Analytics"),
  dashboardSidebar(
    sidebarMenu(
      menuItem("Overview", tabName = "overview", icon = icon("dashboard")),
      menuItem("Trends", tabName = "trends", icon = icon("chart-line")),
      menuItem("Data Explorer", tabName = "data", icon = icon("table")),

      selectInput("jurisdiction", "Select Jurisdiction", 
                  choices = c("All", "ON", "BC"), selected = "All"),
      
      selectInput("ageGroup", "Select Age Group", 
                  choices = c("All", "3-5 years", "6-17 years"), selected = "All"),
      
      selectInput("sex", "Select Sex", 
                  choices = c("All", "Male", "Female", "Other"), selected = "All"),
      
      selectInput("year", "Select Year",
                  choices = c("All", as.character(2010:2025)), selected = "All"),
      
      selectInput("dose", "Select Dose",
                  choices = c("All", "1", "2"), selected = "All")
    )
  ),
  dashboardBody(
    tabItems(
      tabItem(
        tabName = "overview",
        fluidRow(
          valueBoxOutput("totalImmunizations", width = 6),
          valueBoxOutput("avgDoseCount", width = 6)
        )
      ),
      tabItem(
        tabName = "trends",
        fluidRow(
          box(title = "Dose Count Distribution", plotOutput("dose_distribution"), width = 12),
          box(title = "Vaccination Coverage Trends (2 & 7-year-olds)", plotOutput("coverage_trends"), width = 12)
        )
      ),
      tabItem(
        tabName = "data",
        fluidRow(
          box(title = "Raw Data", DTOutput("dataTable"), width = 12)
        )
      )
    )
  )
)

# Server
server <- function(input, output, session) {
  
  # Fetch data from API with error handling
  get_data <- reactive({
    response <- GET(api_url)
    
    if (http_type(response) != "application/json") {
      return(data.frame())  # Return empty if API is down
    }

    data <- tryCatch({
      fromJSON(rawToChar(response$content))$data
    }, error = function(e) {
      return(NULL)  
    })

    if (is.null(data) || length(data) == 0) {
      return(data.frame(AgeGroup=character(), Count=numeric(), DoseCount=numeric(),
                        Jurisdiction=character(), OccurrenceYear=numeric(), 
                        ReferenceDate=character(), Sex=character()))
    }
    
    df <- as.data.frame(data)
    df$OccurrenceYear <- as.numeric(df$OccurrenceYear)
    return(df)
  })
  
  # Reactive data filtering
  filtered_data <- reactive({
    df <- get_data()
    if (nrow(df) == 0) return(df)

    if (input$jurisdiction != "All") {
      df <- df %>% filter(Jurisdiction == input$jurisdiction)
    }
    if (input$ageGroup != "All") {
      df <- df %>% filter(AgeGroup == input$ageGroup)
    }
    if (input$sex != "All") {
      df <- df %>% filter(Sex == input$sex)
    }
    if (input$year != "All") {
      df <- df %>% filter(OccurrenceYear == as.numeric(input$year))
    }
    if (input$dose != "All") {
      df <- df %>% filter(DoseCount == as.numeric(input$dose))
    }
    
    return(df)
  })

  # Dose Count Distribution
  output$dose_distribution <- renderPlot({
    df <- filtered_data()
    if (nrow(df) == 0) return()  # Prevent errors when no data

    ggplot(df, aes(x = DoseCount)) +
      geom_histogram(binwidth = 1, fill = "blue", color = "white", alpha = 0.7) +
      theme_minimal() +
      labs(title = "Dose Count Distribution", x = "Dose Count", y = "Frequency")
  })

  # Vaccination Coverage Trends (2 & 7-year-olds)
  output$coverage_trends <- renderPlot({
    df <- filtered_data()
    if (nrow(df) == 0) return()

    df_summary <- df %>%
      group_by(OccurrenceYear, AgeGroup) %>%
      summarize(coverage = sum(DoseCount) / sum(Count) * 100, .groups = "drop")

    ggplot(df_summary, aes(x = OccurrenceYear, y = coverage, color = AgeGroup)) +
      geom_line(size = 1.2) +
      geom_point(size = 2) +
      theme_minimal() +
      labs(title = "Vaccination Coverage Trends (2 & 7-year-olds)", x = "Year", y = "Coverage (%)")
  })

  # Data Table
  output$dataTable <- renderDT({
    df <- filtered_data()
    if (nrow(df) == 0) return(DT::datatable(data.frame(Message = "No data available")))

    datatable(df, options = list(pageLength = 10))
  })
}

# Run App
shinyApp(ui, server)
