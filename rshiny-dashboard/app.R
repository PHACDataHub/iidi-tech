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
  dashboardHeader(title = "Immunization Analytics"),
  dashboardSidebar(
    sidebarMenu(
      menuItem("Overview", tabName = "overview", icon = icon("dashboard")),
      menuItem("Trends", tabName = "trends", icon = icon("chart-line")),
      menuItem("Data Explorer", tabName = "data", icon = icon("table")),
      
      uiOutput("jurisdictionSelect"),
      uiOutput("ageSelect"),
      uiOutput("sexSelect"),
      uiOutput("yearSelect"),
      uiOutput("doseSelect")
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
          box(title = "Vaccination trend by age", plotOutput("coverage_trends"), width = 12)
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
    # Try GET up to 3 times with exponential backoff
    response <- tryCatch({
      RETRY(
        verb = "GET",
        url = api_url,
        times = 3,                 # max retries
        pause_base = 2,            # backoff: 2, 4, 8 sec
        pause_cap = 10,            # cap max wait between retries
        terminate_on = c(400, 401, 403, 404),  # don't retry on client errors
        timeout(60)                # allow slow API (up to 60s)
      )
    }, error = function(e) {
      message(":x: API request failed: ", e$message)
      return(NULL)
    })
    # Bail out if no response or wrong content-type
    if (is.null(response) || http_type(response) != "application/json") {
      message(":warning: Invalid or missing response from API")
      return(data.frame(Age = character(), Count = numeric(), Dose = numeric(),
                        Jurisdiction = character(), OccurrenceYear = numeric(),
                        ReferenceDate = character(), Sex = character()))
    }
    # Parse JSON safely
    data <- tryCatch({
      fromJSON(rawToChar(response$content))$data
    }, error = function(e) {
      message(":x: JSON parse failed: ", e$message)
      return(NULL)
    })
    # Return empty df if no data
    if (is.null(data) || length(data) == 0) {
      message(":warning: API returned empty dataset")
      return(data.frame())
    }
    # Convert to dataframe
    df <- as.data.frame(data)
    df$OccurrenceYear <- as.numeric(df$OccurrenceYear)
    return(df)
  })

  # Dynamic select inputs with validation
  output$jurisdictionSelect <- renderUI({
    df <- get_data()
    choices <- if (nrow(df) > 0) sort(unique(na.omit(df$Jurisdiction))) else character(0)
    selectInput("jurisdiction", "Select Jurisdiction", 
                choices = c("All", choices), selected = "All")
  })

  output$ageSelect <- renderUI({
    df <- get_data()
    if (nrow(df) == 0) return(selectInput("Age", "Select Age Group", choices = c("All")))

    ages <- unique(na.omit(df$Age))
    if (length(ages) > 0) {
      age_numbers <- as.numeric(gsub("\\D+", "", ages))
      ages <- ages[order(age_numbers)]
    }
    selectInput("Age", "Select Age Group", choices = c("All", ages), selected = "All")
  })
  
  output$sexSelect <- renderUI({
    df <- get_data()
    choices <- if (nrow(df) > 0) sort(unique(na.omit(df$Sex))) else character(0)
    selectInput("sex", "Select Sex", 
                choices = c("All", choices), selected = "All")
  })
  
  output$yearSelect <- renderUI({
    df <- get_data()
    choices <- if (nrow(df) > 0) sort(unique(na.omit(df$OccurrenceYear)), decreasing = TRUE) else character(0)
    selectInput("year", "Select Year",
                choices = c("All", as.character(choices)), selected = "All")
  })
  
  output$doseSelect <- renderUI({
    df <- get_data()
    choices <- if (nrow(df) > 0) sort(unique(na.omit(df$Dose))) else character(0)
    selectInput("dose", "Select Dose",
                choices = c("All", as.character(choices)), selected = "All")
  })

  # Reactive data filtering with error handling
  filtered_data <- reactive({
    df <- get_data()
    if (nrow(df) == 0) return(df)
    
    # Validate inputs exist before using them
    req(input$jurisdiction, input$Age, input$sex, input$year, input$dose)
    
    tryCatch({
      if (input$jurisdiction != "All") df <- df %>% filter(Jurisdiction == input$jurisdiction)
      if (input$Age != "All") df <- df %>% filter(Age == input$Age)
      if (input$sex != "All") df <- df %>% filter(Sex == input$sex)
      if (input$year != "All") df <- df %>% filter(OccurrenceYear == as.numeric(input$year))
      if (input$dose != "All") df <- df %>% filter(Dose == as.numeric(input$dose))
      df
    }, error = function(e) {
      df  # Return original df if any filter fails
    })
  })

  # Overview metrics with safe calculations
  output$totalImmunizations <- renderValueBox({
    df <- filtered_data()
    total <- if (nrow(df) > 0) sum(df$Count, na.rm = TRUE) else 0
    
    valueBox(
      value = format(total, big.mark = ","),
      subtitle = "Total Immunizations",
      icon = icon("syringe"),
      color = "green"
    )
  })

  output$avgDoseCount <- renderValueBox({
    df <- filtered_data()
    total_count <- sum(df$Count, na.rm = TRUE)
    avg <- if (nrow(df) > 0 && total_count > 0) {
      round(sum(df$Dose, na.rm = TRUE) / total_count * 100, 1)
    } else 0
    
    valueBox(
      value = paste0(avg, "%"),
      subtitle = "Average Dose",
      icon = icon("percent"),
      color = "blue"
    )
  })

output$dose_distribution <- renderPlot({
    df <- filtered_data()
    if (nrow(df) == 0) {
        plot.new()
        text(0.5, 0.5, "No data available for the selected filters.\nTry adjusting your selection criteria.", cex = 1.2)
        return()
    }
    
    ggplot(df, aes(x = Dose)) +
        geom_histogram(binwidth = 1, fill = "blue", color = "white", alpha = 0.7) +
        theme_minimal() +
        labs(title = "Dose Count Distribution", x = "Dose Count", y = "Frequency")
})

output$coverage_trends <- renderPlot({
    df <- filtered_data()
    if (nrow(df) == 0) {
        plot.new()
        text(0.5, 0.5, "No coverage trend data available for the selected filters.\nTry adjusting your selection criteria.", cex = 1.2)
        return()
    }
    
    df_summary <- df %>%
        group_by(OccurrenceYear, Age) %>%
        summarize(coverage = sum(Dose, na.rm = TRUE) / sum(Count, na.rm = TRUE) * 100,
                .groups = "drop")
    
    ggplot(df_summary, aes(x = OccurrenceYear, y = coverage, color = Age)) +
        geom_line(linewidth = 1.2) +
        geom_point(size = 2) +
        theme_minimal() +
        labs(title = "Vaccination trend by age", x = "Year", y = "Vaccinated (%)")
})


  # Data table with empty state handling
  output$dataTable <- renderDT({
    df <- filtered_data()
    if (nrow(df) == 0) return(DT::datatable(data.frame(Message = "No data available")))
    
    datatable(df, options = list(pageLength = 10, autoWidth = TRUE))
  })
}

# Run App
shinyApp(ui, server)