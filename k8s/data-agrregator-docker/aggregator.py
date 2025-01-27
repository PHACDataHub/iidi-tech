import requests
import pandas as pd
from flask import Flask, jsonify
from datetime import datetime
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Flask app initialization
app = Flask(__name__)

# Environment variables
FHIR_URL = os.getenv("FHIR_URL", "http://localhost:8080/fhir")
AGGREGATION_INTERVAL = int(os.getenv("AGGREGATION_INTERVAL", 60))  # Default to 60 seconds if not provided

# Cache variables for aggregation
cached_data = None
last_aggregation_time = None

# Patient cache for performance optimization
patient_cache = {}


def fetch_fhir_resources(resource_type):
    """Fetch resources of the specified type from the FHIR server."""
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
        age = (datetime.now() - datetime.strptime(birth_date, "%Y-%m-%d")).days // 365
        if age < 2:
            return "0-2 years"
        elif age < 5:
            return "3-5 years"
        elif age < 18:
            return "6-17 years"
        else:
            return "18+ years"
    except ValueError as e:
        logging.error(f"Invalid birthDate format: {birth_date} - {e}")
        return "Unknown"


def process_immunization_record(immunization):
    """Process a single Immunization record and return data for aggregation."""
    try:
        patient_ref = immunization["patient"]["reference"]
        patient = fetch_patient_data(patient_ref)
        if not patient:
            return None

        return {
            "ReferenceDate": immunization["occurrenceDateTime"].split("T")[0],
            "Jurisdiction": "BC" if "bc" in FHIR_URL else "ON",
            "Sex": patient.get("gender", "Unknown").capitalize(),
            "AgeGroup": calculate_age_group(patient.get("birthDate", "Unknown")),
            "DoseCount": 1,  # Each Immunization record represents one dose
        }
    except KeyError as e:
        logging.error(f"Missing required field in Immunization record: {e}")
        return None


def aggregate_data():
    """Fetch and aggregate data from the FHIR server."""
    # Fetch Immunization resources
    logging.info("Fetching Immunization resources...")
    immunizations = fetch_fhir_resources("Immunization")
    if not immunizations:
        logging.warning("No Immunization records found.")
        return []

    # Process immunization records
    records = []
    for entry in immunizations:
        immunization = entry.get("resource", {})
        processed_record = process_immunization_record(immunization)
        if processed_record:
            records.append(processed_record)

    if not records:
        logging.warning("No valid records processed.")
        return []

    # Convert to DataFrame for aggregation
    df = pd.DataFrame(records)

    # Perform aggregation
    aggregated = df.groupby(
        ["ReferenceDate", "Jurisdiction", "Sex", "AgeGroup"]
    ).size().reset_index(name="DoseCount")

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
    aggregated_data = aggregate_data()
    cached_data = aggregated_data
    last_aggregation_time = current_time

    return jsonify(aggregated_data)

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
