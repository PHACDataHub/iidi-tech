# Use an official Python runtime as a base image
FROM python:3.9 AS builder

# Set the working directory
WORKDIR /app

# Copy requirements.txt if available
COPY requirements.txt requirements.txt

# Install dependencies in a dedicated layer for caching
RUN pip install --no-cache-dir -r requirements.txt

# Use a lightweight image for the final container
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy dependencies from builder stage to reduce image size
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the app code into the image
COPY . .

# Add build-time arguments with default values
ARG FHIR_URL=http://localhost:8080/fhir
ARG AGGREGATION_INTERVAL=60
ARG PUBLIC_KEY_PATH=/secrets/public_key.pem
ARG IS_LOCAL_DEV=false

# Set environment variables for Flask and FHIR configuration
ENV FHIR_URL=$FHIR_URL
ENV AGGREGATION_INTERVAL=$AGGREGATION_INTERVAL
ENV PUBLIC_KEY_PATH=$PUBLIC_KEY_PATH
ENV IS_LOCAL_DEV=$IS_LOCAL_DEV

# Ensure the secrets directory exists
RUN mkdir -p /secrets

# Expose the Flask port
EXPOSE 5000

# Use Gunicorn to run the Flask app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "aggregator:app"]