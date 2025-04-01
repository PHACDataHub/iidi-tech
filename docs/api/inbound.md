# Inbound PT-to-PT Transfer API

This service represents a sample implementation of how provinces could receive and process immunization records from other jurisdictions. While in a production environment this would be deployed within each province's own infrastructure, this reference implementation demonstrates the technical approach for securely receiving, validating, and storing patient immunization data when patients move between provinces.

The **Inbound PT-to-PT Transfer API** is an **Express-based service** designed to receive and process FHIR bundles containing patient immunization records from other provincial/territorial jurisdictions. This service validates incoming bundles against FHIR specifications and business rules before storing them in the local FHIR server.

---

## **Environment Variables**

The API can be configured using the following environment variables:

| Variable           | Description                                        | Default              |
| ------------------ | -------------------------------------------------- | -------------------- |
| `EXPRESS_PORT`     | Port on which the Express server will listen       | `3000`               |
| `EXPRESS_HOST`     | Host address on which the Express server will bind | `0.0.0.0`            |
| `FHIR_URL`         | URL of the FHIR server to store patient bundles    | Required, no default |
| `DEV_IS_LOCAL_ENV` | Flag to indicate local development environment     | `false`              |
| `DEV_IS_TEST_ENV`  | Flag to indicate test environment                  | `false`              |

---

## **API Endpoints**

### **1️⃣ Health Check**

#### **GET `/healthcheck`**

This endpoint checks if the service and its dependencies (FHIR server) are operational.

##### **Response Codes**:

- **200 OK**: Service and FHIR server are operational
- **503 Service Unavailable**: FHIR server is not responding or not operational

##### **Response Format**:

Empty response body with appropriate status code.

### **2️⃣ Process Inbound Transfer**

#### **POST `/inbound-transfer`**

This endpoint receives a FHIR bundle containing patient immunization records, validates it, and stores it in the FHIR server.

##### **Request Body**:

- **`bundle`** (Object): A FHIR bundle containing patient and immunization resources.

##### **Response Format**:

- **201 Created**:

  ```json
  {
    "message": "Patient bundle accepted by FHIR server",
    "patient": {
      "id": "patient-123"
    }
  }
  ```

- **400 Bad Request**: If the bundle fails validation
- **500 Internal Server Error**: If there's an issue with the FHIR server

### **3️⃣ Dry Run Validation**

#### **GET `/inbound-transfer/dry-run`**

This endpoint validates a FHIR bundle without storing it in the FHIR server. Useful for testing and pre-validation.

##### **Request Body**:

- **`bundle`** (Object): A FHIR bundle containing patient and immunization resources.

##### **Response Format**:

- **200 OK**:

  ```json
  {
    "message": "Dry run successful, provided patient bundle would have been accepted by FHIR server"
  }
  ```

- **400 Bad Request**: If the bundle fails validation

---

## **Validation Rules**

The API performs several validation steps on incoming bundles:

1. **Basic Structure Validation**: Ensures the payload is a valid FHIR bundle
2. **Business Rules Validation**: Checks that the bundle follows project-specific business rules
3. **FHIR Specification Validation**: Validates the bundle against FHIR standards
4. **Transaction Preparation**: Converts the bundle to a transaction type before submission to FHIR server

---

## **Example Patient Resources**

The API expects FHIR Patient resources similar to:

```json
{
  "resourceType": "Patient",
  "id": "patient-1",
  "name": [
    {
      "family": "Doe",
      "given": ["John", "Michael"]
    }
  ],
  "gender": "male",
  "birthDate": "1990-06-15",
  "address": [
    {
      "line": ["1234 Main St"],
      "city": "Vancouver",
      "state": "BC",
      "postalCode": "V6B 3L1",
      "country": "CA"
    }
  ],
  "identifier": [
    {
      "system": "https://healthcare.example.org/ids",
      "value": "abcdef123456"
    },
    {
      "system": "https://healthcare.example.org/healthcard",
      "value": "1234567890"
    }
  ]
}
```
