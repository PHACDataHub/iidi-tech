# Use the official Python base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script into the container
COPY script.py /app/

# Set default environment variables (can be overridden)
ENV FHIR_URL=http://localhost:8080/fhir
ENV NUM_RECORDS=1
ENV PT=bc

# Specify the command to run the Python script
CMD ["python", "script.py"]
