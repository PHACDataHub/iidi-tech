# FHIR Immunization Data Aggregation API

The **FHIR Immunization Data Aggregation API** is a **Flask-based service** that retrieves, processes, and aggregates immunization data from a **FHIR server**. This API **groups immunization records by key attributes** such as:

- **Occurrence Year**
- **Jurisdiction (ON or BC)**
- **Sex**
- **Age Group**
- **Dose Count**

This API supports **real-time data analysis and reporting** for **public health monitoring**.

---

## **Environment Variables**

The API is configurable using the following environment variables:

| Variable               | Description                                                | Default                      |
| ---------------------- | ---------------------------------------------------------- | ---------------------------- |
| `FHIR_URL`             | Base URL of the FHIR server                                | `http://localhost:8080/fhir` |
| `AGGREGATION_INTERVAL` | Time in seconds to cache aggregated data                   | `60`                         |
| `PUBLIC_KEY_PATH`      | Path to the public key for JWT validation                  | `/secrets/public_key.pem`    |
| `IS_LOCAL_DEV`         | Set `true` to disable authentication in local environments | `false`                      |

---

## **API Endpoints**

### **1️⃣ Get Aggregated Immunization Data**

#### **GET `/aggregated-data`**

Retrieves **FHIR-based immunization records**, processes them, and returns **grouped** data.

#### **Request Headers**

| Header          | Description                         | Required                          |
| --------------- | ----------------------------------- | --------------------------------- |
| `Authorization` | Bearer token for JWT authentication | ✅ (unless `IS_LOCAL_DEV = true`) |

#### **Response Format**

Returns aggregated immunization data in JSON format.

##### **Example Response:**

```json
[
  {
    "OccurrenceYear": "2023",
    "Jurisdiction": "ON",
    "Sex": "Female",
    "Age": "5 years",
    "Dose": 2,
    "Count": 120,
    "ReferenceDate": "2023-12-31"
  },
  {
    "OccurrenceYear": "2023",
    "Jurisdiction": "BC",
    "Sex": "Male",
    "Age": "7 years",
    "Dose": 1,
    "Count": 95,
    "ReferenceDate": "2023-12-31"
  }
]
```

#### **Response Fields**

| Field            | Description                                  |
| ---------------- | -------------------------------------------- |
| `OccurrenceYear` | The year the immunization occurred           |
| `Jurisdiction`   | The province where immunization was recorded |
| `Sex`            | The patient's sex                            |
| `Age`            | The patient's age group                      |
| `Dose`           | The dose count for the vaccine               |
| `Count`          | Number of immunization records in this group |
| `ReferenceDate`  | The last day of the occurrence year          |

---

### **2️⃣ Health Check Endpoint**

#### **GET `/health`**

Returns API health status.

#### **Response Format**

```json
{
  "status": "ok"
}
```

---

## **Data Processing Workflow**

### **Step 1: Fetching FHIR Data**

- The API queries the FHIR server for **Immunization** resources.
- It paginates through records to retrieve complete datasets.
- Uses structured logging to monitor data retrieval.

### **Step 2: Fetching Patient Data**

- The API retrieves **Patient** resources from FHIR for each immunization record.
- Uses **LRU caching** to reduce redundant API calls.

### **Step 3: Processing and Aggregation**

- Extracts **Jurisdiction, Year, Sex, Age, Dose**.
- Groups data by these attributes.
- Assigns **December 31st** as the **ReferenceDate**.

### **Step 4: Caching & Authentication**

- Stores aggregated data for `AGGREGATION_INTERVAL` seconds.
- Enforces **JWT authentication** unless `IS_LOCAL_DEV` is enabled.
- Uses a **public key** for token verification.

---

## **Security Features**

- **JWT Authentication**: Tokens are validated via **RSA public keys**.
- **Data Protection**: No personal identifiers are stored or exposed.
- **Rate Limiting & Caching**: Prevents excessive FHIR API calls.
- **Structured Logging**: Ensures visibility into API operations.

---

## **Deployment**

### **Local Development**

Run the API locally with authentication disabled:

```bash
export IS_LOCAL_DEV=true
python app.py
```

### **Production Deployment**

Use **Gunicorn** for scalable deployments:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```
