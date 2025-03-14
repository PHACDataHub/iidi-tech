# Use an official Python runtime as a base image for dependency installation
FROM python:3.9 AS builder

# Set the working directory
WORKDIR /app

# Copy requirements.txt if available
COPY requirements.txt ./

# Install dependencies in a dedicated layer for caching
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Use a lightweight image for the final container
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy dependencies from builder stage to reduce image size
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code
COPY . .

# Ensure the secrets directory exists
RUN mkdir -p /secrets

# Set environment variables (Ensure correct expansion at runtime)
ARG FHIR_URL="http://localhost:8080/fhir"
ARG AGGREGATION_INTERVAL=60
ARG PUBLIC_KEY_PATH="/secrets/public_key.pem"
ARG IS_LOCAL_DEV=false

ENV FHIR_URL=$FHIR_URL \
    AGGREGATION_INTERVAL=$AGGREGATION_INTERVAL \
    PUBLIC_KEY_PATH=$PUBLIC_KEY_PATH \
    IS_LOCAL_DEV=$IS_LOCAL_DEV

# Expose the Flask port
EXPOSE 5000

# Default command for running the Flask app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "aggregator:app"]