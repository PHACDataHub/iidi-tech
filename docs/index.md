# Welcome to IIDI-Tech Documentation

## Overview

The **Interoperable Immunization Data Initiative (IIDI)** is a **federated data-sharing architecture** designed to facilitate **secure, standardized, and real-time immunization data exchange** between **provincial and federal health systems** in Canada. This initiative enables **inter-provincial (PT-to-PT) immunization record transfers** and **data reporting to PHAC (Public Health Agency of Canada)** for national surveillance and analysis.

IIDI leverages **FHIR-based APIs, Kubernetes-based microservices, Redis for job queuing, and R-Shiny for visualization**, ensuring a robust, scalable, and privacy-compliant ecosystem.

---

## **System Components & Architecture**

### **Provincial Kubernetes Namespaces: Ontario & British Columbia**
Each **province operates its own Kubernetes namespace**, where immunization records are processed and transferred securely. Key components include:

- **SMART Patient Viewer**: Allows healthcare providers to view immunization records in a FHIR-compliant format.
- **HAPI FHIR Server**: Serves as the **FHIR repository**, storing immunization records.
- **Aggregator Service**: Extracts and prepares data for **PT-to-PT transfers and PT-to-PHAC reporting**.
- **Synthesizer**: Generates **synthetic FHIR data** for testing and validation.
- **Redis Queue**: Handles **asynchronous processing** to manage API rate limits and ensure resilience.
- **Transfer Services (Outbound & Inbound)**: Enable **secure transmission** of immunization records across jurisdictions.

---

### **Federal Kubernetes Namespace: PHAC (Federal Data Processing)**
At the federal level, PHAC processes immunization data for **national-level analysis**. Core services include:

- **Federator Service**: Receives and **normalizes** immunization records from multiple provinces.
- **R-Shiny Dashboard**: Provides **visual insights** for public health officials, helping track **coverage trends, vaccine uptake, and emerging patterns**.

---

## **PT-to-PT Transfer Data Flow**

### **1 Transfer Initiation (Ontario → BC)**
- Ontario’s **Transfer-Outbound Service** retrieves immunization records from the **HAPI FHIR Server** for a **migrating patient**.
- Data is structured in **FHIR-compliant JSON** format.

### **2 Job Queued in Redis (Ontario)**
- The JSON payload is **queued in Redis** to handle API rate limits and ensure reliable processing.

### **3 Secure Data Transfer (Ontario → BC)**
- Ontario’s **Transfer-Outbound Service** encrypts and transmits the immunization record to **BC’s Transfer-Inbound Service** via **mutual TLS (mTLS)**.

### **4 Transfer Processing (BC Inbound Service)**
- BC’s **Transfer-Inbound Service** verifies **API authentication** and validates the payload using **HL7 FHIR standards**.

### **5 Data Storage in BC’s FHIR Repository**
- The immunization record is **stored in BC’s HAPI FHIR Server**, maintaining **data integrity and compliance** with **FHIR guidelines**.

---

## **PT-to-PHAC Data Reporting**

### **1 Data Aggregation from Provincial Systems**
- Each province’s **Aggregator Service** queries the **HAPI FHIR Server** to retrieve structured immunization records.

### **2 FHIR Data Validation & De-Identification**
- The **Aggregator Service** processes and **de-identifies** immunization records.
- Validation is performed against **FHIR standards** to ensure **accuracy & compliance** before federal reporting.

### **3 Secure Data Transfer to PHAC**
- Each province’s **Aggregator Service** securely transmits records to PHAC’s **Federator Service** using:
  - **TLS encryption**
  - **API security policies** for protection in transit

### **4 PHAC Federator Service Validates & Normalizes Data**
- The **Federator Service** at PHAC:
  - Receives and **normalizes** records
  - **Removes inconsistencies**
  - **Standardizes FHIR fields** from multiple PTs into a unified format

### **5 Data Storage in PHAC’s Federal Data Platform**
- Once validated, immunization records are stored in **PHAC’s Federated Data Repository** for **national surveillance & trend analysis**.

### **6 Immunization Insights via R-Shiny Dashboard**
- Processed data is **visualized** in **R-Shiny Dashboards** for:
  - **Tracking vaccine trends**
  - **Identifying coverage gaps**
  - **Monitoring emerging patterns**

---

## **Why IIDI Matters**
✅ **Interoperability**: Enables **seamless** immunization record sharing across **jurisdictions**  
✅ **FHIR Standards**: Ensures **data consistency & compliance**  
✅ **Security & Privacy**: Implements **mutual TLS, API authentication, and de-identification**  
✅ **Scalability**: Uses **Kubernetes-based microservices & Redis for async processing**  
✅ **Analytics & Insights**: Provides **real-time public health intelligence** via **R-Shiny dashboards**  

---

## **Next Steps**
- 📄 Read the [Getting Started Guide](getting-started.md) to set up your environment.
- 🔍 Explore the [Architecture Overview](architecture/GCP-Architecture.md).
- 🛠 Check out the [API Reference](api.md) for integration details.

---

This documentation provides a **comprehensive guide** to understanding **IIDI’s architecture, data flow, and security model**. If you have any questions, refer to the **Contributing Guide** or reach out to the **IIDI Technical Team**.
