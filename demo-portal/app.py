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
        The Foundation for Federated Data Architecture defines a secure, scalable, and policy-driven approach to sharing data across independent organizations, systems, or jurisdictions.
        It enables real-time synchronization, role-based access, and privacy-first data exchange without requiring central control or ownership.
        The model is built on four key domains: <strong>Data Emitters</strong>, <strong>Security and Governance</strong>, <strong>Federated Infrastructure</strong>, and <strong>General Users</strong>.
    </p>

    <h6><strong>Architecture Diagram</strong></h6>
    <img src="/static/svg/foundation-for-federated-data-architecture.svg"
        alt="Federated Data Architecture"
        style="max-width: 100%; border: 1px solid #ccc; padding: 6px; border-radius: 6px; margin-top: 10px;">

    <h6 style="margin-top: 15px;"><strong>Data Emitters and Users</strong></h6>
    <ul>
        <li><strong style="background-color:#F3D8C9; padding:2px 6px; border-radius:4px;">Data Emitter Nodes:</strong>
            Original sources of data operated by individual partners. These nodes retain full ownership and apply local governance policies before releasing data to others.
        </li>
        <li><strong style="background-color:#F3D8C9; padding:2px 6px; border-radius:4px;">General Users:</strong>
            Authorized systems or users that access governed, aggregated outputs through standard interfaces. Data access is approved, compliant, and auditable by design.
        </li>
    </ul>

    <h6 style="margin-top: 15px;"><strong>Security, Control, Governance and Enforcement</strong></h6>
    <ul>
        <li><strong style="background-color:#D3F0E8; padding:2px 6px; border-radius:4px;">Access Control Models:</strong>
            Define who can access which data, under what conditions, and for what purpose. These models are flexible and respect each partner’s legal and privacy frameworks.
        </li>
        <li><strong style="background-color:#D3F0E8; padding:2px 6px; border-radius:4px;">Data Governance Gateway:</strong>
            Governs all data requests through a centralized decision engine. It checks for appropriate permissions, agreements, and compliance requirements before granting access.
        </li>
        <li><strong style="background-color:#D3F0E8; padding:2px 6px; border-radius:4px;">Policy Enforcement:</strong>
            Applies runtime rules such as expiry windows, purpose-of-use restrictions, and consent checks. Ensures governance is enforced continuously and automatically.
        </li>
        <li><strong style="background-color:#D3F0E8; padding:2px 6px; border-radius:4px;">Security Protocols:</strong>
            Enforces encryption, identity validation, and secure communication across all participants. Aligns with national privacy legislation and modern security practices.
        </li>
    </ul>

    <h6 style="margin-top: 15px;"><strong>Infrastructure, Storage, Query and Standards</strong></h6>
    <ul>
        <li><strong style="background-color:#F1D4DC; padding:2px 6px; border-radius:4px;">Cloud Platforms:</strong>
            Provide the infrastructure for deploying and operating federation components. Each partner manages its own environment while maintaining interoperability.
        </li>
        <li><strong style="background-color:#F1D4DC; padding:2px 6px; border-radius:4px;">API Management:</strong>
            Facilitates secure data exchange through consistent APIs. Includes validation, rate limiting, authentication, and full traceability of all interactions.
        </li>
        <li><strong style="background-color:#F1D4DC; padding:2px 6px; border-radius:4px;">Data Storage Solutions:</strong>
            Host datasets securely with encryption, audit trails, and access controls. Support both local data and aggregated, cross-jurisdictional information.
        </li>
        <li><strong style="background-color:#F1D4DC; padding:2px 6px; border-radius:4px;">Data Standards:</strong>
            Use formats such as HL7 FHIR to ensure consistency and machine readability. Standards support seamless integration and shared understanding across systems.
        </li>
        <li><strong style="background-color:#F1D4DC; padding:2px 6px; border-radius:4px;">Real Time Data Sync:</strong>
            Keeps systems aligned using event-driven updates and automated pipelines. Maintains data freshness without compromising autonomy or performance.
        </li>
    </ul>

    <h6 style="margin-top: 15px;"><strong>Summary</strong></h6>
    <p>
        This architecture is not only a technical model but also a governance framework that respects local control, enforces compliance, and builds trust.
        It enables real-time collaboration across distributed data environments by combining secure infrastructure, enforceable policy, and interoperable standards.
        Whether applied in health, climate, finance, or public safety, it offers a flexible and future-ready foundation for secure data collaboration at scale.
    </p>
  """,
    },
    {
        "title": "Technical Architecture",
        "content": """
            <h5>Overview</h5>
            <p>
                The IIDI technical architecture operationalizes the foundational domains of the Federated Data Architecture model:
                <strong style="background-color:#F3D8C9; padding:2px 6px; border-radius:4px;">Data Emitters & General Users</strong>,
                <strong style="background-color:#D3F0E8; padding:2px 6px; border-radius:4px;">Security, Control, Governance & Enforcement</strong>, and
                <strong style="background-color:#F1D4DC; padding:2px 6px; border-radius:4px;">Infrastructure, Storage, Query & Standards</strong>.
                Each deployed component in the Kubernetes platform directly corresponds to one or more of these foundational domains.
            </p>

            <h6 style="margin-top: 24px"><strong>Data Emitters & General Users</strong></h6>
            <div style="background-color:#F3D8C9; padding:10px; border-radius:6px; margin-bottom:16px;">
                <ul>
                    <li><strong>FHIR Immunization Registries:</strong> Provincial HAPI FHIR Servers act as data emitter nodes, serving as authoritative sources of immunization records.</li>
                    <li><strong>Synthesizer:</strong> Generates FHIR-compliant synthetic patient data to support system testing, demo flows, and validation.</li>
                    <li><strong>SMART Patient Viewer:</strong> Enables healthcare providers (general users) to securely access immunization records through a standardized interface.</li>
                </ul>
            </div>

            <h6 ><strong>Security, Control, Governance & Enforcement</strong></h6>
            <div style="background-color:#D3F0E8; padding:10px; border-radius:6px; margin-bottom:16px;">
                <ul>
                    <li><strong>Istio with mTLS:</strong> Enforces secure, mutually authenticated communication between services. Ensures policy enforcement at runtime.</li>
                    <li><strong>Transfer Services:</strong> Outbound and Inbound Transfer components apply FHIR validation, policy enforcement, and jurisdictional access control prior to any data exchange.</li>
                    <li><strong>Redis:</strong> Provides asynchronous job queuing with backpressure and retry handling, ensuring fault-tolerant and governed data delivery.</li>
                    <li><strong>Aggregator:</strong> Performs de-identification and summarization at the PT level, enforcing local governance rules before reporting to PHAC.</li>
                </ul>
            </div>

            <h6 ><strong>Infrastructure, Storage, Query & Standards</strong></h6>
            <div style="background-color:#F1D4DC; padding:10px; border-radius:6px; margin-bottom:16px;">
                <ul>
                    <li><strong>Kubernetes Namespaces (BC, ON, PHAC):</strong> Isolate workloads across jurisdictions and the federal level, ensuring multi-tenant security and operational autonomy.</li>
                    <li><strong>Containerized Microservices:</strong> All components (FHIR servers, aggregators, dashboards, etc.) are deployed as containers for resilience and scalability.</li>
                    <li><strong>Event-Driven Architecture:</strong> Supports real-time data sync and decoupling through Redis and asynchronous service communication.</li>
                    <li><strong>HL7 FHIR:</strong> Data is exchanged using the HL7 FHIR standard, ensuring semantic interoperability and consistent representation across systems.</li>
                    <li><strong>R Shiny Dashboard (PHAC):</strong> Hosts aggregated, de-identified data from PTs, enabling national immunization reporting and insight generation.</li>
                </ul>
            </div>

            <h6 style="margin-top: 15px;"><strong>Architecture Diagram</strong></h6>
            <p>Each technical component is shown in the cluster diagram below, with color-coded mappings to its corresponding foundational pillar.</p>
            <img src="/static/svg/k8s-architecture.svg" alt="Kubernetes Infrastructure" style="max-width:100%; border:1px solid #ddd; padding:10px; border-radius:8px; margin-bottom:20px;">
            <h6 style="margin-top: 15px;"><strong>Summary</strong></h6>
            <p>
                The IIDI technical architecture translates high-level federation principles into a working, production-grade implementation.
                Each component — from secure data emitters to governed aggregation and federated APIs — has been deliberately mapped to the foundational pillars
                of the federated model. Through Kubernetes, containerized services, Istio, Redis, and HL7 FHIR, the platform enables real-time,
                standards-compliant immunization data sharing across jurisdictions, all while maintaining local autonomy and national coordination.
                The architecture prioritizes security, resilience, and future scalability — laying the groundwork for broader public health applications beyond immunization.
            </p>
        """,
    },
    {
        "title": "User Journey 1: PT-to-PT Transfer",
        "content": """
            <h5><strong>Overview: Secure Movement of Immunization Records Across Jurisdictions</strong></h5>
            <p>
                The PT-to-PT transfer capability represents a foundational pillar of the Interoperable Immunization Data Initiative (IIDI).
                It enables the secure, structured, and standards-aligned movement of patient immunization records when individuals relocate
                between provinces or territories. This journey reflects real-world clinical workflows, empowering jurisdictions to
                preserve patient continuity of care while maintaining data sovereignty and regulatory compliance.
            </p>
            <p>
                Unlike centralized models, this federated approach avoids direct data aggregation. Instead, immunization records are
                transmitted securely from one jurisdiction to another using modern interoperability protocols and runtime policy enforcement.
                The model reinforces trust between jurisdictions by validating consent, applying consistent data standards,
                and ensuring all transfers are fully auditable.
            </p>

            <h6 style="margin-top: 15px;"><strong>Key Federated Components Enabling PT-to-PT Transfer</strong></h6>
            <ul>
                <li><strong>API Gateway:</strong> Facilitates secure, authorized communication between the outbound and inbound services.</li>
                <li><strong>FHIR Data Exchange:</strong> Immunization records are structured using HL7 FHIR standards, ensuring semantic interoperability.</li>
                <li><strong>Redis Message Queue:</strong> Provides asynchronous job queuing with fault tolerance, enabling retry mechanisms and rate limiting.</li>
                <li><strong>Transfer-Outbound Service:</strong> Authenticates, packages, and sends records from the origin jurisdiction after consent validation.</li>
                <li><strong>Transfer-Inbound Service:</strong> Verifies integrity, enforces policy, and ingests records into the receiving jurisdiction’s FHIR registry.</li>
            </ul>

            <h6><strong>Technical Flow of a Cross-Jurisdiction Transfer</strong></h6>
            <ol>
                <li>The patient relocates to a new province or seeks care in a different jurisdiction.</li>
                <li>The originating province completes consent checks and authorizes the outbound request.</li>
                <li>The Transfer-Outbound service securely packages the FHIR-formatted payload and pushes it to Redis.</li>
                <li>The Transfer-Inbound service at the receiving jurisdiction polls Redis, validates the request, and ensures compliance with HL7 FHIR.</li>
                <li>Upon successful validation, the record is written into the receiving jurisdiction’s HAPI FHIR server and becomes queryable.</li>
            </ol>

            <img src="/static/images/UJ-1.png" alt="PT-to-PT Data Transfer Workflow" style="max-width:100%; border:1px solid #ddd; padding:10px; border-radius:8px; margin-bottom:20px;">

            <h6><strong>What Data Is Transferred?</strong></h6>
            <p>
                The PT-to-PT transfer includes only essential, structured information required for safe clinical continuity. All payloads are
                formatted using HL7 FHIR and exclude unnecessary or non-consented details.
            </p>
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
                                <li>Unique patient identifier (local to jurisdiction)</li>
                                <li>Name, date of birth, and gender</li>
                                <li>Address (city, province, postal code)</li>
                                <li>Health card number (if authorized)</li>
                            </ul>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Immunization History</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                            <ul>
                                <li>Vaccine type (e.g., MMR, COVID-19)</li>
                                <li>Date administered, manufacturer, and lot number</li>
                                <li>Dose number and administration site</li>
                                <li>Any adverse reactions or exemptions recorded</li>
                            </ul>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px;"><strong>Metadata</strong></td>
                        <td style="padding: 10px;">
                            <ul>
                                <li>Source province/territory of the transfer</li>
                                <li>Destination province confirmation and ingest time</li>
                            </ul>
                        </td>
                    </tr>
                </tbody>
            </table>

            <h6><strong>Safeguards, Scope, and Key Clarifications</strong></h6>
            <ul>
                <li>All data is <strong>synthetic and anonymized</strong>, designed solely for demonstration and validation purposes.</li>
                <li>Consent validation must occur externally and is assumed as a precondition for any data exchange.</li>
                <li>This is a <strong>push-based model</strong> — receiving jurisdictions do not pull or request patient data independently.</li>
                <li>Manual transfers (fax/email) are considered out of scope for this model.</li>
                <li>The current proof of concept focuses on MMR vaccines but can support additional vaccine types in future iterations.</li>
                <li>Optional user interface demos can visualize transferred records in real-time via SMART Viewer or API query.</li>
            </ul>

            <h6 style="margin-top: 15px;"><strong>Summary</strong></h6>
            <p>
                PT-to-PT transfer is a critical step toward modernizing Canada’s immunization data ecosystem. It enables provinces to securely
                exchange structured health records while maintaining autonomy and enforcing local governance. By combining FHIR standards,
                secure message queues, consent-aware services, and runtime policy enforcement, IIDI delivers a highly portable and scalable
                foundation for cross-jurisdictional data sharing.
            </p>
            <p>
                This user journey shows that interoperable health data is possible without centralization. Instead, it highlights how a federated
                model — backed by technical rigour, real-world workflows, and strong trust boundaries — can support secure, patient-centred
                data exchange across Canada’s diverse health systems.
            </p>
        """,
    },
    {
        "title": "User Journey 2: Federated Immunization Data Architecture",
        "content": """
        <h5><strong>Overview: Federated, Privacy-Preserving Public Health Surveillance</strong></h5>
        <p>
            This user journey demonstrates how immunization data from provincial and territorial registries can be securely
            aggregated and reported to PHAC — without ever relinquishing patient-level control. Instead of centralizing health data,
            the architecture follows a federated model, in which <strong>each jurisdiction governs its own data pipelines</strong>
            and contributes only <em>structured, de-identified</em> insights for national surveillance. This design supports public trust,
            legal compliance, and analytical consistency across Canada’s diverse health landscape.
        </p>

        <div style="display: flex; gap: 20px; margin-bottom: 20px;">
            <div style="flex: 1; background-color: #f8f9fa; padding: 15px; border-radius: 8px;">
                <h6><strong>Provincial Components</strong></h6>
                <ul>
                    <li><strong>FHIR Immunization Registries:</strong> Source of truth for immunization records (e.g., BC, ON).</li>
                    <li><strong>Synthetic Data Generator:</strong> Simulates realistic, FHIR-compliant records for safe validation and testing.</li>
                    <li><strong>SMART Patient Viewer:</strong> Supports local user access to jurisdiction-governed records.</li>
                    <li><strong>Aggregator:</strong> Performs summarization and de-identification at the provincial level before reporting to PHAC.</li>
                </ul>
            </div>
            <div style="flex: 1; background-color: #f8f9fa; padding: 15px; border-radius: 8px;">
                <h6><strong>Federal Components</strong></h6>
                <ul>
                    <li><strong>Federator (PHAC):</strong> Receives structured, anonymized data sets and enforces validation policies.</li>
                    <li><strong>R Shiny Dashboards:</strong> Delivers visual insights to support national decision-making, coverage analysis, and vaccine equity.</li>
                </ul>
            </div>
        </div>

        <img src="/static/images/UJ-2.png" alt="Federated Immunization Data Architecture" style="max-width:100%; border:1px solid #ddd; padding:10px; border-radius:8px; margin-bottom:20px;">

        <h6><strong>Data Flow and Governance</strong></h6>
        <ol>
            <li>An authorized request triggers the aggregation process at the provincial level.</li>
            <li>Access control systems validate authentication, authorization, and jurisdictional policies.</li>
            <li>The Aggregator extracts immunization records from the FHIR registry, applies de-identification, and formats data to a shared schema.</li>
            <li>The anonymized payload is securely transmitted to PHAC’s Federator using mTLS encryption and audit logging.</li>
            <li>PHAC validates and ingests the report for national analytics — without ever accessing identifiable PHI.</li>
        </ol>

        <h5><strong>Core Design Principles</strong></h5>
        <ul>
            <li><strong>Provincial Autonomy:</strong> Data never leaves a jurisdiction in raw form — PTs control aggregation and transmission.</li>
            <li><strong>Privacy by Design:</strong> All de-identification occurs locally, before any report reaches PHAC.</li>
            <li><strong>Analytical Integrity:</strong> Aggregation adheres to HL7 FHIR-based schemas, ensuring national consistency despite system diversity.</li>
            <li><strong>PHAC Receives Only What Is Needed:</strong> Summarized, structured reports — not patient-level records — power national surveillance.</li>
        </ul>

        <h6><strong>How Aggregation Works at the PT Level</strong></h6>
        <ol>
            <li>FHIR immunization records are queried securely within each provincial registry.</li>
            <li>All identifiers (e.g., names, health numbers, addresses) are stripped before aggregation.</li>
            <li>Records are grouped by jurisdiction, age group, gender, and vaccine type.</li>
            <li>Dose counts and patient totals are calculated per category.</li>
            <li>The final report is formatted into a PHAC-compliant schema and transmitted securely.</li>
        </ol>

        <h6><strong>Key Data Fields in Aggregated Reports</strong></h6>
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
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">When the immunization occurred (aggregated format)</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">Jurisdiction</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">Province or territory (e.g., BC, ON)</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">Age Group</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">Binned age ranges (e.g., 0–2, 3–5, etc.)</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">Gender</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">Aggregated by reported gender category</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">Vaccine Type</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">CVX or vaccine category (e.g., MMR)</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">Dose Count</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">Total doses administered in the reporting window</td>
                </tr>
                <tr>
                    <td style="padding: 10px;">Total Patients Vaccinated</td>
                    <td style="padding: 10px;">Unique individuals included in the report</td>
                </tr>
            </tbody>
        </table>

        <h6 style="margin-top: 15px;"><strong>Public Health Impact and National Value</strong></h6>
        <ul>
            <li>Minimizes risk by avoiding transmission of personal identifiers</li>
            <li>Strengthens trust between provinces and PHAC through clear governance and auditability</li>
            <li>Reduces manual reporting overhead by providing real-time, structured updates</li>
            <li>Supports agile decision-making and cross-jurisdictional comparison via dashboards</li>
        </ul>

        <h6><strong>Clarifications and Assumptions</strong></h6>
        <ul>
            <li><strong>De-Identification Responsibility:</strong> PHAC never de-identifies data. This is strictly handled by PTs before aggregation.</li>
            <li><strong>Aggregation Scope:</strong> PHAC does not fetch or query patient data. Only pre-aggregated summaries are accepted.</li>
        </ul>

        <h6 style="margin-top: 15px;"><strong>Summary</strong></h6>
        <p>
            The Federated Immunization Data Architecture redefines how public health intelligence can be gathered across Canada —
            securely, respectfully, and efficiently. It proves that meaningful data aggregation does not require centralization or
            compromise on privacy. Instead, it demonstrates a scalable trust model: one that allows PHAC to access timely insights
            without ever touching raw personal data.
        </p>
        <p>
            Through strong provincial ownership, secure interfaces, and structured standards like HL7 FHIR, this model balances local
            autonomy with national accountability. It offers a replicable, privacy-preserving pattern for other public health domains
            — from COVID surveillance to vaccine equity to broader disease analytics.
        </p>
    """,
    },
    {
        "title": "Synthetic Patient Data Generation",
        "content": """
            <h5><strong>Overview: Safe, Realistic, Standards-Compliant Data for Interoperability Testing</strong></h5>
            <p>
                To enable safe experimentation and validation of cross-jurisdictional workflows, the IIDI platform generates
                <strong>synthetic immunization data</strong> that mirrors real-world records without exposing personal health information (PHI).
                These records are formatted using the <strong>HL7 FHIR standard</strong> and reflect variations in provincial data models —
                ensuring both realism and jurisdictional fidelity.
            </p>
            <p>
                Synthetic data is used to test FHIR endpoints, simulate patient movement between provinces, validate dashboard pipelines,
                and support continuous development without compromising privacy. Each generated patient, immunization, and allergy record is
                deterministic, governed, and fully traceable.
            </p>

            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px; margin-bottom: 20px;">
                <h6><strong>FHIR Patient Resource Structure</strong></h6>
                <p>Each synthetic patient record follows the <strong>FHIR Patient resource</strong> schema, including core identifiers and demographic extensions:</p>

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
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Unique, auto-generated UUID</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Name</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Patient.name</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{"family": "Singh", "given": ["Simar"]}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Faker-generated name with diverse samples</td>
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
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Randomized within pediatric age cohorts</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px;">Address</td>
                            <td style="padding: 8px;">Patient.address</td>
                            <td style="padding: 8px;">{"city": "Toronto", "state": "ON"}</td>
                            <td style="padding: 8px;">Province-specific logic to simulate local residency</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px; margin-bottom: 20px;">
                <h6><strong>Provincial Variations in Data Generation</strong></h6>
                <p>The generator accounts for jurisdictional rules by customizing fields per province:</p>
                <div style="display: flex; gap: 20px;">
                    <div style="flex: 1;">
                        <p><strong>British Columbia (BC)</strong></p>
                        <ul>
                            <li>Includes <strong>AllergyIntolerance</strong> resources</li>
                            <li>Uses SNOMED-CT codes for allergy types</li>
                            <li>Captures severity and onset date</li>
                        </ul>
                    </div>
                    <div style="flex: 1;">
                        <p><strong>Ontario (ON)</strong></p>
                        <ul>
                            <li>No allergy data is generated for ON patients</li>
                            <li>FHIR bundles exclude the AllergyIntolerance resource</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px;">
                <h6><strong>FHIR Immunization Resource Structure</strong></h6>
                <p>Each synthetic patient is linked to multiple immunization records with the following structure:</p>

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
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Random draw from supported vaccine types</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Manufacturer</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Immunization.manufacturer</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">"Pfizer", "Moderna"</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">Randomly assigned from list of vendors</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px;">Dose Number</td>
                            <td style="padding: 8px;">Immunization.protocolApplied.doseNumber</td>
                            <td style="padding: 8px;">1, 2</td>
                            <td style="padding: 8px;">Sequential or randomized per patient profile</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <h6 style="margin-top: 15px;"><strong>Summary</strong></h6>
            <p>
                The synthetic data engine plays a foundational role in enabling rapid development, demonstration, and validation
                of IIDI architecture components. It replicates real-world variability while preserving full privacy, allowing
                provinces and the federal government to simulate end-to-end data flows without relying on production data.
            </p>
            <p>
                Its strict alignment with FHIR standards and support for jurisdiction-specific nuances (e.g., BC vs. ON) ensures that
                interoperability testing remains grounded in actual data behavior — preparing the system for real-world onboarding in the future.
            </p>
        """,
    },
    {
        "title": "GitHub Repository & Infrastructure",
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

            <h6>Infrastructure</h6>
            <p>
                The IIDI technical stack is designed for interoperability, security, and compliance with public health data
                governance frameworks. Key infrastrcutural components are documented below:
            </p>
            <ul>
                <li><a href="https://github.com/PHACDataHub/iidi-tech/blob/main/docs/architecture/GCP%20Architecture/GCP-Architecture.png" target="_blank" style="color: #0066cc; text-decoration: underline;"><strong>GCP Infrastructure Overview</strong></a> - High-level infrastructure design for deployment.</li>
            </ul>
            <img src="https://github.com/PHACDataHub/iidi-tech/blob/main/docs/architecture/GCP%20Architecture/GCP-Architecture.png?raw=true"
                alt="GCP Infrastructure Diagram" style="max-width:100%; border:1px solid #ddd; padding:10px; border-radius:8px; margin-top:10px; margin-bottom:20px;">

            <h6>Architecture Review Board Documentation</h6>
            <p>
                The architecture follows a federated data model to support two primary user journeys:
            </p>
            <ul>
                <li><a href="https://github.com/PHACDataHub/iidi-tech/blob/main/docs/architecture/User-Journey-1/User-Journey-1.md" target="_blank" style="color: #0066cc; text-decoration: underline;"><strong>Interoperable Immunization Data Initiative (IIDI) – User Journey 1: PT-to-PT Transfer</strong></a></li>
                <li><a href="https://github.com/PHACDataHub/iidi-tech/blob/main/docs/architecture/User-Journey-2/User-Journey-2.md" target="_blank" style="color: #0066cc; text-decoration: underline;"><strong>Interoperable Immunization Data Initiative (IIDI) – User Journey 2: Federated Architecture</strong></a></li>
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
