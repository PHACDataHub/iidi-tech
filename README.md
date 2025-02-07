# Interoperable Immunization Data Initiative (IIDI)

## One-liner Summary

A structured implementation for **interoperable immunization data exchange**, supporting **FHIR-based APIs**, federated aggregation, and simulated cross-jurisdictional record transfers.

---

## Purpose

The **Interoperable Immunization Data Initiative (IIDI)** provides a **development environment** for testing **data interoperability, aggregation, and transfer mechanisms** between simulated jurisdictions. The initiative focuses on **FHIR-compliant data exchange**, ensuring that immunization records remain **structured, standardized, and accessible** while respecting system independence.

---

## Current Development Scope (MVP)

This repository implements the **minimum viable product (MVP) of the demo**, which includes:

- **FHIR-compliant immunization data repositories**, preloaded with synthetic patient records.
- **Mock provincial services**, simulating jurisdictional immunization data endpoints.
- **Federated data aggregation services** to generate structured immunization reports.
- **Basic PT-to-PT record transfer simulation** using FHIR standards.

---

## Technical Architecture

The IIDI architecture follows a **modular and federated approach**, ensuring **flexibility, security, and interoperability**:

## Key Architectural Components

## Key Architectural Components

1. **Mock Provincial Services (FHIR Repositories)**

   - Each province has its own **FHIR-compliant immunization data repository**.
   - Synthetic data is preloaded into these repositories for development and testing.

2. **Federated Aggregation Layer**

   - Aggregates anonymized immunization data from multiple provincial sources.
   - Enables **structured, standards-compliant data access** for reporting and analysis.
   - Incorporates **data integrity validation** to ensure accuracy and consistency.

3. **PT-to-PT Transfer Simulation**

   - Tests **FHIR-based** inter-jurisdictional data transfers.
   - Simulates **secure and reliable** data movement between provincial systems.
   - (Future Consideration) **Fault-tolerance mechanisms** may be explored for handling system failures or data inconsistencies.

4. **Security, Privacy & Data Integrity Mechanisms**
   - Implements **RBAC (Role-Based Access Control)** and **ABAC (Attribute-Based Access Control)** to enforce secure access policies.
   - Uses **data minimization techniques** to ensure privacy compliance.
   - Establishes **integrity validation processes** to detect and mitigate data corruption risks.
   - (Future Consideration) **Resiliency features** may be introduced to maintain system stability during outages or failures.

---

## Key Objectives

The **Interoperable Immunization Data Initiative (IIDI)** is structured around the following objectives:

1. **Enable Federated Immunization Record Access**

   - Use **FHIR-based APIs** to facilitate **decentralized yet structured** immunization data sharing.
   - Maintain **local control of records** while enabling **cross-jurisdictional access**.

2. **Support National Immunization Surveillance**

   - Transition from **batch-based** to **event-driven, real-time** data exchange.
   - Improve **public health reporting and decision-making**.

3. **Ensure Secure and Privacy-Compliant Data Sharing**

   - Use **role-based access control (RBAC)** and **data aggregation** to minimize exposure.
   - Ensure **privacy and security standards** are met across all data interactions.

4. **Facilitate PT-to-PT Immunization Record Transfers**
   - Ensure that **individual immunization histories move with them** between provinces.
   - Maintain **data consistency and accuracy** across jurisdictions.

---

## Development Quickstart

### **Prerequisites**

Before setting up the development environment, ensure the following dependencies are installed:

- **Docker v27+** (older versions may work but are unverified).
- **Optional:**
  - **Node.js v22** (v18 may work)
    - Used for running helper scripts.
    - If unavailable, commands like `npm run <command>` can be manually executed by referencing `package.json`.
  - **VSCode (Optional)**
    - Recommended extensions can be found in `.vscode/extensions.json`.

---

## Development quickstart

### Prerequisites

- Docker v27 (older versions may be sufficient, unverified)
- Optional:
  - Node v22
    - v18 may be sufficient
    - not strictly required. At the moment, it's mainly to run the script shorthands inside the root `package.json`. If you don't have Node, anywhere you see a `npm run <command>` statement below, you can look up `<command>` in package.json and run the corresponding terminal command directly (does not apply to shorthands for further `node ...` or `npm ...` commands obviously, but those are currently optional)
  - VSCode
    - not strictly required, other editors could be used, but assumed in future steps

### Quickstart Steps

- Clone repository locally
- Open a terminal inside the repo root
- (Optional) run `npm run ci:all` in the repo root, to install all project and service dependencies
- (Optional) install recommended vscode exstensions (see `.vscode/extensions.json`)
- Start the local dev docker-compose environment with `npm run dev` from the repo root
  - or manually run the `predev` and `dev` commands as defined in the root `package.json`
- Wait for docker-compose services to finish spinning up
- The following routes should now be available
  - Mock Ontario Services
    - http://localhost:8080/on/fhir
      - a HAPI FHIR JPA server, loaded with synthetic data
    - http://localhost:8080/on/browser
      - a FHIR patient browser pointed at the corresponding mock FHIR server
    - http://localhost:8080/on/aggregator/aggregated-data
      - REST endpoint for IPVD-format-compliant aggregated records from the corresponding mock FHIR server
    - transfer routes TBD
  - Mock B.C. Services
    - http://localhost:8080/bc/fhir
      - a HAPI FHIR JPA server, loaded with synthetic data
    - http://localhost:8080/bc/browser
      - a FHIR patient browser pointed at the corresponding mock FHIR server
    - http://localhost:8080/bc/aggregator/aggregated-data
      - REST endpoint for IPVD-format-compliant aggregated records from the corresponding mock FHIR server
    - transfer routes TBD
  - Mock Federal Services
    - http://localhost:8080/fed/federated-aggregator/aggregated-data
      - REST endpoint for IPVD-format-compliant aggregated records, federated from each PT aggregator
    - http://localhost:8080/fed/shiny-dashboard
      - not yet implemented
