from flask import Flask, render_template, jsonify
import requests
import os

app = Flask(__name__)

# Define service entities for each province
entities = {
    "Federal": [
        {"name": "Dashboard", "url": os.getenv("FED_DASHBOARD_URL")},
        {"name": "Federator", "url": os.getenv("FED_FEDERATOR_URL")},
    ],
    "British Columbia (BC)": [
        {"name": "Patient Browser", "url": os.getenv("BC_BROWSER_URL")},
        {"name": "HAPI FHIR Server", "url": os.getenv("BC_FHIR_URL")},
        # {"name": "Aggregator", "url": os.getenv("BC_AGGREGATOR_URL")}, #Disabling the Aggregator as it requires key-based authentication to retrieve data.
        {
            "name": "Patient Transfer Dashboard",
            "url": os.getenv("BC_DEMO_TRANSFER_DASHBOARD_URL"),
        },
    ],
    "Ontario (ON)": [
        {"name": "Patient Browser", "url": os.getenv("ON_BROWSER_URL")},
        {"name": "HAPI FHIR Server", "url": os.getenv("ON_FHIR_URL")},
        # {"name": "Aggregator", "url": os.getenv("ON_AGGREGATOR_URL")}, #Disabling the Aggregator as it requires key-based authentication to retrieve data.
        {
            "name": "Patient Transfer Dashboard",
            "url": os.getenv("ON_DEMO_TRANSFER_DASHBOARD_URL"),
        },
    ],
}

# Define collapsible sections dynamically instead of hardcoding them in HTML
collapsible_sections = [
    {
        "title": "Synthetic Patient Data Generation",
        "content": """
            <h5><strong>Overview: What is Being Generated?</strong></h5>
            <p>
                The synthetic data mimics real-world immunization records from provincial registries while ensuring
                FHIR-compliant JSON format for interoperability. Differences between BC and ON data models are accounted for,
                including variations in fields such as allergy tracking.
            </p>

            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px;">
                <h6><strong>FHIR Patient Resource Structure</strong></h6>
                <p>A FHIR Patient Resource consists of core fields and extensions, ensuring consistency across jurisdictions.</p>

                <table style="width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #ddd;">
                    <thead>
                        <tr style="background-color: #e9ecef; border-bottom: 2px solid #ccc;">
                            <th style="text-align: left; padding: 10px;">Field</th>
                            <th style="text-align: left; padding: 10px;">FHIR Path</th>
                            <th style="text-align: left; padding: 10px;">Example Value</th>
                            <th style="text-align: left; padding: 10px;">Logic</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Patient ID</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Patient.id</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">"patient-001"</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Unique identifier.</td>
                        </tr>
                        <tr style="background-color: #f8f9fa;">
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Name</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Patient.name</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">{ "family": "Singh", "given": ["Simar"] }</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Randomized names using Faker.</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Gender</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Patient.gender</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">"male", "female", "other"</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Random selection.</td>
                        </tr>
                        <tr style="background-color: #f8f9fa;">
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Birth Date</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Patient.birthDate</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">"2012-06-15"</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Randomized within given age range.</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Address</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Patient.address</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">{ "city": "Toronto", "state": "ON" }</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Province-specific logic.</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <h6><strong>Provincial Differences in Data Generation</strong></h6>
            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px;">
                <p><strong>British Columbia (BC) Specific Fields</strong></p>
                <ul style="margin-top: 5px; margin-bottom: 5px;">
                    <li>Allergy information is included using FHIR `AllergyIntolerance` resource.</li>
                    <li>Uses SNOMED CT-coded allergy types, severity levels, and reaction dates.</li>
                </ul>

                <p><strong>Ontario (ON) Specific Fields</strong></p>
                <ul style="margin-top: 5px; margin-bottom: 5px;">
                    <li>Ontario does not track allergy information in immunization records.</li>
                    <li>The script skips allergy generation for ON patients.</li>
                </ul>
            </div>

            <h6><strong>Immunization Data Generation (FHIR Standard)</strong></h6>
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #ddd;">
                <thead>
                    <tr style="background-color: #e9ecef; border-bottom: 2px solid #ccc;">
                        <th style="text-align: left; padding: 10px;">Field</th>
                        <th style="text-align: left; padding: 10px;">FHIR Path</th>
                        <th style="text-align: left; padding: 10px;">Example Value</th>
                        <th style="text-align: left; padding: 10px;">Logic</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">Vaccine Type</td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">Immunization.vaccineCode</td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">"MMR", "Influenza"</td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">Random selection.</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">Manufacturer</td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">Immunization.manufacturer</td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">"Pfizer", "Moderna"</td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">Random manufacturer assignment.</td>
                    </tr>
                </tbody>
            </table>

            <h6><strong>Summary of Key Features</strong></h6>
            <ul style="margin-top: 5px; margin-bottom: 5px;">
                <li><strong>FHIR-Compliant</strong>: Structured to align with HL7 FHIR.</li>
                <li><strong>Synthetic but Realistic</strong>: Uses Faker for realistic patient data.</li>
                <li><strong>Handles Provincial Variations</strong>: BC and ON have different data models.</li>
                <li><strong>Includes Adverse Reactions & Exemptions</strong>: Adds realism for testing.</li>
            </ul>
        """,
    },
    {
        "title": "PT-to-PT Transfer Assumptions",
        "content": """
            <h5><strong>Overview: What is PT-to-PT Transfer?</strong></h5>
            <p>When a patient moves or seeks healthcare in another province, their immunization record needs to be securely transferred. This Proof of Concept (PoC) focuses on the technical feasibility of such transfers while leaving governance, consent, and policy discussions out of scope.</p>

            <h6><strong>How the Transfer Works</strong></h6>
            <p>The transfer follows a structured push-based approach:</p>
            <ul style="margin-top: 5px; margin-bottom: 5px;">
                <li>The originating province (data owner) initiates the transfer.</li>
                <li>A secure API transmits immunization records between provinces.</li>
                <li>The transfer occurs only after external consent and authorization.</li>
                <li>The receiving province acknowledges and integrates the record.</li>
            </ul>

            <h6><strong>Data Transferred Between Provinces</strong></h6>

            <p><strong>1. Patient Information</strong></p>
            <ul style="margin-top: 5px; margin-bottom: 5px;">
                <li>Unique patient identifier within the provincial system.</li>
                <li>Full name, birth date, and gender.</li>
                <li>Address, including city, province, and postal code.</li>
                <li>Health card number (if applicable) for identity matching.</li>
            </ul>

            <p><strong>2. Immunization History</strong></p>
            <ul style="margin-top: 5px; margin-bottom: 5px;">
                <li>Vaccine type (CVX codes).</li>
                <li>Date of administration and dose number.</li>
                <li>Manufacturer and lot number.</li>
                <li>Site of administration (e.g., left arm, right arm).</li>
                <li>Adverse reactions and exemptions (if applicable).</li>
            </ul>

            <p><strong>3. Metadata for PT-to-PT Transfers</strong></p>
            <ul style="margin-top: 5px; margin-bottom: 5px;">
                <li>Transfer origin marker indicating the source jurisdiction.</li>
                <li>Receiving province acknowledgment confirming integration.</li>
            </ul>

            <h6><strong>Technical Flow of the Transfer</strong></h6>
            <ol style="margin-top: 5px; margin-bottom: 5px;">
                <li>Patient relocates or seeks healthcare in another province.</li>
                <li>Originating province completes consent and authorization.</li>
                <li>A secure API request is triggered by the originating province.</li>
                <li>Receiving province ingests and processes the immunization record.</li>
                <li>The record is now available in the receiving province’s registry.</li>
            </ol>

            <h6><strong>Key Assumptions and Considerations</strong></h6>
            <ul style="margin-top: 5px; margin-bottom: 5px;">
                <li>This PoC does not handle consent management; it must be externally managed.</li>
                <li>The push-based model ensures data is only transferred when authorized.</li>
                <li>Manual transfer requests (fax, email, policy-driven) remain possible but are out of scope.</li>
                <li>The PoC leverages FHIR repositories to validate secure data exchange.</li>
            </ul>

            <h6><strong>Testing and Simulation Approach</strong></h6>
            <ul style="margin-top: 5px; margin-bottom: 5px;">
                <li>FHIR-based simulation using synthetic data.</li>
                <li>Initial scope focused on MMR vaccine records, expandable in future phases.</li>
                <li>Optional UI demonstration to visualize transferred records.</li>
            </ul>
        """,
    },
    {
        "title": "Aggregation & PHAC Data Access",
        "content": """
            <h5><strong>Overview: Why is Aggregation Needed?</strong></h5>
            <p style="line-height: 1.5; color: #333;">
                PHAC does not require full patient-level data but instead needs structured, summarized reports for national immunization monitoring.
                Aggregation transforms raw immunization records into anonymized datasets, ensuring accuracy while protecting privacy.
                This process maintains consistency across provinces, even when different immunization tracking systems are used.
            </p>
            <p style="line-height: 1.5; color: #333;">
                <strong>PHAC does not access or process identifiable Personal Health Information (PHI) at any stage.</strong>
                All de-identification is performed at the Provincial/Territorial (PT) level before any data is shared with PHAC.
                The information shared with PHAC is structured, anonymized, and formatted for public health reporting in compliance with privacy regulations.
                Aggregation ensures uniform national immunization reporting while aligning with PT-specific privacy frameworks.
            </p>

            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px;">
                <h6><strong>Key Data Captured in Aggregation</strong></h6>
                <p>The aggregation logic extracts the following key fields:</p>

                <table style="width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #ddd;">
                    <thead>
                        <tr style="background-color: #e9ecef; border-bottom: 2px solid #ccc;">
                            <th style="text-align: left; padding: 10px;">Field</th>
                            <th style="text-align: left; padding: 10px;">Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Reference Date</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Date of immunization event (reported at an aggregate level).</td>
                        </tr>
                        <tr style="background-color: #f8f9fa;">
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Jurisdiction</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Province where the immunization was recorded (e.g., BC, ON).</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Age Group</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Categorized age ranges (e.g., 0-2 years, 3-5 years, etc.).</td>
                        </tr>
                        <tr style="background-color: #f8f9fa;">
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Gender</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Aggregate counts by gender category (Male, Female, Other).</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Vaccine Type</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Type of vaccine administered (e.g., MMR, COVID-19).</td>
                        </tr>
                        <tr style="background-color: #f8f9fa;">
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Dose Count</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Total number of doses administered in the reporting period.</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px;">Total Patients Vaccinated</td>
                            <td style="padding: 8px;">Unique number of individuals vaccinated within the reporting period.</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <h6><strong>How Data Aggregation Works</strong></h6>
            <ol style="margin-top: 5px; margin-bottom: 5px; padding-left: 15px;">
                <li>Extract immunization records from FHIR repositories at the PT level.</li>
                <li>De-identify data by removing personally identifiable details (e.g., names, health card numbers) entirely at the PT level before aggregation.</li>
                <li>Categorize data by jurisdiction, age group, gender, and vaccine type.</li>
                <li>Summarize dose counts and calculate total vaccinated individuals.</li>
                <li>Format the final dataset into a structured, anonymized report in compliance with PHAC's reporting framework.</li>
            </ol>

            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px; margin-top: 15px;">
                <h6><strong>Benefits for Public Health and PHAC</strong></h6>
                <ul style="margin-top: 5px; margin-bottom: 5px;">
                    <li>Reduces complexity by providing summarized, structured reports rather than raw data.</li>
                    <li>Ensures privacy by removing personal identifiers and focusing on aggregate statistics.</li>
                    <li>Standardizes immunization reporting across jurisdictions for consistency and interoperability.</li>
                    <li>Scales efficiently to include new vaccines and evolving public health priorities.</li>
                </ul>
            </div>

            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px; margin-top: 15px;">
                <h6><strong>Addressing Key Concerns and Clarifications</strong></h6>
                <p><strong>PHAC's Role in De-Identification:</strong> The previous document wording implied that PHAC de-identifies data, which is incorrect.</p>
                <p><strong>Clarification:</strong> PTs are fully responsible for de-identification before sharing data. PHAC does not access raw patient-level data.</p>

                <p><strong>PHAC's Role in Aggregation:</strong> The document previously suggested PHAC "fetches" patient data and aggregates it, which is inaccurate.</p>
                <p><strong>Clarification:</strong> Aggregation is conducted entirely at the PT level. PHAC receives only aggregated, anonymized data.</p>
            </div>
        """,
    },
    {
        "title": "Technical Infrastructure",
        "content": """
            <h5>Overview</h5>
            <p>
                The technical architecture enables secure, real-time immunization data exchange between jurisdictions while
                ensuring that each province maintains full control over its data. It follows a federated model, using a
                combination of API gateways, security layers, and standardized data exchange mechanisms.
            </p>

            <h6>Key Components</h6>
            <ul>
                <li><strong>Provincial Immunization Systems</strong>: Each province maintains its own immunization data repository.</li>
                <li><strong>FHIR-Based Data Exchange</strong>: Standardized API interactions ensure compatibility between different systems.</li>
                <li><strong>Access Control Gateway</strong>: Manages authentication, authorization, and data access policies.</li>
                <li><strong>Interoperability Layer</strong>: Enables data transformation and validation to align different provincial data formats.</li>
                <li><strong>Audit & Compliance Framework</strong>: Ensures all data access is logged and follows regulatory requirements.</li>
            </ul>
            <h6><strong>Federated Immunization Data Architecture (UJ-1)</strong></h6>
            <p>
                The <strong>federated model</strong> ensures that each province maintains local control over its immunization records while
                supporting national-level aggregation for public health surveillance. The architecture consists of:
            </p>
            <ul>
                <li><strong>FHIR Immunization Registries</strong>: Each province maintains its own secure database.</li>
                <li><strong>Synthetic Data Generator</strong>: Creates test data for validation.</li>
                <li><strong>SMART Patient Viewer</strong>: Allows healthcare providers to view immunization records.</li>
                <li><strong>Aggregator</strong>: Summarizes and anonymizes immunization records before sharing with PHAC.</li>
                <li><strong>Federator (PHAC)</strong>: Receives de-identified, aggregated data for national reporting.</li>
                <li><strong>R-Shiny Dashboards</strong>: Provides real-time analytics and insights.</li>
            </ul>
            <img src="/static/images/UJ-1.png" alt="Federated Immunization Data Architecture (UJ-1)" style="max-width:100%;">

            <h6><strong>PT-to-PT Transfer Workflow (UJ-2)</strong></h6>
            <p>
                The PT-to-PT transfer mechanism enables secure, structured movement of immunization records when a patient relocates
                between jurisdictions. This workflow ensures that records are securely exchanged without centralization.
            </p>
            <ul>
                <li><strong>API Gateway</strong>: Facilitates secure and authenticated communication.</li>
                <li><strong>FHIR Data Transfer</strong>: Ensures records are formatted correctly.</li>
                <li><strong>Message Queue</strong>: Manages retries and queued requests.</li>
                <li><strong>Outbound Transfer Service</strong>: Extracts and sends immunization data.</li>
                <li><strong>Inbound Transfer Service</strong>: Receives and validates incoming records.</li>
            </ul>
            <img src="/static/images/UJ-2.png" alt="PT-to-PT Data Transfer Workflow (UJ-2)" style="max-width:100%;">
            <h6>Data Flow</h6>
            <ol>
                <li>A request for immunization data is initiated by an authorized system.</li>
                <li>The Access Control Gateway verifies authentication and consent requirements.</li>
                <li>Once approved, data is retrieved from the provincial immunization system.</li>
                <li>The interoperability layer processes and transforms the data to a standard format.</li>
                <li>The response is securely delivered back to the requester.</li>
            </ol>

            <h6>Security & Compliance</h6>
            <ul>
                <li>End-to-end encryption is enforced for all data exchanges.</li>
                <li>Mutual TLS authentication ensures secure API communication.</li>
                <li>Audit logs are maintained to track all requests and access events.</li>
                <li>Provincial data sovereignty is preserved by keeping raw data within jurisdictions.</li>
            </ul>

            <h6>Scalability & Infrastructure</h6>
            <ul>
                <li>Containerized microservices enable efficient scaling.</li>
                <li>Event-driven architecture allows real-time data synchronization.</li>
                <li>Cloud-hosted infrastructure supports high availability and fault tolerance.</li>
            </ul>
        """,
    },
    {
        "title": "Foundation for Federated Data Architecture",
        "content": """
        <h5><strong>Overview</strong></h5>
        <p>
            The Foundation for Federated Data Architecture outlines a secure and interoperable model for exchanging immunisation data across Canada.
            It allows real-time synchronisation, role-based access, and privacy-first data sharing — without centralising control or ownership.
            The model consists of four domains: <strong>Data Emitters</strong>, <strong>Security and Governance</strong>,
            <strong>Federated Infrastructure</strong>, and <strong>General Users</strong>. Together, these domains form the foundation of compliant,
            distributed health data exchange.
        </p>

        <h6><strong>Architecture Diagram</strong></h6>
        <img src="/static/svg/foundation-for-federated-data-architecture.svg"
             alt="Federated Data Architecture"
             style="max-width: 100%; border: 1px solid #ccc; padding: 6px; border-radius: 6px; margin-top: 10px;">

        <h6 style="margin-top: 20px;"><strong>Key Concepts</strong></h6>

        <h6 style="margin-top: 16px; color: #856404;"><strong>🟨 Security, Control, Governance and Enforcement</strong></h6>
        <ul>
            <li><strong style="background-color:#fff3cd; padding:2px 6px; border-radius:4px;">Access Control Models:</strong>
                Define who can access what data, under which conditions, and for what purpose. Tailored to each jurisdiction’s legal frameworks,
                they enforce compliant, transparent, and auditable data usage.
            </li>

            <li><strong style="background-color:#fff3cd; padding:2px 6px; border-radius:4px;">Data Governance Gateway:</strong>
                Validates all data requests by enforcing jurisdictional agreements, consent requirements, and access policies.
                It serves as the central gatekeeper for safe and legal data exchange.
            </li>

            <li><strong style="background-color:#fff3cd; padding:2px 6px; border-radius:4px;">Policy Enforcement:</strong>
                Executes real-time policy checks such as time-bound access, consent verification, and purpose-of-use restrictions.
                These enforcement systems make governance actionable at runtime.
            </li>

            <li><strong style="background-color:#fff3cd; padding:2px 6px; border-radius:4px;">Security Protocols:</strong>
                Apply identity validation, encryption, and system hardening across the federation. These controls support compliance
                with Canadian privacy legislation and prevent unauthorised access.
            </li>
        </ul>

        <h6 style="margin-top: 16px; color: #0c5460;"><strong>🟦 Infrastructure, Storage, Query, Data Flow and Standards</strong></h6>
        <ul>
            <li><strong style="background-color:#bee5eb; padding:2px 6px; border-radius:4px;">Cloud Platforms:</strong>
                Scalable and secure environments for deploying workloads, sharing services, and running jurisdiction-specific applications.
                These platforms enable a consistent operational foundation across jurisdictions.
            </li>

            <li><strong style="background-color:#bee5eb; padding:2px 6px; border-radius:4px;">API Management:</strong>
                Provides secure access points for system-to-system communication. Includes request validation, rate limiting,
                authentication, and observability across federated APIs.
            </li>

            <li><strong style="background-color:#bee5eb; padding:2px 6px; border-radius:4px;">Data Storage Solutions:</strong>
                Stores both jurisdictional and aggregated datasets using encryption-at-rest and role-based access controls.
                Designed for durability, auditability, and regional autonomy.
            </li>

            <li><strong style="background-color:#cfe2ff; padding:2px 6px; border-radius:4px;">Data Standards (HL7 FHIR):</strong>
                HL7 FHIR enables structured, consistent, and machine-readable representation of health records.
                It underpins semantic interoperability across different jurisdictions and systems.
            </li>

            <li><strong style="background-color:#d1ecf1; padding:2px 6px; border-radius:4px;">Real-Time Data Sync:</strong>
                Asynchronous, event-driven pipelines that update immunisation records across systems continuously.
                These mechanisms ensure up-to-date views while preserving data sovereignty.
            </li>
        </ul>

        <h6 style="margin-top: 16px; color: #155724;"><strong>🟩 Source Data Emitters</strong></h6>
        <ul>
            <li><strong style="background-color:#d1e7dd; padding:2px 6px; border-radius:4px;">Data Emitter Nodes:</strong>
                The authoritative sources of immunisation data within each province or territory. These nodes maintain full control
                and apply governance policies before any data is shared externally.
            </li>
        </ul>

        <h6 style="margin-top: 16px; color: #155724;"><strong>🟩 General Data Users</strong></h6>
        <ul>
            <li><strong style="background-color:#d1e7dd; padding:2px 6px; border-radius:4px;">General Users:</strong>
                Authorised systems or users who access governed outputs — not raw PT data — to generate insights, analytics,
                or reports. Access is standardised, governed, and fully auditable.
            </li>
        </ul>
    """,
    },
    {
        "title": "GitHub Repository & Architecture",
        "content": """
            <h5>Overview</h5>
            <p>
                The Interoperable Immunization Data Initiative (IIDI) is built using a secure, scalable, and federated model.
                The architecture enables seamless data exchange while ensuring that provincial and territorial jurisdictions
                maintain control over their immunization records.
            </p>

            <h6>GitHub Repository</h6>
            <p>
                The source code and related documentation for IIDI can be found in the official GitHub repository:
            </p>
            <ul>
                <li><a href="https://github.com/PHACDataHub/iidi-tech" target="_blank"><strong>IIDI-Tech GitHub Repository</strong></a></li>
            </ul>

            <h6>Technical Architecture</h6>
            <p>
                The IIDI technical stack is designed for interoperability, security, and compliance with public health data
                governance frameworks. Key architecture components are documented below:
            </p>
            <ul>
                <li><a href="https://github.com/PHACDataHub/iidi-tech/blob/main/docs/architecture/GCP%20Architecture/GCP-Architecture.png" target="_blank"><strong>GCP Architecture Overview</strong></a> - High-level infrastructure design for deployment.</li>
            </ul>
            <img src="https://github.com/PHACDataHub/iidi-tech/blob/main/docs/architecture/GCP%20Architecture/GCP-Architecture.png?raw=true"
                alt="GCP Architecture Diagram" style="max-width:100%;">

            <h6>Architecture Review Board Documentation</h6>
            <p>
                The architecture follows a federated data model to support two primary user journeys:
            </p>
            <ul>
                <li><a href="https://github.com/PHACDataHub/iidi-tech/blob/main/docs/architecture/User-Journey-1.md" target="_blank"><strong>Interoperable Immunization Data Initiative (IIDI) – User Journey 1: PT-to-PT Transfer</strong></a></li>
                <li><a href="https://github.com/PHACDataHub/iidi-tech/blob/main/docs/architecture/User-Journey-2.md" target="_blank"><strong>Interoperable Immunization Data Initiative (IIDI) – User Journey 2: PT-to-PHAC</strong></a></li>
            </ul>
        """,
    },
]


@app.route("/")
def index():
    return render_template(
        "index.html", entities=entities, collapsible_sections=collapsible_sections
    )


def check_health(url):
    """Helper function to check service health by making an HTTP request."""
    try:
        response = requests.get(url, timeout=5, allow_redirects=True)
        return response.status_code in (200, 302)  # Consider 200 and 302 as 'healthy'
    except requests.exceptions.RequestException:
        return None  # Any exception means service is unreachable


@app.route("/health-check/<province_name>")
def health_check(province_name):
    """Endpoint to check the health of services per province."""
    province_name = province_name.replace("%20", " ")

    if province_name in entities:
        province_health_status = {}
        for service in entities[province_name]:
            result = check_health(service["url"])
            health_status = (
                "healthy" if result else "error" if result is None else "unhealthy"
            )
            province_health_status[service["name"]] = health_status

        return jsonify({province_name: province_health_status})

    return jsonify({"error": "Province not found"}), 404


@app.route("/health", methods=["GET"])
def health():
    """Simple health check for Kubernetes probes."""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
