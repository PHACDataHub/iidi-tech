import random
from datetime import datetime, timedelta
import requests
import json
from faker import Faker
import logging
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize Faker
faker = Faker("en_CA")

# FHIR server URL
FHIR_URL = os.getenv("FHIR_URL", "http://localhost:8080/fhir")
NUM_RECORDS = int(os.getenv("NUM_RECORDS", "1"))
PT = os.getenv("PT", "bc").lower()

# Function to generate a random date
def random_date(start_date, end_date):
    delta = end_date - start_date
    return (start_date + timedelta(days=random.randint(0, delta.days))).strftime("%Y-%m-%d")

# Enhanced Script for Synthetic MMR Immunization Records

def create_patient_resource(patient_id):
    ethnicity = random.choice(["Caucasian", "Asian", "Indigenous", "African", "Hispanic", "Mixed"])
    language = random.choice(["English", "French", "Mandarin", "Punjabi", "Spanish", "Arabic"])
    return {
        "resourceType": "Patient",
        "id": patient_id,
        "name": [{"family": faker.last_name(), "given": [faker.first_name(), faker.first_name()]}],
        "gender": random.choice(["male", "female", "other"]),
        "birthDate": random_date(datetime(2010, 1, 1), datetime(2020, 12, 31)),
        "address": [
            {
                "line": [faker.street_address()],
                "city": faker.city(),
                "state": "BC" if PT == "bc" else "ON",
                "postalCode": faker.postalcode(),
                "country": "CA"
            }
        ],
        "identifier": [
            {"system": "http://healthcare.example.org/ids", "value": faker.uuid4()}
        ],
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-consent",
                "valueCode": random.choice(["accepted", "declined", "undecided"])
            },
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-ethnicity",
                "valueString": ethnicity
            },
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-language",
                "valueString": language
            }
        ]
    }

def create_allergy_resource(patient_id):
    if PT == "on":
        return None
    return {
        "resourceType": "AllergyIntolerance",
        "patient": {"reference": f"Patient/{patient_id}"},
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": random.choice(["91935009", "91934004", "62014003", "226060000"]),
                    "display": random.choice([
                        "Allergy to egg protein",
                        "Allergy to gelatin",
                        "Allergy to penicillin",
                        "Allergy to latex"
                    ])
                }
            ]
        },
        "criticality": random.choice(["low", "high", "unable-to-assess"]),
        "type": random.choice(["allergy", "intolerance"]),
        "note": [{"text": faker.paragraph()}],
        "onsetDateTime": random_date(datetime(2015, 1, 1), datetime(2023, 12, 31))
    }

def create_immunization_resource(patient_id):
    manufacturer = random.choice(["Pfizer", "Moderna", "AstraZeneca"])
    lot_number = faker.uuid4()[:8].upper()
    site = random.choice(["Left Arm", "Right Arm", "Left Thigh", "Right Thigh"])
    return {
        "resourceType": "Immunization",
        "patient": {"reference": f"Patient/{patient_id}"},
        "vaccineCode": {
            "coding": [
                {"system": "http://hl7.org/fhir/sid/cvx", "code": "03", "display": "MMR"}
            ]
        },
        "occurrenceDateTime": random_date(datetime(2021, 1, 1), datetime(2023, 12, 31)),
        "manufacturer": {"display": manufacturer},
        "lotNumber": lot_number,
        "site": {"coding": [{"display": site}]},
        "protocolApplied": [
            {"doseNumberString": str(random.randint(1, 2)), "series": "MMR Vaccination"}
        ],
        "status": "completed",
        "reaction": [
            {
                "detail": {
                    "display": random.choice(["Fever", "Rash", "Nausea"])
                },
                "date": random_date(datetime(2021, 1, 1), datetime(2023, 12, 31))
            }
        ] if random.choice([True, False]) else None,
        "extension": [] if PT == "on" else [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/immunization-exemption",
                "valueCodeableConcept": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                            "code": random.choice(["RELIG", "MED", "PHIL"]),
                            "display": random.choice([
                                "Religious objection",
                                "Medical contraindication",
                                "Philosophical objection"
                            ])
                        }
                    ],
                    "text": faker.sentence()
                }
            }
        ]
    }

# Create a transaction bundle
def create_transaction_bundle(records):
    entries = []
    for record in records:
        entries.append({"resource": record["Patient"], "request": {"method": "POST", "url": "Patient"}})
        if record["Allergy"]:
            entries.append({"resource": record["Allergy"], "request": {"method": "POST", "url": "AllergyIntolerance"}})
        entries.append({"resource": record["Immunization"], "request": {"method": "POST", "url": "Immunization"}})
    return {"resourceType": "Bundle", "type": "transaction", "entry": entries}

# Generate synthetic records
def generate_synthetic_records(num_records):
    records = []
    for i in range(num_records):
        patient_id = f"patient-{i+1}"
        patient = create_patient_resource(patient_id)
        allergy = create_allergy_resource(patient_id)
        immunization = create_immunization_resource(patient_id)
        records.append({"Patient": patient, "Allergy": allergy, "Immunization": immunization})
    return records

# Upload bundle to FHIR server using a persistent session
def upload_to_fhir_server(bundle):
    headers = {"Content-Type": "application/json"}
    max_retries = 3

    # Use a persistent session for efficient connection reuse
    with requests.Session() as session:
        session.headers.update(headers)  # Set common headers

        # Retry logic with exponential backoff
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=2,  # Wait 1s, 2s, 4s on retries
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        try:
            logging.info("Uploading the bundle to the FHIR server...")
            response = session.post(FHIR_URL, json=bundle, timeout=(5, 30))  # Add timeouts
            if response.status_code in (200, 201):
                logging.info(f"Successfully uploaded the bundle to the FHIR server. Response: {response.status_code}")
                logging.info(f"Response Content: {response.text}")
            else:
                logging.error(f"Failed to upload bundle: {response.status_code}")
                logging.error(f"Response Content: {response.text}")
        except requests.RequestException as e:
            logging.error(f"Error uploading to FHIR server: {e}")

# Main execution remains unchanged
if __name__ == "__main__":
    logging.info(f"Generating {NUM_RECORDS} synthetic MMR immunization records...")
    synthetic_records = generate_synthetic_records(NUM_RECORDS)
    transaction_bundle = create_transaction_bundle(synthetic_records)
    logging.info("Uploading records to FHIR server...")
    upload_to_fhir_server(transaction_bundle)