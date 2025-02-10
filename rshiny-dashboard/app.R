library(shiny)
library(shinydashboard)
library(ggplot2)
library(dplyr)
library(httr)
library(jsonlite)
library(DT)
library(tidyr)
library(scales)

aggregator_url <- Sys.getenv(
  "AGGREGATOR_URL",
  "http://localhost:8080/on/aggregator/aggregated-data"
)

ui <- dashboardPage(
  dashboardHeader(title = "Immunization Coverage Analytics"),
  dashboardSidebar(
    sidebarMenu(
      menuItem("Overview", tabName = "overview", icon = icon("dashboard")),
      menuItem("Trends", tabName = "trends", icon = icon("chart-line")),
      menuItem("Data Explorer", tabName = "data", icon = icon("table")),
      selectInput(
        "jurisdiction",
        "Jurisdiction:",
        choices = c("All", "BC", "ON")
      ),
      selectInput(
        "ageGroup",
        "Age Group:",
        choices = c("All", "3-5 years", "6-17 years")
      ),
      selectInput(
        "sex", 
        "Sex:",
        choices = c("All", "Female", "Male", "Other")
      )
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
          box(
            title = "Immunization Distribution by Sex",
            plotOutput("sexDistribution"),
            width = 6
          ),
          box(
            title = "Dose Count by Jurisdiction",
            plotOutput("jurisdictionDoses"),
            width = 6
          )
        )
      ),
      tabItem(
        tabName = "trends",
        fluidRow(
          box(
            title = "Temporal Trends",
            plotOutput("timeTrend"),
            width = 12
          ),
          box(
            title = "Age Group Analysis",
            plotOutput("ageAnalysis"),
            width = 12
          )
        )
      ),
      tabItem(
        tabName = "data",
        fluidRow(
          box(
            title = "Raw Data",
            DTOutput("dataTable"),
            width = 12
          )
        )
      )
    )
  )
)

server <- function(input, output, session) {
  custom_theme <- theme_minimal() +
    theme(
      text = element_text(size = 12),
      axis.text = element_text(size = 10),
      axis.title = element_text(size = 12, face = "bold"),
      legend.text = element_text(size = 10),
      legend.title = element_text(size = 12, face = "bold"),
      plot.title = element_text(size = 14, face = "bold")
    )

  get_data <- reactive({
    response <- GET(aggregator_url)
    data <- fromJSON(rawToChar(response$content))$data
    df <- as.data.frame(data)
    df$OccurrenceYear <- as.numeric(df$OccurrenceYear)
    return(df)
  })

  filtered_data <- reactive({
    df <- get_data()
    if (input$jurisdiction != "All") {
      df <- df %>% filter(.data$Jurisdiction == input$jurisdiction)
    }
    if (input$ageGroup != "All") {
      df <- df %>% filter(.data$AgeGroup == input$ageGroup)
    }
    if (input$sex != "All") {
      df <- df %>% filter(.data$Sex == input$sex)
    }
    return(df)
  })

  output$totalImmunizations <- renderValueBox({
    valueBox(
      sum(filtered_data()$Count),
      "Total Immunizations",
      icon = icon("syringe"),
      color = "blue"
    )
  })

  output$avgDoseCount <- renderValueBox({
    valueBox(
      round(mean(filtered_data()$DoseCount), 1),
      "Average Doses",
      icon = icon("calculator"),
      color = "green"
    )
  })

  output$currentYear <- renderValueBox({
    valueBox(
      max(filtered_data()$OccurrenceYear),
      "Latest Year",
      icon = icon("calendar"),
      color = "purple"
    )
  })

  output$timeTrend <- renderPlot({
    filtered_data() %>%
      group_by(.data$OccurrenceYear, .data$Jurisdiction) %>%
      summarise(
        TotalCount = sum(.data$Count), 
        .groups = "drop"
      ) %>%
      ggplot(aes(
        x = .data$OccurrenceYear, 
        y = .data$TotalCount, 
        color = .data$Jurisdiction
      )) +
      geom_line(size = 1) +
      geom_point() +
      custom_theme +
      labs(
        title = "Immunization Trends Over Time",
        x = "Year",
        y = "Total Immunizations"
      ) +
      scale_y_continuous(labels = comma)
  })

  output$sexDistribution <- renderPlot({
    filtered_data() %>%
      group_by(.data$Sex) %>%
      summarise(
        TotalCount = sum(.data$Count),
        .groups = "drop"
      ) %>%
      ggplot(aes(
        x = .data$Sex, 
        y = .data$TotalCount, 
        fill = .data$Sex
      )) +
      geom_bar(
               stat = "identity",
               width = 0.4) +
      custom_theme +
      labs(
        title = "Distribution by Sex",
        x = "Sex",
        y = "Total Count"
      )
  })

  output$jurisdictionDoses <- renderPlot({
    filtered_data() %>%
      group_by(.data$Jurisdiction) %>%
      summarise(
        AvgDoses = mean(.data$DoseCount), 
        .groups = "drop"
      ) %>%
      ggplot(aes(
        x = .data$Jurisdiction, 
        y = .data$AvgDoses, 
        fill = .data$Jurisdiction
      )) +
      geom_bar(
               stat = "identity",
               width = 0.15) +
      custom_theme +
      labs(
        title = "Average Doses by Jurisdiction",
        x = "Jurisdiction",
        y = "Average Doses"
      )
  })

  output$ageAnalysis <- renderPlot({
    filtered_data() %>%
      group_by(.data$AgeGroup, .data$OccurrenceYear) %>%
      summarise(
        TotalCount = sum(.data$Count), 
        .groups = "drop"
      ) %>%
      ggplot(aes(
        x = .data$OccurrenceYear, 
        y = .data$TotalCount, 
        color = .data$AgeGroup
      )) +
      geom_line(size = 1) +
      custom_theme +
      labs(
        title = "Age Group Trends Over Time",
        x = "Year",
        y = "Total Count"
      )
  })

  output$dataTable <- renderDT({
    datatable(
      filtered_data(),
      options = list(pageLength = 10),
      filter = "top"
    )
  })
}

shinyApp(ui = ui, server = server)
