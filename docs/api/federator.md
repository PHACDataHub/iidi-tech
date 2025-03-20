# **Federator API**

The **Federator API** is an **Express-based service** designed to retrieve, process, and aggregate data from multiple external sources. The API aggregates the data, validates it, and returns the grouped results to the caller. This service is **public**, meaning no authentication is required to make requests.

---

## **Environment Variables**

The API can be configured using the following environment variables:

| Variable           | Description                                                                                              | Default                      |
| ------------------ | -------------------------------------------------------------------------------------------------------- | ---------------------------- |
| `AGGREGATOR_URLS`  | A comma-separated list of URLs to fetch data from.                                                       | `http://localhost:8080/data` |
| `PRIVATE_KEY_PATH` | Path to the private key used for signing JWT tokens for outbound requests (for aggregator communication) | `/secrets/private_key.pem`   |
| `IS_LOCAL_DEV`     | Set `true` to disable JWT signing for local development environments                                     | `false`                      |

> **Note**: Additional provinces or jurisdictions can be added to the federator by modifying the `AGGREGATOR_URLS` environment variable. Each province or jurisdiction must have a corresponding external data source endpoint.

---

## **API Endpoints**

### **1️⃣ Get Aggregated Data**

#### **GET `/aggregated-data`**

This endpoint retrieves **aggregated data** from external data sources, validates it, and returns **grouped results**.

##### **Query Parameters**:

None.

##### **Request Headers**:

| Header | Description                                      |
| ------ | ------------------------------------------------ |
| None   | No authentication required for public API usage. |

##### **Response Format**:

- **`data`** (Array): A list of valid aggregated data objects. Each object contains:

  - `Age`: The age group for the data.
  - `Count`: The number of occurrences.
  - `Dose`: The immunization dose count.
  - `Jurisdiction`: The jurisdiction (e.g., ON, BC).
  - `OccurrenceYear`: The year the grouped occurrences took place.
  - `Sex`: The sex of the individuals (e.g., Male, Female, Other) in teh current group.
  - `ReferenceDate`: The reference date for the records in current group.

- **`errors`** (Array): A list of error messages for any failed data aggregations. Each error describes the failure reason (e.g., network issues, invalid data format).

##### **Example Response**:

```json
{
  "data": [
    {
      "Age": "15 years",
      "Count": 5,
      "Dose": 1,
      "Jurisdiction": "ON",
      "OccurrenceYear": "2015",
      "Sex": "Female",
      "ReferenceDate": "2015-12-31"
    },
    {
      "Age": "13 years",
      "Count": 3,
      "Dose": 2,
      "Jurisdiction": "BC",
      "OccurrenceYear": "2016",
      "Sex": "Male",
      "ReferenceDate": "2016-12-31"
    }
  ],
  "errors": []
}
```
