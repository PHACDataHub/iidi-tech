"""
FHIR Immunization Data Aggregator API

This script is a Flask-based API that retrieves, processes, and aggregates immunization data 
from a FHIR (Fast Healthcare Interoperability Resources) server. The data is then grouped by 
various attributes and returned as a JSON response.

Main Functionalities:
1. **Environment Variables Setup**:
   - `FHIR_URL`: The base URL of the FHIR server (default: `http://localhost:8080/fhir`).
   - `AGGREGATION_INTERVAL`: Time interval (in seconds) for caching aggregated data.

2. **Flask API Initialization**:
   - The script initializes a Flask application to serve aggregated immunization data.

3. **Logging and Caching**:
   - Configures logging for debugging and monitoring.
   - Implements an LRU cache for patient data retrieval.
   - Uses a caching mechanism for aggregated data to optimize performance.

4. **FHIR Resource Fetching**:
   - The `fetch_fhir_resources(resource_type)` function retrieves FHIR resources (e.g., Immunization, Patient).
   - Handles pagination and error management.

5. **Patient Data Caching**:
   - `fetch_patient_data(patient_reference)` retrieves and caches patient information to minimize redundant API calls.

6. **Processing Immunization Records**:
   - `process_immunization_record(immunization)` extracts key attributes from each immunization record:
     - Determines jurisdiction (BC or ON) based on the FHIR URL.
     - Extracts dose count, occurrence year, patient sex, and age group.
     - Uses `calculate_age_group(birth_date)` to categorize patients into predefined age groups.

7. **Data Aggregation**:
   - `aggregate_data()` processes immunization records and groups them by:
     - `OccurrenceYear`
     - `Jurisdiction`
     - `Sex`
     - `Age`
     - `Dose`
   - Counts the number of records for each combination.
   - Standardizes data and ensures the `ReferenceDate` is always December 31st of the `OccurrenceYear`.

8. **API Endpoints**:
   - `GET /aggregated-data`: Returns aggregated immunization data.
     - Uses caching to avoid unnecessary reprocessing within the aggregation interval.
   - `GET /health`: A health check endpoint to verify that the API is running.

9. **Script Execution**:
   - Ensures required environment variables are set.
   - Starts the Flask server when executed as the main script.
"""

import requests
import pandas as pd
from flask import Flask, jsonify
from datetime import datetime
import logging
import os
from cachetools import LRUCache
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Flask app initialization
app = Flask(__name__)

# Environment variables
FHIR_URL = os.getenv("FHIR_URL", "http://localhost:8080/fhir")
AGGREGATION_INTERVAL = int(os.getenv("AGGREGATION_INTERVAL", 60))  # Default to 60 seconds

# Cache variables for aggregation
cached_data = None
last_aggregation_time = None

# Patient cache with LRU eviction policy
patient_cache = LRUCache(maxsize=1000)

def validate_environment_variables():
    """Ensure required environment variables are set."""
    if not FHIR_URL:
        raise ValueError("FHIR_URL environment variable is required!")

def fetch_fhir_resources(resource_type):
    """Fetch resources of the specified type from the FHIR server, handling pagination."""
    url = f"{FHIR_URL}/{resource_type}?_count=1000"
    results = []
    
    while url:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if "entry" in data:
                results.extend(data["entry"])
            url = next((link["url"] for link in data.get("link", []) if link["relation"] == "next"), None)
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching {resource_type} data from FHIR server: {e}")
            break
    
    return results

def fetch_patient_data(patient_reference):
    """Fetch Patient resource based on reference, with caching."""
    patient_id = patient_reference.split("/")[-1]
    if patient_id in patient_cache:
        return patient_cache[patient_id]

    url = f"{FHIR_URL}/Patient/{patient_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        patient = response.json()
        patient_cache[patient_id] = patient
        return patient
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching Patient data for {patient_id}: {e}")
        return None

def calculate_age_group(birth_date):
    """Calculate age group based on birthDate."""
    try:
        if not birth_date:
            return "Unknown"

        birth_date = datetime.strptime(birth_date, "%Y-%m-%d")
        today = datetime.now()

        if birth_date > today:
            return "Unknown"

        age = (today - birth_date).days // 365

        return "1 year" if age <= 1 else f"{age} years"

    except ValueError:
        return "Unknown"

def process_immunization_record(immunization):
    """Process a single Immunization record and return data for aggregation."""
    try:
        patient_ref = immunization.get("patient", {}).get("reference")
        if not patient_ref:
            return None

        patient = fetch_patient_data(patient_ref)
        if not patient:
            return None
        
        occurrence_date = immunization.get("occurrenceDateTime", "")
        birth_date = patient.get("birthDate", "")

        occurrence_year = occurrence_date[:4] if occurrence_date else "Unknown"

        return {
            "Jurisdiction": "BC" if "bc" in FHIR_URL.lower() else "ON",
            "OccurrenceYear": occurrence_year,
            "Sex": patient.get("gender", "Unknown").capitalize(),
            "Age": calculate_age_group(birth_date),
            "Dose": int(immunization.get("protocolApplied", [{}])[0].get("doseNumberString", 1)),  
        }
    except Exception as e:
        logging.error(f"Error processing immunization record: {e}")
        return None

def aggregate_data():
    """Fetch and aggregate data from the FHIR server."""
    logging.info("Fetching Immunization resources...")
    immunizations = fetch_fhir_resources("Immunization")
    
    if not immunizations:
        logging.warning("No Immunization records found.")
        return []

    records = [process_immunization_record(entry.get("resource", {})) for entry in immunizations]
    records = [r for r in records if r]
    
    if not records:
        logging.warning("No valid records processed.")
        return []
    
    df = pd.DataFrame(records)
    
    # Standardizing data
    df["OccurrenceYear"] = df["OccurrenceYear"].astype(str).str.strip()
    df["Sex"] = df["Sex"].str.capitalize()
    df["Age"] = df["Age"].str.strip()
    
    # Aggregating data
    aggregated = df.groupby([
        "OccurrenceYear", "Jurisdiction", "Sex", "Age", "Dose"
    ], as_index=False).agg(
        Count=("Dose", "count")
    )
    
    # Ensuring ReferenceDate is always 31st December of the OccurrenceYear
    aggregated["ReferenceDate"] = aggregated["OccurrenceYear"].apply(lambda year: f"{year}-12-31" if year.isnumeric() else "Unknown")
    return aggregated.to_dict(orient="records")

@app.route("/aggregated-data", methods=["GET"])
def get_aggregated_data():
    """API endpoint to return aggregated data."""
    global cached_data, last_aggregation_time

    current_time = datetime.now().timestamp()
    
    if cached_data and last_aggregation_time and (current_time - last_aggregation_time < AGGREGATION_INTERVAL):
        logging.info("Returning cached aggregated data...")
        return jsonify(cached_data)
    
    logging.info("Calculating new aggregated data...")
    cached_data = aggregate_data()
    last_aggregation_time = current_time

    return jsonify(cached_data)

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    validate_environment_variables()
    app.run(host="0.0.0.0", port=5000)
