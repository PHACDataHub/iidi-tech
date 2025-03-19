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
