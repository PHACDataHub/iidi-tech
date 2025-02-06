library(shiny)
library(ggplot2)
library(httr)
library(jsonlite)
library(shinythemes)

aggregator_url <- Sys.getenv(
  "AGGREGATOR_URL",
  "http://localhost:8080/on/aggregator/aggregated-data"
)

ui <- fluidPage(
  theme = shinytheme("flatly"),
  
  # Header
  titlePanel(
    div(
      h1("Immunization Coverage Dashboard", 
         style = "color: #2C3E50; padding: 20px 0;
                  border-bottom: 2px solid #ECF0F1;")
    )
  ),
  
  # Main content
  mainPanel(
    width = 12,
    div(
      style = "padding: 20px;",
      fluidRow(
        column(
          width = 12,
          plotOutput("vaccinePlot", height = "600px")
        )
      ),
      fluidRow(
        column(
          width = 12,
          div(
            style = "color: #7F8C8D; font-size: 12px; text-align: right;",
            "Data source: IIDI Aggregator API"
          )
        )
      )
    )
  )
)

server <- function(input, output) {
  get_vaccine_data <- function() {
    response <- GET(aggregator_url)
    data <- fromJSON(rawToChar(response$content))
    return(as.data.frame(data))
  }
  
  output$vaccinePlot <- renderPlot({
    vaccine_data <- get_vaccine_data()
    
    ggplot(vaccine_data, aes(x = ReferenceDate, y = Count, fill = Sex)) +
      geom_bar(stat = "identity", position = "stack") +
      facet_wrap(~AgeGroup, scales = "free_y") +
      scale_fill_brewer(palette = "Set2") +
      labs(
        title = "Immunization Coverage Over Time",
        subtitle = "Breakdown by Age Group and Sex",
        x = "Reference Date",
        y = "Number of Immunizations",
        fill = "Sex"
      ) +
      theme_minimal() +
      theme(
        plot.title = element_text(size = 16, face = "bold"),
        plot.subtitle = element_text(size = 12),
        axis.text.x = element_text(angle = 45, hjust = 1),
        strip.text = element_text(size = 12, face = "bold"),
        panel.grid.minor = element_blank(),
        panel.spacing = unit(2, "lines")
      )
  })
}

shinyApp(ui = ui, server = server)
