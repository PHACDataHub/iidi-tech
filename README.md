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

### Local Machine

#### Local Prerequisites

- Docker v27 (older versions may be sufficient, unverified)
- Optional:
  - Node v22
    - v18 may be sufficient
    - not strictly required. At the moment, it's mainly to run the script shorthands inside the root `package.json`. If you don't have Node, anywhere you see a `npm run <command>` statement below, you can look up `<command>` in package.json and run the corresponding terminal command directly (does not apply to shorthands for further `node ...` or `npm ...` commands obviously, but those are currently optional)
  - VSCode
    - not strictly required, other editors could be used, but assumed in future steps

#### Local Quickstart Steps

- Clone repository locally
- Open a terminal inside the repo root
- (Optional) run `npm run ci:all` in the repo root, to install all project and service dependencies
- (Optional) install recommended vscode exstensions (see `.vscode/extensions.json`)
- Start the local dev docker-compose environment with `npm run dev` from the repo root
  - or manually run the `predev` and `dev` commands as defined in the root `package.json`
- Wait for docker-compose services to finish spinning up
- Visit http://localhost:8080 for the "demo portal", which links through to the available services

#### Local Node Service Debugging

- (Re)start the docker-compose environment with `npm run dev:debug`
- Open `chrome://inspect/#devices` in chrome, click "Open dedicated DevTools for Node" and use the "Add connection" menu to set ports to watch
  - One per node server in the docker-compose env, should all be exposed as `127.0.0.1:92##`. Look in `./docker-compose.dev.yaml` for containers with port mappings like `9229:92##` to see what services expose debugger sockets

### GitHub Codespaces

#### Codespaces Prerequisites

- Credits to burn
  - We don't currently have employer provided credits. You likely have a personal amount of 120 free core-hours per month. These may burn faster than you'd think though, the codespace currently needs at least 4 cores to perform. Not ideal.

#### Codespaces Quickstart Steps

- Create a codespace attached to the `iidi-tech` repo
- Note that `npm run ci:all` runs as a post startup step, don't have to do it manually but packages may not be available immediately on fresh codespace launch
- (Optional) install recommended vscode exstensions (see `.vscode/extensions.json`); codespaces will prompt you for this
- Start the local dev docker-compose environment with `npm run dev` from the repo root (default working dir when you open a terminal in the codespace)
- Wait for docker-compose services to finish spinning up
- Under the ports tab, find the external URL associated with the codespaces 8080 port. Open this port and you should see the "demo portal" page, which links through to the available services

#### Codespaces Node Service Debugging

- (Re)start the docker-compose environment with `npm run dev:debug`
- On your local machine, install the GitHub CLI "gh", run `gh auth login` and `gh auth refresh -h github.com -s codespace`, follow interactive steps
- Use the GitHub CLI ssh tool to create an SSH tunnel from your local machine to the codespace container, eg. `gh codespace ssh -- -L 92##:localhost:92## -L 92##:localhost:92##...`
  - One per node server in the docker-compose env, should all be exposed an ports `92##`. Look in `./docker-compose.dev.yaml` for containers with port mappings like `9229:92##` to see what services expose debuggers
  - Note: might be rejected if you try to make too many tunnels, uncertain. If it does, only tunnel to the specific debug port(s) you need
- Open `chrome://inspect/#devices` in chrome, click "Open dedicated DevTools for Node" and use the "Add connection" menu to set ports to watch
  - One per SSH tunnel, should all be exposed as `127.0.0.1:92##`

### IMPORTANT: working with the dev docker-compose env

It's important to note that the local docker images are cached by the `name:tag` pair set in each docker-compose service's `image` field. Images that copy in code/dependnecies at image build time need to have their tag incremented in the docker-compose file to ensure that up to date changes are captured! This is both a problem in dev (to refresh against local changes, you need to either increment the tag number or run `docker image rm name:tag --force` and then restart the docker-compose env) and for commited code between devs (assume other devs have cached builds of older version numbers, if you merge changes without bumping the tag then your changes may not be reflected in their local dev env).

At the moment, this impacts

- both synthesizers
- both aggregators
- both patient browsers
- the r-shiny dashboard
- the demo portal

This does not impact any service using the `node-dev` image. The `node-dev` image mounts source files from the local dev machine and installs dependencies at run time. The `node-dev` services are always kept "live" against local repo state.
