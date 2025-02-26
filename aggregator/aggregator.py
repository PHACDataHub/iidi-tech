import requests
import pandas as pd
from flask import Flask, jsonify
from datetime import datetime
import logging
import os
from cachetools import LRUCache

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
        age = (datetime.now() - datetime.strptime(birth_date, "%Y-%m-%d")).days // 365
        if age < 2:
            return "0-2 years"
        elif age < 5:
            return "3-5 years"
        elif age < 18:
            return "6-17 years"
        else:
            return "18+ years"
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
        
        # Determine the jurisdiction from the FHIR URL
        jurisdiction = "BC" if "bc" in FHIR_URL.lower() else "ON"
        
        # Extract relevant data
        dose_number = 1  # Default dose number
        protocol_applied = immunization.get("protocolApplied", [])
        if protocol_applied:
            dose_number = int(protocol_applied[0].get("doseNumberString", 1))
        
        occurrence_date = immunization.get("occurrenceDateTime", "")
        birth_date = patient.get("birthDate", "")
        
        # Calculate the patient's age at the time of immunization
        if occurrence_date and birth_date:
            birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d")
            occurrence_date_obj = datetime.strptime(occurrence_date, "%Y-%m-%d")
            age_in_days = (occurrence_date_obj - birth_date_obj).days
            
            # Validate if the dose is given before the first birthday
            if age_in_days < 365:  # Before the first birthday
                if jurisdiction == "ON":
                    logging.info(f"Skipping dose for patient {patient_ref} given before first birthday in ON jurisdiction.")
                    return None  # Skip this record for ON
                else:
                    logging.info(f"Accepting early dose for patient {patient_ref} in BC jurisdiction.")

        occurrence_year = occurrence_date[:4] if len(occurrence_date) >= 4 else "Unknown"
        
        return {
            "OccurrenceYear": occurrence_year.strip(),
            "Jurisdiction": jurisdiction,
            "Sex": patient.get("gender", "Unknown").capitalize(),
            "AgeGroup": calculate_age_group(birth_date),
            "DoseCount": dose_number,
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
    df["AgeGroup"] = df["AgeGroup"].str.strip()
    
    # Aggregating data
    aggregated = df.groupby([
        "OccurrenceYear", "Jurisdiction", "Sex", "AgeGroup", "DoseCount"
    ], as_index=False).agg(
        Count=("DoseCount", "count")
    )
    
    # Ensuring ReferenceDate is always 31st December of the OccurrenceYear
    aggregated["ReferenceDate"] = aggregated["OccurrenceYear"].apply(lambda year: f"{year}-12-31")
    
    # Sorting the output for better readability
    aggregated = aggregated.sort_values(
        by=["OccurrenceYear", "AgeGroup", "Sex", "DoseCount"],
        ascending=[True, True, True, True]
    )
    
    return aggregated.to_dict(orient="records")

@app.route("/aggregated-data", methods=["GET"])
def get_aggregated_data():
    """API endpoint to return aggregated data."""
    global cached_data, last_aggregation_time

    reference_date = datetime.now()
    current_time = reference_date.timestamp()
    
    if cached_data and last_aggregation_time and (current_time - last_aggregation_time < AGGREGATION_INTERVAL):
        logging.info("Returning cached aggregated data...")
        return jsonify(cached_data)
    
    logging.info("Calculating new aggregated data...")
    aggregates_with_reference_date = list(map(
        lambda aggregate_record: {
            **aggregate_record,
            "ReferenceDate": reference_date.strftime('%Y-%m-%d')
        },
        aggregate_data()
    ))

    cached_data = aggregates_with_reference_date
    last_aggregation_time = current_time

    return jsonify(cached_data)

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    validate_environment_variables()
    app.run(host="0.0.0.0", port=5000)
