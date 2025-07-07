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
        "title": "Foundation for Federated Data Architecture",
        "content": """
        <h5><strong>Overview</strong></h5>
        <p>
            The Foundation for Federated Data Architecture outlines a secure and interoperable model for exchanging immunization data across Canada.
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

        <h6 style="margin-top: 16px; color: #155724;"><strong>Data Emitters and Users</strong></h6>
        <ul>
            <li><strong style="background-color:#d1e7dd; padding:2px 6px; border-radius:4px;">Data Emitter Nodes:</strong>
                The authoritative sources of immunization data within each province or territory. These nodes maintain full control
                and apply governance policies before any data is shared externally.
            </li>
            <li><strong style="background-color:#d1e7dd; padding:2px 6px; border-radius:4px;">General Users:</strong>
                Authorised systems or users who access governed outputs — not raw PT data — to generate insights, analytics,
                or reports. Access is standardised, governed, and fully auditable.
            </li>
        </ul>

        <h6 style="margin-top: 16px; color: #856404;"><strong>Security, Control, Governance and Enforcement</strong></h6>
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

        <h6 style="margin-top: 16px; color: #0c5460;"><strong>Infrastructure, Storage, Query, Data Flow and Standards</strong></h6>
        <ul>
            <li><strong style="background-color:#cfe2ff; padding:2px 6px; border-radius:4px;">Cloud Platforms:</strong>
                Scalable and secure environments for deploying workloads, sharing services, and running jurisdiction-specific applications.
                These platforms enable a consistent operational foundation across jurisdictions.
            </li>

            <li><strong style="background-color:#cfe2ff; padding:2px 6px; border-radius:4px;">API Management:</strong>
                Provides secure access points for system-to-system communication. Includes request validation, rate limiting,
                authentication, and observability across federated APIs.
            </li>

            <li><strong style="background-color:#cfe2ff; padding:2px 6px; border-radius:4px;">Data Storage Solutions:</strong>
                Stores both jurisdictional and aggregated datasets using encryption-at-rest and role-based access controls.
                Designed for durability, auditability, and regional autonomy.
            </li>

            <li><strong style="background-color:#cfe2ff; padding:2px 6px; border-radius:4px;">Data Standards (HL7 FHIR):</strong>
                HL7 FHIR enables structured, consistent, and machine-readable representation of health records.
                It underpins semantic interoperability across different jurisdictions and systems.
            </li>

            <li><strong style="background-color:#cfe2ff; padding:2px 6px; border-radius:4px;">Real-Time Data Sync:</strong>
                Asynchronous, event-driven pipelines that update immunization records across systems continuously.
                These mechanisms ensure up-to-date views while preserving data sovereignty.
            </li>
        </ul>
        """
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

            <h6><strong>Kubernetes Infrastructure</strong></h6>
            <p>
                The platform is built on Kubernetes, providing a scalable and resilient foundation for our federated architecture.
                Below is our Kubernetes cluster diagram:
            </p>
            <img src="/static/images/k8s-architecture.png" alt="Kubernetes Infrastructure" style="max-width:100%; border:1px solid #ddd; padding:10px; border-radius:8px; margin-bottom:20px;">
            

            <h6>Key Components</h6>
            <ul>
                <li><strong>Provincial Immunization Systems</strong>: Each province maintains its own immunization data repository.</li>
                <li><strong>FHIR-Based Data Exchange</strong>: Standardized API interactions ensure compatibility between different systems.</li>
                <li><strong>Access Control Gateway</strong>: Manages authentication, authorization, and data access policies.</li>
                <li><strong>Interoperability Layer</strong>: Enables data transformation and validation to align different provincial data formats.</li>
                <li><strong>Audit & Compliance Framework</strong>: Ensures all data access is logged and follows regulatory requirements.</li>
            </ul>

            

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
        """
    },
    {
        "title": "User Journey 1: PT-to-PT Transfer",
        "content": """
            <h5><strong>Overview: What is PT-to-PT Transfer?</strong></h5>
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

            <h6><strong>Technical Flow of the Transfer</strong></h6>
            <ol>
                <li>Patient relocates or seeks healthcare in another province</li>
                <li>Originating province completes consent and authorization</li>
                <li>Secure API request triggered by originating province</li>
                <li>Receiving province ingests and processes immunization record</li>
                <li>Record becomes available in receiving province's registry</li>
            </ol>

            <img src="/static/images/UJ-1.png" alt="PT-to-PT Data Transfer Workflow" style="max-width:100%; border:1px solid #ddd; padding:10px; border-radius:8px;">
            
            <h6><strong>Data Transferred Between Provinces</strong></h6>
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #ddd;">
                <thead style="background-color: #e9ecef;">
                    <tr>
                        <th style="text-align: left; padding: 10px;">Category</th>
                        <th style="text-align: left; padding: 10px;">Data Elements</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Patient Information</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                            <ul>
                                <li>Unique patient identifier within the provincial system.</li>
                                <li>Full name, birth date, gender</li>
                                <li>Address (city, province, postal code)</li>
                                <li>Health card number (if applicable) for identity matching</li>
                            </ul>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Immunization History</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                            <ul>
                                <li>Vaccine type (CVX codes)</li>
                                <li>Date of administration and dose number</li>
                                <li>Manufacturer and lot number</li>
                                <li>Site of administration (e.g., left arm, right arm)</li>
                                <li>Adverse reactions and exemptions (if applicable)</li>
                            </ul>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px;"><strong>Metadata</strong></td>
                        <td style="padding: 10px;">
                            <ul>
                                <li>Transfer origin marker indicating the source jurisdiction</li>
                                <li>Receiving province acknowledgment confirming integration.</li>
                            </ul>
                        </td>
                    </tr>
                </tbody>
            </table>

            <h6><strong>Addressing Key Concerns and Clarificationsk</strong></h6>
            <ul>
                <li>Data is <strong>synthetically generated</strong> based on FHIR standards. PoC leverages FHIR repositories for secure data exchange validation</li>
                <li>Consent management must be externally managed (out of PoC scope)</li>
                <li>Push-based model ensures data is only transferred when authorized</li>
                <li>Manual transfer requests (fax, email) remain possible but out of scope</li>
                <li>Initial scope focused on MMR vaccine records, expandable in future phases</li>
                <li>Optional UI demonstration to visualize transferred records.</li>
            </ul>
        """
    },
    {
        "title": "User Journey 2: Federated Immunization Data Architecture",
        "content": """
            <h5><strong>Federated Architecture Overview</strong></h5>
            <p>
                This architecture ensures each province maintains local control over immunization records while supporting national-level 
                aggregation for public health surveillance. The model consists of:
            </p>

            <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                <div style="flex: 1; background-color: #f8f9fa; padding: 15px; border-radius: 8px;">
                    <h6><strong>Provincial Components</strong></h6>
                    <ul>
                        <li><strong>FHIR Immunization Registries</strong>: Secure provincial databases</li>
                        <li><strong>Synthetic Data Generator</strong>: Creates test data for validation</li>
                        <li><strong>SMART Patient Viewer</strong>: Healthcare provider access to records</li>
                        <li><strong>Aggregator</strong>: Summarizes/anonymizes records for PHAC</li>
                    </ul>
                </div>
                <div style="flex: 1; background-color: #f8f9fa; padding: 15px; border-radius: 8px;">
                    <h6><strong>Federal Components</strong></h6>
                    <ul>
                        <li><strong>Federator (PHAC)</strong>: Receives aggregated data</li>
                        <li><strong>R-Shiny Dashboards</strong>: National analytics and insights</li>
                    </ul>
                </div>
            </div>

            
            <img src="/static/images/UJ-2.png" alt="Federated Immunization Data Architecture" style="max-width:100%; border:1px solid #ddd; padding:10px; border-radius:8px; margin-bottom:20px;">

            <h6><strong>Data Flow</strong></h6>
            <ol>
                <li>A request for immunization data is initiated by an authorized system.</li>
                <li>The Access Control Gateway verifies authentication and consent requirements.</li>
                <li>Once approved, data is retrieved from the provincial immunization system.</li>
                <li>The interoperability layer processes and transforms the data to a standard format.</li>
                <li>The response is securely delivered back to the requester.</li>
            </ol>
            
            <h5><strong>Key Principles</strong></h5>
                <ul>
                    <li>PTs maintain full control over their immunization data</li>
                    <li>PHAC only receives pre-aggregated, anonymized datasets</li>
                    <li>No patient-level data leaves provincial systems</li>
                    <li>All de-identification occurs at source (PT level)</li>
                </ul>
            
            <h5><strong>Aggregation & PHAC Data Access</strong></h5>
            
            <p>
                PHAC does not require full patient-level data but instead needs structured, summarized reports for national immunization monitoring. 
                Aggregation transforms raw immunization records into anonymized datasets, ensuring accuracy while protecting privacy. 
                This process maintains consistency across provinces, even when different immunization tracking systems are used. 
            </p>
            
            <p>
                <b>PHAC does not access or process identifiable Personal Health Information (PHI) at any stage.</b> All de-identification is performed at 
                the Provincial/Territorial (PT) level before any data is shared with PHAC. The information shared with PHAC is structured, anonymized, 
                and formatted for public health reporting in compliance with privacy regulations. Aggregation ensures uniform national immunization 
                reporting while aligning with PT-specific privacy frameworks.
            </p>
            
            <h6><strong>How Data Aggregation Works</strong></h6>
            <ol>
                <li><strong>Extract</strong> immunization records from FHIR repositories at the PT level</li>
                <li><strong>De-identify</strong> data by removing personally identifiable details (e.g., names, health card numbers) entirely at the PT level before aggregation</li>
                <li><strong>Categorize</strong> data by jurisdiction, age group, gender, and vaccine type</li>
                <li><strong>Summarize</strong> dose counts and calculate total vaccinated individuals</li>
                <li><strong>Format</strong> the final dataset into a structured, anonymized report in compliance with PHAC's reporting framework</li>
            </ol>
            
            <h6><strong>Key Data Captured in Aggregation</strong></h6>
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #ddd;">
                <thead style="background-color: #e9ecef;">
                    <tr>
                        <th style="text-align: left; padding: 10px;">Field</th>
                        <th style="text-align: left; padding: 10px;">Description</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">Reference Date</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">Date of immunization event (reported at an aggregate level)</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">Jurisdiction</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">Province where immunization was recorded (e.g., BC, ON)</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">Age Group</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">Categorized age ranges (e.g., 0-2 years, 3-5 years, etc.)</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">Gender</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">Aggregate counts by gender category (Male, Female, Other)</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">Vaccine Type</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">Type of vaccine administered (e.g., MMR, COVID-19)</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">Dose Count</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">Total number of doses administered in the reporting period</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px;">Total Patients Vaccinated</td>
                        <td style="padding: 10px;">Unique number of individuals vaccinated within the reporting period</td>
                    </tr>
                </tbody>
            </table>
            
            <h6 style="margin-top: 20px;"><strong>Benefits for Public Health and PHAC</strong></h6>
            <ul>
                <li>Reduces complexity by providing summarized, structured reports rather than raw data</li>
                <li>Ensures privacy by removing personal identifiers and focusing on aggregate statistics</li>
                <li>Standardizes immunization reporting across jurisdictions for consistency and interoperability</li>
                <li>Scales efficiently to include new vaccines and evolving public health priorities</li>
            </ul>
            
            <h6><strong>Addressing Key Concerns and Clarifications</strong></h6>
            <ul>
                <li>
                    <strong>De-identification Responsibility:</strong> 
                    The previous document incorrectly implied PHAC de-identifies data. 
                    <strong>PTs are fully responsible for de-identification before sharing data, 
                    and PHAC does not access raw patient-level data.</strong>
                </li>
                <li>
                    <strong>Aggregation Process:</strong> 
                    The document previously inaccurately suggested PHAC "fetches" patient data for aggregation. 
                    <strong>Aggregation is conducted entirely at the PT level, 
                    and PHAC only receives aggregated, anonymized data.</strong>
                </li>
            </ul>
                
        """
    },
    {
        "title": "Synthetic Patient Data Generation",
        "content": """
            <h5><strong>Overview: What is Being Generated?</strong></h5>
            <p>
                The synthetic data mimics real-world immunization records from provincial registries while ensuring
                FHIR-compliant JSON format for interoperability. Differences between BC and ON data models are accounted for,
                including variations in fields such as allergy tracking.
            </p>

            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px; margin-bottom: 20px;">
                <h6><strong>FHIR Patient Resource Structure</strong></h6>
                <p>A FHIR Patient Resource consists of core fields and extensions, ensuring consistency across jurisdictions.</p>

                <table style="width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #ddd;">
                    <thead style="background-color: #e9ecef;">
                        <tr>
                            <th style="text-align: left; padding: 10px;">Field</th>
                            <th style="text-align: left; padding: 10px;">FHIR Path</th>
                            <th style="text-align: left; padding: 10px;">Example Value</th>
                            <th style="text-align: left; padding: 10px;">Logic</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Patient ID</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Patient.id</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">"patient-001"</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Unique identifier</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Name</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Patient.name</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{ "family": "Singh", "given": ["Simar"] }</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Randomized names</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Gender</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Patient.gender</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">"male", "female", "other"</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Random selection</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Birth Date</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Patient.birthDate</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">"2012-06-15"</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Randomized within age range</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px;">Address</td>
                            <td style="padding: 8px;">Patient.address</td>
                            <td style="padding: 8px;">{ "city": "Toronto", "state": "ON" }</td>
                            <td style="padding: 8px;">Province-specific logic</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px; margin-bottom: 20px;">
                <h6><strong>Provincial Differences in Data Generation</strong></h6>
                <div style="display: flex; gap: 20px;">
                    <div style="flex: 1;">
                        <p><strong>British Columbia (BC) Specific Fields</strong></p>
                        <ul>
                            <li>Allergy information included using FHIR AllergyIntolerance resource</li>
                            <li>Uses SNOMED CT-coded allergy types</li>
                            <li>Includes severity levels and reaction dates</li>
                        </ul>
                    </div>
                    <div style="flex: 1;">
                        <p><strong>Ontario (ON) Specific Fields</strong></p>
                        <ul>
                            <li>No allergy information in immunization records</li>
                            <li>Allergy generation skipped for ON patients</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px;">
                <h6><strong>Immunization Data Generation (FHIR Standard)</strong></h6>
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #ddd;">
                    <thead style="background-color: #e9ecef;">
                        <tr>
                            <th style="text-align: left; padding: 10px;">Field</th>
                            <th style="text-align: left; padding: 10px;">FHIR Path</th>
                            <th style="text-align: left; padding: 10px;">Example Value</th>
                            <th style="text-align: left; padding: 10px;">Logic</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Vaccine Type</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Immunization.vaccineCode</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">"MMR", "Influenza"</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Random selection</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Manufacturer</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Immunization.manufacturer</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">"Pfizer", "Moderna"</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Random assignment</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Dose Number</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Immunization.protocolApplied.doseNumber</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">1, 2, 3</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Based on vaccine type</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px;">Adverse Reactions</td>
                            <td style="padding: 8px;">Immunization.reaction</td>
                            <td style="padding: 8px;">"Fever", "Swelling"</td>
                            <td style="padding: 8px;">Conditional generation</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        """
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
                <li><a href="https://github.com/PHACDataHub/iidi-tech" target="_blank" style="color: #0066cc; text-decoration: underline;"><strong>IIDI-Tech GitHub Repository</strong></a></li>
            </ul>

            <h6>Technical Architecture</h6>
            <p>
                The IIDI technical stack is designed for interoperability, security, and compliance with public health data
                governance frameworks. Key architecture components are documented below:
            </p>
            <ul>
                <li><a href="https://github.com/PHACDataHub/iidi-tech/blob/main/docs/architecture/GCP%20Architecture/GCP-Architecture.png" target="_blank" style="color: #0066cc; text-decoration: underline;"><strong>GCP Architecture Overview</strong></a> - High-level infrastructure design for deployment.</li>
            </ul>
            <img src="https://github.com/PHACDataHub/iidi-tech/blob/main/docs/architecture/GCP%20Architecture/GCP-Architecture.png?raw=true"
                alt="GCP Architecture Diagram" style="max-width:100%; border:1px solid #ddd; padding:10px; border-radius:8px; margin-top:10px; margin-bottom:20px;">

            <h6>Architecture Review Board Documentation</h6>
            <p>
                The architecture follows a federated data model to support two primary user journeys:
            </p>
            <ul>
                <li><a href="https://github.com/PHACDataHub/iidi-tech/blob/main/docs/architecture/User-Journey-1.md" target="_blank" style="color: #0066cc; text-decoration: underline;"><strong>Interoperable Immunization Data Initiative (IIDI) – User Journey 1: PT-to-PT Transfer</strong></a></li>
                <li><a href="https://github.com/PHACDataHub/iidi-tech/blob/main/docs/architecture/User-Journey-2.md" target="_blank" style="color: #0066cc; text-decoration: underline;"><strong>Interoperable Immunization Data Initiative (IIDI) – User Journey 2: Federated Architecture</strong></a></li>
            </ul>
        """
    }
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
