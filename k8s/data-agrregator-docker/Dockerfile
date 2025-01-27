# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy requirements.txt if available
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code into the image
COPY . .

# Add build-time arguments with default values
ARG FHIR_URL=http://localhost:8080/fhir
ARG AGGREGATION_INTERVAL=60

# Set environment variables for Flask and FHIR configuration
ENV FHIR_URL=$FHIR_URL
ENV AGGREGATION_INTERVAL=$AGGREGATION_INTERVAL

# Expose the Flask port
EXPOSE 5000

# Use Gunicorn to run the Flask app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "aggregator:app"]