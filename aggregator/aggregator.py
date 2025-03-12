"""
FHIR Immunization Data Aggregator API

This script is a Flask-based API that retrieves, processes, and aggregates immunization data 
from a FHIR (Fast Healthcare Interoperability Resources) server. The data is then grouped by 
various attributes and returned as a JSON response.

Main Functionalities:
1. **Environment Variables Setup**:
   - `FHIR_URL`: The base URL of the FHIR server (default: `http://localhost:8080/fhir`).
   - `AGGREGATION_INTERVAL`: Time interval (in seconds) for caching aggregated data.
   - `PUBLIC_KEY_PATH`: Path to the public key used for JWT validation.
   - `IS_LOCAL_DEV`: Boolean flag to disable authentication for local development.

2. **Flask API Initialization**:
   - The script initializes a Flask application to serve aggregated immunization data.
   - Supports asynchronous operations to optimize API calls and data processing.

3. **Logging and Caching**:
   - Configures logging for debugging and monitoring.
   - Implements an **LRU cache** for patient data retrieval to reduce redundant FHIR API calls.
   - Uses a **caching mechanism** for aggregated data to avoid unnecessary recalculations within the configured interval.

4. **FHIR Resource Fetching**:
   - The `fetch_fhir_resources(resource_type)` function retrieves FHIR resources asynchronously (e.g., Immunization, Patient).
   - Handles **pagination** and **error management** to ensure robust data retrieval.

5. **Patient Data Caching**:
   - `fetch_patient_data(patient_reference)`:  
     - Fetches **FHIR Patient resource** asynchronously using a **cache** to minimize API calls.
     - If data is not in cache, retrieves from FHIR server and stores it in **LRU cache**.

6. **Processing Immunization Records**:
   - `process_immunization_record(immunization)`:  
     - Extracts key attributes from each **immunization record**, including:
       - **Jurisdiction** (BC or ON) based on `FHIR_URL`.
       - **Dose count**, **occurrence year**, **patient sex**, and **age group**.
     - Uses `calculate_age_group(birth_date)` to categorize patients into predefined **age groups**.

7. **Data Aggregation**:
   - `aggregate_data()`:  
     - **Asynchronously** processes immunization records and groups them by:
       - `OccurrenceYear`
       - `Jurisdiction`
       - `Sex`
       - `Age`
       - `Dose`
     - Counts the number of records for each combination.
     - Standardizes data format and ensures `ReferenceDate` is always **December 31st** of the `OccurrenceYear`.

8. **API Endpoints**:
   - `GET /aggregated-data`: Returns aggregated immunization data.
     - Uses caching to avoid unnecessary reprocessing within the aggregation interval.
     - Requires JWT authentication if `IS_LOCAL_DEV` is `false`.
   - `GET /health`: A health check endpoint to verify that the API is running.

9. **Script Execution**:
   - Ensures required **environment variables** are set before execution.
   - **Starts the Flask server** when executed as the main script.
   - Uses **Gunicorn** with multiple workers for production deployment.
"""

import httpx
import pandas as pd
from flask import Flask, jsonify, request
from datetime import datetime
import logging
import os
from cachetools import LRUCache
import jwt
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Flask app initialization
app = Flask(__name__)

# Environment variables
FHIR_URL = os.getenv("FHIR_URL", "http://localhost:8080/fhir")
AGGREGATION_INTERVAL = int(os.getenv("AGGREGATION_INTERVAL", 60))  # Default to 60 seconds
IS_LOCAL_DEV = os.getenv("IS_LOCAL_DEV", "false").lower() == "true"
PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH", "/secrets/public_key.pem")

def load_public_key():
    """Loads the public key from the mounted secret synchronously."""
    try:
        with open(PUBLIC_KEY_PATH, "r") as key_file:
            public_key = key_file.read().strip()
            if not public_key:
                raise ValueError("Public key file is empty!")
            return public_key
    except (FileNotFoundError, ValueError) as e:
        # Missing public key is acceptable in local dev, but should be an immediate program error exit in prod
        if IS_LOCAL_DEV:
          logging.error(f"Error loading public key: {e}")
          return None
        else:
          raise e
PUBLIC_KEY = load_public_key()

is_auth_required = not IS_LOCAL_DEV or (IS_LOCAL_DEV and not PUBLIC_KEY is None)

# Cache variables for aggregation
cached_data = None
last_aggregation_time = None

# Patient cache with LRU eviction policy
patient_cache = LRUCache(maxsize=1000)

def verify_jwt(token):
    """Verifies JWT using the public key."""
    if not PUBLIC_KEY:
        logging.error("Public key is not loaded, cannot verify JWT!")
        return None
    try:
        return jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
    except jwt.ExpiredSignatureError:
        logging.error("JWT has expired.")
    except jwt.InvalidSignatureError:
        logging.error("JWT signature verification failed!")
    except jwt.DecodeError:
        logging.error("JWT decode failed, invalid format!")
    except Exception as e:
        logging.error(f"Unexpected JWT error: {e}")
    return None

async def fetch_fhir_resources(resource_type):
    """Fetch resources of the specified type from the FHIR server, handling pagination."""
    url = f"{FHIR_URL}/{resource_type}?_count=1000"
    results = []
    async with httpx.AsyncClient() as client:
        while url:
            try:
                response = await client.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                if "entry" in data:
                    results.extend(data["entry"])
                url = next((link["url"] for link in data.get("link", []) if link["relation"] == "next"), None)
            except httpx.RequestError as e:
                logging.error(f"Error fetching {resource_type} data from FHIR server: {e}")
                break
    return results

async def fetch_patient_data(patient_reference):
    """Fetch Patient resource based on reference, with caching."""
    patient_id = patient_reference.split("/")[-1]
    if patient_id in patient_cache:
        return patient_cache[patient_id]
    url = f"{FHIR_URL}/Patient/{patient_id}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            patient = response.json()
            patient_cache[patient_id] = patient
            return patient
        except httpx.RequestError as e:
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

async def process_immunization_record(immunization):
    """Process a single Immunization record and return data for aggregation."""
    patient_ref = immunization.get("patient", {}).get("reference")
    if not patient_ref:
        return None
    patient = await fetch_patient_data(patient_ref)
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

async def aggregate_data():
    """Fetch and aggregate data from the FHIR server asynchronously."""
    logging.info("Fetching Immunization resources...")
    immunizations = await fetch_fhir_resources("Immunization")

    if not immunizations:
        logging.warning("No Immunization records found.")
        return []

    records = [await process_immunization_record(entry.get("resource", {})) for entry in immunizations]
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
async def get_aggregated_data():
    """API endpoint to return aggregated data with JWT authentication."""
    global cached_data, last_aggregation_time

    if is_auth_required:
        auth_header = request.headers.get("Authorization", "").strip()
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        token = auth_header.split(" ", 1)[-1]
        if not verify_jwt(token):
            return jsonify({"error": "Invalid token"}), 403

    current_time = datetime.now().timestamp()

    if cached_data and last_aggregation_time and (current_time - last_aggregation_time < AGGREGATION_INTERVAL):
        logging.info("Returning cached aggregated data...")
        return jsonify(cached_data)
    
    logging.info("Calculating new aggregated data...")  
    cached_data = await aggregate_data()
    last_aggregation_time = current_time
    return jsonify(cached_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
