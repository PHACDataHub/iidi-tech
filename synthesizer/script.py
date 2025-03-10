"""
Synthetic FHIR Data Generator and Uploader

This script generates synthetic immunization records for testing purposes 
and uploads them to a FHIR server as a transaction bundle. It supports both 
British Columbia (BC) and Ontario (ON) jurisdictions, ensuring realistic 
data generation based on configurable parameters.

Dependencies:
- `requests`: For making API calls to the FHIR server.
- `faker`: For generating realistic patient data.
- `logging`: For logging execution details.
- `os`: For handling environment variables.
- `random`, `datetime`, `timedelta`: For generating randomized dates and values.

Environment Variables:
- `FHIR_URL`: Base URL of the FHIR server (default: "http://localhost:8080/fhir").
- `NUM_RECORDS`: Number of synthetic records to generate (default: 1).
- `PT`: Province code ("bc" or "on") to differentiate jurisdiction-specific logic.

Key Functions:
1. **random_date(start_date, end_date)**
   - Generates a random date within the given range.

2. **create_patient_resource(patient_id)**
   - Generates a Patient resource with:
     - Randomized demographic details (name, gender, birthdate, address).
     - Unique identifiers (health card number, UUID).
     - Additional metadata such as consent status, ethnicity, language.

3. **create_allergy_resource(patient_id)**
   - Generates an AllergyIntolerance resource (only for BC patients).
   - Assigns a random allergy type, criticality, and onset date.

4. **create_immunization_resource(patient_id, birth_date)**
   - Generates an Immunization resource with:
     - Vaccine manufacturer, lot number, and site of administration.
     - Randomized dose count (1 or 2).
     - Occurrence date post first birthday.
     - Optional reaction details (fever) and additional metadata.

5. **create_transaction_bundle(records)**
   - Constructs a FHIR transaction bundle containing:
     - Patient, Immunization, and Allergy (if applicable) resources.

6. **generate_synthetic_records(num_records)**
   - Generates the specified number of synthetic records.

7. **upload_to_fhir_server(bundle)**
   - Uploads the generated bundle to the FHIR server.
   - Implements request retries for fault tolerance.

Execution Flow:
1. Generates `NUM_RECORDS` synthetic immunization records.
2. Creates a FHIR transaction bundle.
3. Uploads the bundle to the specified FHIR server.
4. Logs success or failure messages.

This script is useful for testing FHIR-based immunization record systems 
and validating API ingestion pipelines.
"""

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

# FHIR server URL and parameters
FHIR_URL = os.getenv("FHIR_URL", "http://localhost:8080/fhir")
NUM_RECORDS = int(os.getenv("NUM_RECORDS", "1"))
PT = os.getenv("PT", "bc").lower()

# Generate a random date within a specified range
def random_date(start_date, end_date):
    delta = end_date - start_date
    return (start_date + timedelta(days=random.randint(0, delta.days))).strftime("%Y-%m-%d")

# Create a Patient resource
def create_patient_resource(patient_id):
    ethnicity = random.choice(["Caucasian", "Asian", "Indigenous", "African", "Hispanic", "Mixed"])
    language = random.choice(["English", "French", "Mandarin", "Punjabi", "Spanish", "Arabic"])
    gender = random.choice(["male", "female", "other"])
    risk_factor = random.choice(["healthcare_worker", "traveler", "military_personnel", None])
    pregnancy_status = random.choice(["pregnant", "postpartum", None]) if gender == "female" else None

    return {
        "resourceType": "Patient",
        "id": patient_id,
        "name": [{"family": faker.last_name(), "given": [faker.first_name(), faker.first_name()]}],
        "gender": gender,
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
            {"system": "http://healthcare.example.org/ids", "value": faker.uuid4()},
            {"system": "http://healthcare.example.org/healthcard", "value": faker.bothify("##########")}
        ],
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-consent",
                "valueCode": random.choice(["accepted", "declined", "undecided"])
            },
            {
                "url": "http://hl7.org/fhir/StructureDefinition/date-of-consent",
                "valueDate": random_date(datetime(2020, 1, 1), datetime(2023, 12, 31))
            },
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-ethnicity",
                "valueString": ethnicity
            },
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-language",
                "valueString": language
            },
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-risk-factor",
                "valueString": risk_factor
            },
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-pregnancy-status",
                "valueString": pregnancy_status
            }
        ]
    }

# Create an AllergyIntolerance resource
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
        "onsetDateTime": random_date(datetime(2015, 1, 1), datetime(2023, 12, 31)),
        # Since all provinces here are assumed to be FHIR compliant, ensure correct fields
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", 
                    "code": random.choice(["active", "inactive", "resolved"])
                }
            ]
        }
    }

# Create an Immunization resource
# Create an Immunization resource
def create_immunization_resource(patient_id, birth_date):
    manufacturer = random.choice(["Pfizer", "Moderna", "AstraZeneca"])
    lot_number = faker.uuid4()[:8].upper()
    site = random.choice(["Left Arm", "Right Arm", "Left Thigh", "Right Thigh"])
    
    # Ensure birth_date is a valid datetime object
    birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d")
    
    # Ensure occurrence_date is never in the future
    min_date = birth_date_obj + timedelta(days=365)
    max_date = datetime.today()
    occurrence_date = random_date(min_date, max_date)

    exemption_reason = random.choice([None, "RELIG", "MED", "PHILISOP"])
    exemption_display = {
        "RELIG": "Religious objection",
        "MED": "Medical contraindication",
        "PHILISOP": "Philosophical objection"
    }.get(exemption_reason, "")

    concurrent_vaccine = random.choice(["Influenza", "COVID-19", None])

    return {
        "resourceType": "Immunization",
        "patient": {"reference": f"Patient/{patient_id}"},
        "vaccineCode": {
            "coding": [
                {"system": "http://hl7.org/fhir/sid/cvx", "code": "03", "display": "MMR"}
            ]
        },
        "occurrenceDateTime": occurrence_date,
        "manufacturer": {"display": manufacturer},
        "lotNumber": lot_number,
        "site": {"coding": [{"display": site}]},
        "protocolApplied": [
            {"doseNumberString": str(random.randint(1, 2)), "series": "MMR Vaccination"}
        ],
        "status": "completed",
        # TODO: Modify reaction[*].detail. reaction[*].detail.coding doesn't exist in the Immunization resource.
        # Not saved by the FHIR server.
        "reaction": [
            {
                "detail": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "271807003",
                            "display": "Fever"
                        }
                    ]
                },
                "date": random_date(datetime(2021, 1, 1), datetime(2023, 12, 31))
            }
        ] if random.choice([True, False]) else None,
        "extension": [
            *([{
                "url": "http://hl7.org/fhir/StructureDefinition/immunization-exemption",
                "valueCodeableConcept": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                            "code": exemption_reason,
                            "display": exemption_display
                        }
                    ]
                }
            }] if exemption_reason else []),
            *([{
                "url": "http://hl7.org/fhir/StructureDefinition/immunization-concurrent-administration",
                "valueString": concurrent_vaccine
            }] if concurrent_vaccine else []),
            {
                "url": "http://hl7.org/fhir/StructureDefinition/immunization-expiry-date",
                "valueDate": random_date(datetime(2023, 1, 1), datetime(2025, 12, 31))
            },
            {
                "url": "http://hl7.org/fhir/StructureDefinition/immunization-reporting-source",
                "valueString": faker.company()
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
        immunization = create_immunization_resource(patient_id, patient["birthDate"])
        records.append({"Patient": patient, "Allergy": allergy, "Immunization": immunization})
    return records

# Upload the transaction bundle to the FHIR server
def upload_to_fhir_server(bundle):
    headers = {"Content-Type": "application/json"}
    max_retries = 3

    with requests.Session() as session:
        session.headers.update(headers)
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        try:
            logging.info("Uploading the bundle to the FHIR server...")
            response = session.post(FHIR_URL, json=bundle, timeout=(5, 30))
            if response.status_code in (200, 201):
                logging.info(f"Successfully uploaded the bundle. Response: {response.status_code}")
                logging.info(f"Response Content: {response.text}")
            else:
                logging.error(f"Failed to upload bundle: {response.status_code}")
                logging.error(f"Response Content: {response.text}")
                exit(1)
        except requests.RequestException as e:
            logging.error(f"Error uploading to FHIR server: {e}")
            exit(1)

# Main execution
if __name__ == "__main__":
    logging.info(f"Generating {NUM_RECORDS} synthetic MMR immunization records...")
    synthetic_records = generate_synthetic_records(NUM_RECORDS)
    transaction_bundle = create_transaction_bundle(synthetic_records)
    logging.info("Uploading records to FHIR server...")
    upload_to_fhir_server(transaction_bundle)