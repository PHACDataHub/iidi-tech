# Outbound PT-to-PT Transfer API

This service represents a sample implementation of how provinces could send immunization records to other jurisdictions when patients move. While in a production environment this would be deployed within each province's own infrastructure, this reference implementation demonstrates the technical approach for packaging and transferring patient immunization data to the destination province.

The **Outbound PT-to-PT Transfer API** is an **Express-based service** designed to process transfer requests, retrieve patient immunization records from the local FHIR server, and transmit them to the receiving province's inbound transfer service.

---

## **Environment Variables**

The API can be configured using the following environment variables:

| Variable                                     | Description                                                             | Default              |
| -------------------------------------------- | ----------------------------------------------------------------------- | -------------------- |
| `EXPRESS_PORT`                               | Port on which the Express server will listen                            | `3000`               |
| `EXPRESS_HOST`                               | Host address on which the Express server will bind                      | `0.0.0.0`            |
| `REDIS_PORT`                                 | Port for the Redis server used for job queuing                          | `6379`               |
| `REDIS_PASSWORD`                             | Password for Redis authentication                                       | Required, no default |
| `REDIS_HOST`                                 | Host address for the Redis server                                       | `0.0.0.0`            |
| `FHIR_URL`                                   | URL of the FHIR server to retrieve patient bundles                      | Required, no default |
| `OWN_TRANSFER_CODE`                          | Province/Territory code of this service (e.g., 'ON', 'BC')              | Required, no default |
| `INBOUND_TRANSFER_SERVICES_BY_TRANSFER_CODE` | JSON mapping of PT codes to their inbound transfer service URLs         | Required, no default |
| `TRANSFER_DASHBOARD_ORIGINS`                 | Comma-separated list of allowed CORS origins for the transfer dashboard | `*`                  |
| `DEV_IS_LOCAL_ENV`                           | Flag to indicate local development environment                          | `false`              |
| `DEV_IS_TEST_ENV`                            | Flag to indicate test environment                                       | `false`              |

---

## **API Endpoints**

### **1️⃣ Health Check**

#### **GET `/healthcheck`**

This endpoint checks if the service and its dependencies (FHIR server and Redis) are operational.

##### **Response Format**:

```json
{
  "is_fhir_active": true,
  "redisStatus": "CONNECTED"
}
```

##### **Response Codes**:

- **200 OK**: Service, FHIR server, and Redis are operational
- **503 Service Unavailable**: FHIR server or Redis is not responding or not operational

### **2️⃣ Create Transfer Request**

#### **POST `/transfer-request`**

This endpoint initiates a transfer request for a patient to another province.

##### **Request Body**:

```json
{
  "patient_id": "patient-123",
  "transfer_to": "BC"
}
```

- **`patient_id`** (String): ID of the patient to transfer
- **`transfer_to`** (String): Province/Territory code of the destination

##### **Response Format**:

```json
{
  "id": "job-456",
  "patient_id": "patient-123",
  "transfer_to": "BC",
  "status": "queued",
  "created_at": "2023-06-15T12:34:56Z"
}
```

##### **Response Codes**:

- **202 Accepted**: Transfer request has been accepted and queued
- **400 Bad Request**: Invalid patient ID or transfer code
- **404 Not Found**: Patient not found
- **500 Internal Server Error**: Error processing the request

### **3️⃣ Get All Transfer Requests**

#### **GET `/transfer-request`**

This endpoint retrieves a list of all transfer requests, with optional pagination.

##### **Query Parameters**:

- **`start`** (Number, optional): Starting index for pagination
- **`end`** (Number, optional): Ending index for pagination

##### **Response Format**:

```json
[
  {
    "id": "job-456",
    "patient_id": "patient-123",
    "transfer_to": "BC",
    "status": "completed",
    "created_at": "2023-06-15T12:34:56Z",
    "completed_at": "2023-06-15T12:35:30Z"
  },
  {
    "id": "job-457",
    "patient_id": "patient-124",
    "transfer_to": "ON",
    "status": "queued",
    "created_at": "2023-06-15T13:00:00Z"
  }
]
```

### **4️⃣ Get Transfer Request by ID**

#### **GET `/transfer-request/:transferRequestId`**

This endpoint retrieves details of a specific transfer request.

##### **Path Parameters**:

- **`transferRequestId`** (String): ID of the transfer request

##### **Response Format**:

```json
{
  "id": "job-456",
  "patient_id": "patient-123",
  "transfer_to": "BC",
  "status": "completed",
  "created_at": "2023-06-15T12:34:56Z",
  "completed_at": "2023-06-15T12:35:30Z"
}
```

##### **Response Codes**:

- **200 OK**: Transfer request found
- **404 Not Found**: Transfer request not found

### **5️⃣ Get Transfer Requests for a Patient**

#### **GET `/patient/:patientId/transfer-request`**

This endpoint retrieves all transfer requests for a specific patient.

##### **Path Parameters**:

- **`patientId`** (String): ID of the patient

##### **Query Parameters**:

- **`start`** (Number, optional): Starting index for pagination
- **`end`** (Number, optional): Ending index for pagination

##### **Response Format**:

```json
[
  {
    "id": "job-456",
    "patient_id": "patient-123",
    "transfer_to": "BC",
    "status": "completed",
    "created_at": "2023-06-15T12:34:56Z",
    "completed_at": "2023-06-15T12:35:30Z"
  },
  {
    "id": "job-458",
    "patient_id": "patient-123",
    "transfer_to": "ON",
    "status": "failed",
    "created_at": "2023-06-16T10:00:00Z",
    "failed_at": "2023-06-16T10:01:15Z",
    "error": "Connection timeout"
  }
]
```

### **6️⃣ Dry Run Transfer Request**

#### **GET `/transfer-request/dry-run`**

This endpoint validates that a patient can be transferred and returns the bundle that would be sent, without actually initiating a transfer.

##### **Request Body**:

```json
{
  "patient_id": "patient-123"
}
```

##### **Response Format**:

```json
{
  "bundle": {
    "resourceType": "Bundle",
    "type": "collection",
    "entry": [
      {
        "resource": {
          "resourceType": "Patient",
          "id": "patient-123",
          "name": [
            {
              "family": "Doe",
              "given": ["John"]
            }
          ]
          // Additional patient data
        }
      }
      // Additional resources (immunizations, etc.)
    ]
  }
}
```

##### **Response Codes**:

- **200 OK**: Patient can be transferred
- **400 Bad Request**: Invalid patient ID
- **404 Not Found**: Patient not found
- **500 Internal Server Error**: Error processing the request

---

## **Transfer Process and Job Stages**

The transfer process is implemented using BullMQ, a Redis-based queue system that ensures reliable processing of transfer requests. Each transfer job progresses through several stages:

1. **Initialization** (`initialized`): The transfer request is created and queued
2. **Collecting and Transferring** (`collecting_and_transfering`):
   - The patient's complete FHIR bundle is retrieved from the local FHIR server
   - The bundle is transmitted to the destination province's inbound transfer service
   - If successful, the new patient ID from the destination province is stored
3. **Setting Patient Post-Transfer Metadata** (`setting_patient_post_transfer_metadata`):
   - The original patient record is updated with a "replaced-by" link
   - This maintains data integrity and creates a reference to the new record
4. **Completion** (`completed`): All stages have been successfully completed
5. **Rejection** (`rejected`): The destination province rejected the transfer (e.g., invalid data)
6. **Failure** (`failed`): An error occurred during the transfer process

The system includes robust error handling:

- If a transfer fails after the bundle has been accepted by the destination province but before metadata is updated, the system will make additional attempts to complete the metadata update
- Exponential backoff is used for retries to avoid overwhelming the system
- Detailed logging tracks the progress of each job through its stages

---
