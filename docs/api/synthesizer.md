# Synthetic FHIR Data Generator and Uploader

The **Synthetic FHIR Data Generator and Uploader** is a Python-based script designed to generate **synthetic immunization records** and upload them to a **FHIR server** as a **transaction bundle**. The script supports both **British Columbia (BC) and Ontario (ON)** jurisdictions and ensures realistic data generation with configurable parameters.

---

## **Dependencies**

This script relies on the following Python libraries:

| Dependency | Purpose                                  |
| ---------- | ---------------------------------------- |
| `requests` | For making API calls to the FHIR server. |
| `faker`    | For generating realistic patient data.   |
| `logging`  | For structured logging and debugging.    |
| `os`       | For handling environment variables.      |
| `random`   | For generating randomized values.        |
| `datetime` | For generating randomized dates.         |

---

## **Environment Variables**

The script behavior can be configured using the following environment variables:

| Variable      | Description                                           | Default                      |
| ------------- | ----------------------------------------------------- | ---------------------------- |
| `FHIR_URL`    | Base URL of the FHIR server.                          | `http://localhost:8080/fhir` |
| `NUM_RECORDS` | Number of synthetic immunization records to generate. | `1`                          |
| `PT`          | Province code (`bc` or `on`) for jurisdiction logic.  | `bc`                         |

---

## **Key Functions**

### **1️⃣ Generate a Random Date**

#### `random_date(start_date, end_date)`

Generates a random date within the given range.

---

### **2️⃣ Create a Patient Resource**

#### `create_patient_resource(patient_id)`

Generates a **FHIR-compliant Patient resource** with:

- Randomized demographic details (**name, gender, birthdate, address**).
- Unique identifiers (**health card number, UUID**).
- Additional metadata (**consent status, ethnicity, language, risk factors**).

---

### **3️⃣ Create an Allergy Resource** _(Only for BC Patients)_

#### `create_allergy_resource(patient_id)`

Generates an **AllergyIntolerance** resource with:

- Random **allergy type, criticality, and onset date**.
- **SNOMED-CT coding** for standardization.
- **FHIR-compliant allergy status and type**.

---

### **4️⃣ Create an Immunization Resource**

#### `create_immunization_resource(patient_id, birth_date)`

Generates an **Immunization resource** with:

- Vaccine **manufacturer, lot number, administration site**.
- Randomized **dose count (1 or 2 doses)**.
- **Occurrence date post first birthday**.
- Optional **reaction details (fever)**.
- Additional metadata (**exemption reasons, concurrent vaccines**).

---

### **5️⃣ Create a FHIR Transaction Bundle**

#### `create_transaction_bundle(records)`

Constructs a **FHIR-compliant transaction bundle** containing:

- **Patient**, **Immunization**, and **Allergy (if applicable)** resources.
- **Batch submission** format for efficient FHIR API ingestion.

---

### **6️⃣ Generate Synthetic Records**

#### `generate_synthetic_records(num_records)`

Generates a specified number of **synthetic patient and immunization records**.

---

### **7️⃣ Upload Data to FHIR Server**

#### `upload_to_fhir_server(bundle)`

Uploads the generated **FHIR transaction bundle** to the FHIR server.

- Implements **retry logic** for fault tolerance.
- Logs success or failure messages.

---

## **Execution Flow**

1️⃣ Generates `NUM_RECORDS` synthetic immunization records.
2️⃣ Creates a **FHIR transaction bundle**.
3️⃣ Uploads the bundle to the specified **FHIR server**.
4️⃣ Logs **success** or **failure** messages.

---

## **API Endpoint Interaction**

- The script **POSTs** data to the `FHIR_URL` via a **FHIR transaction bundle**.
- Implements **retries for API failures** to ensure data delivery.

---

## **Example FHIR Patient Resource (Generated)**

```json
{
  "resourceType": "Patient",
  "id": "patient-1",
  "name": [
    {
      "family": "Smith",
      "given": ["John", "Michael"]
    }
  ],
  "gender": "male",
  "birthDate": "2015-05-20",
  "address": [
    {
      "line": ["123 Fake Street"],
      "city": "Vancouver",
      "state": "BC",
      "postalCode": "V5K 0A1",
      "country": "CA"
    }
  ],
  "identifier": [
    { "system": "http://healthcare.example.org/ids", "value": "abcd-1234" },
    {
      "system": "http://healthcare.example.org/healthcard",
      "value": "9876543210"
    }
  ]
}
```

---

## **Deployment**

### **Run Locally**

Run the script with authentication disabled for local testing:

```bash
export IS_LOCAL_DEV=true
python synthetic_fhir_data.py
```
