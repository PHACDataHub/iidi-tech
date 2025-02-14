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
                  choices = c("All", "Male", "Female", "Other"), selected = "All")
    )
  ),
  dashboardBody(
    tabItems(
      tabItem(
        tabName = "overview",
        fluidRow(
          valueBoxOutput("totalImmunizations", width = 4),
          valueBoxOutput("avgDoseCount", width = 4),
          valueBoxOutput("currentYear", width = 4)
        ),
        fluidRow(
          box(title = "Immunization Distribution by Sex", plotOutput("sexDistribution"), width = 6),
          box(title = "Dose Count by Jurisdiction", plotOutput("jurisdictionDoses"), width = 6)
        )
      ),
      tabItem(
        tabName = "trends",
        fluidRow(
          box(title = "Coverage Decline Rate per Year", plotOutput("decline_rate"), width = 12),
          box(title = "Ontario vs. BC Coverage Comparison", plotOutput("on_bc_comparison"), width = 12),
          box(title = "Sex-Based Coverage Trends", plotOutput("sex_trends"), width = 12),
          box(title = "Dose Count Distribution", plotOutput("dose_distribution"), width = 12),
          box(title = "Catch-up Rate Analysis", plotOutput("catchup_rate"), width = 12)
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
      return(data.frame())  # Return an empty data frame if API is unreachable
    }

    data <- tryCatch({
      fromJSON(rawToChar(response$content))$data
    }, error = function(e) {
      return(NULL)  # If parsing fails, return NULL
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
    if (nrow(df) == 0) return(df)  # Prevent filtering empty datasets

    if (!is.null(input$jurisdiction) && input$jurisdiction != "All") {
      df <- df %>% filter(Jurisdiction == input$jurisdiction)
    }
    if (!is.null(input$ageGroup) && input$ageGroup != "All") {
      df <- df %>% filter(AgeGroup == input$ageGroup)
    }
    if (!is.null(input$sex) && input$sex != "All") {
      df <- df %>% filter(Sex == input$sex)
    }
    
    return(df)
  })

  # Coverage Decline Rate per Year
  output$decline_rate <- renderPlot({
    df <- filtered_data()
    if (nrow(df) == 0) return()  # Prevent errors when no data

    df_summary <- df %>%
      group_by(OccurrenceYear) %>%
      summarize(decline = (max(DoseCount) - min(DoseCount)) / max(DoseCount) * 100, .groups = "drop")

    ggplot(df_summary, aes(x = OccurrenceYear, y = decline)) +
      geom_line(size = 1.2) +
      geom_point(size = 2) +
      theme_minimal() +
      labs(title = "Coverage Decline Rate per Year", x = "Year", y = "Percentage Decline (%)")
  })
  
  # Ontario vs. BC Coverage Comparison
  output$on_bc_comparison <- renderPlot({
    df <- filtered_data() %>% filter(Jurisdiction %in% c("ON", "BC"))
    if (nrow(df) == 0) return()  # Prevent errors when no data

    ggplot(df, aes(x = OccurrenceYear, y = DoseCount / Count * 100, fill = Jurisdiction)) +
      geom_bar(stat = "identity", position = "dodge") +
      theme_minimal() +
      labs(title = "Ontario vs. BC Coverage Comparison", x = "Year", y = "Percent Vaccinated (%)")
  })
  
  # Sex-Based Coverage Trends
  output$sex_trends <- renderPlot({
    df <- filtered_data()
    if (nrow(df) == 0) return()  # Prevent errors when no data

    ggplot(df, aes(x = OccurrenceYear, y = DoseCount / Count * 100, color = Sex)) +
      geom_line(size = 1.2) +
      geom_point(size = 2) +
      theme_minimal() +
      labs(title = "Sex-Based Coverage Trends", x = "Year", y = "Percent Vaccinated (%)")
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
  
  # Catch-up Rate Analysis
  output$catchup_rate <- renderPlot({
    df <- filtered_data()
    if (nrow(df) == 0) return()  # Prevent errors when no data

    df <- df %>%
      mutate(Delayed = ifelse(OccurrenceYear > min(OccurrenceYear), "Delayed", "On Time"))

    ggplot(df, aes(x = OccurrenceYear, fill = Delayed)) +
      geom_bar() +
      theme_minimal() +
      labs(title = "Catch-up Rate Analysis", x = "Year", y = "Count")
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
