library(shiny)
library(shinydashboard)
library(ggplot2)
library(dplyr)
library(httr)
library(jsonlite)
library(DT)
library(tidyr)
library(scales)

dta_url <- Sys.getenv("AGGREGATOR_URL", "http://federator:3000/aggregated-data")

population_data <- data.frame(
  Jurisdiction = c("ON", "BC"),
  Population_2Y = c(147340, 51477), 
  Population_7Y = c(147500, 51500) 
)

dashboard_ui <- dashboardPage(
  dashboardHeader(title = "STARVAX Vaccination Analytics"),
  dashboardSidebar(
    sidebarMenu(
      menuItem("Overview", tabName = "overview", icon = icon("dashboard")),
      menuItem("Trends", tabName = "trends", icon = icon("chart-line")),
      menuItem("Data Explorer", tabName = "data", icon = icon("table"))
    )
  ),
  dashboardBody(
    tabItems(
      tabItem(
        tabName = "trends",
        fluidRow(
          box(title = "DTaP & MMR Coverage (2-Year-Olds)", plotOutput("trend_2y"), width = 12),
          box(title = "DTaP & MMR Coverage (7-Year-Olds)", plotOutput("trend_7y"), width = 12)
        ),
        fluidRow(
          box(title = "Comparison by Jurisdiction", plotOutput("jurisdiction_comparison"), width = 12)
        )
      )
    )
  )
)

server_logic <- function(input, output, session) {
  get_data <- reactive({
    response <- GET(dta_url)
    data <- fromJSON(rawToChar(response$content))$data
    df <- as.data.frame(data)
    df$OccurrenceYear <- as.numeric(df$OccurrenceYear)
    
    df <- df %>% left_join(population_data, by = "Jurisdiction") %>%
      mutate(
        DTaP_2Y_Coverage = (DoseCount / Population_2Y) * 100,
        MMR_2Y_Coverage = (Count / Population_2Y) * 100,
        DTaP_7Y_Coverage = (DoseCount / Population_7Y) * 100,
        MMR_7Y_Coverage = (Count / Population_7Y) * 100
      )
    return(df)
  })

  output$trend_2y <- renderPlot({
    df <- get_data()
    
    ggplot(df, aes(x = OccurrenceYear)) +
      geom_line(aes(y = DTaP_2Y_Coverage, color = "DTaP (≥4 doses)"), size = 1) +
      geom_line(aes(y = MMR_2Y_Coverage, color = "MMR (≥1 dose)"), size = 1, linetype = "dashed") +
      scale_y_continuous(labels = scales::percent_format(scale = 1)) +
      labs(
        x = "Year",
        y = "Vaccination Coverage (%)",
        title = "Vaccination Trends for 2-Year-Olds"
      ) +
      theme_minimal() +
      theme(legend.title = element_blank())
  })

  output$trend_7y <- renderPlot({
    df <- get_data()
    
    ggplot(df, aes(x = OccurrenceYear)) +
      geom_line(aes(y = DTaP_7Y_Coverage, color = "DTaP (up-to-date)"), size = 1) +
      geom_line(aes(y = MMR_7Y_Coverage, color = "MMR (≥2 doses)"), size = 1, linetype = "dashed") +
      scale_y_continuous(labels = scales::percent_format(scale = 1)) +
      labs(
        x = "Year",
        y = "Vaccination Coverage (%)",
        title = "Vaccination Trends for 7-Year-Olds"
      ) +
      theme_minimal() +
      theme(legend.title = element_blank())
  })

  output$jurisdiction_comparison <- renderPlot({
    df <- get_data()
    
    ggplot(df, aes(x = OccurrenceYear)) +
      geom_line(aes(y = DTaP_2Y_Coverage, color = "DTaP (2Y) - ON"), size = 1) +
      geom_line(aes(y = DTaP_2Y_Coverage, color = "DTaP (2Y) - BC"), size = 1, linetype = "dotted") +
      geom_line(aes(y = MMR_2Y_Coverage, color = "MMR (2Y) - ON"), size = 1) +
      geom_line(aes(y = MMR_2Y_Coverage, color = "MMR (2Y) - BC"), size = 1, linetype = "dotted") +
      scale_y_continuous(labels = scales::percent_format(scale = 1)) +
      labs(
        x = "Year",
        y = "Vaccination Coverage (%)",
        title = "Vaccination Coverage Comparison by Jurisdiction"
      ) +
      theme_minimal() +
      theme(legend.title = element_blank())
  })
}

# Run App
shinyApp(ui = dashboard_ui, server = server_logic)
