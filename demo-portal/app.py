from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

# Define service entities for each province
entities = {
    "Federal": [
        {"name": "Dashboard", "url": "https://rshiny-dashboard.federal.iidi.alpha.phac.gc.ca/browser"},
        {"name": "Aggregator", "url": "https://aggregator.federal.iidi.alpha.phac.gc.ca/browser"},
    ],
    "British Columbia (BC)": [
        {"name": "Patient Browser", "url": "https://patient-browser.bc.iidi.alpha.phac.gc.ca"},
        {"name": "HAPI FHIR Server", "url": "https://fhir.bc.iidi.alpha.phac.gc.ca"},
        {"name": "Aggregator", "url": "https://aggregator.bc.iidi.alpha.phac.gc.ca"}
    ],
    "Ontario (ON)": [
        {"name": "Patient Browser", "url": "https://patient-browser.on.iidi.alpha.phac.gc.ca"},
        {"name": "HAPI FHIR Server", "url": "https://fhir.on.iidi.alpha.phac.gc.ca"},
        {"name": "Aggregator", "url": "https://aggregator.on.iidi.alpha.phac.gc.ca"}
    ]
}

# Define collapsible sections dynamically instead of hardcoding them in HTML
collapsible_sections = [
    {
        "title": "Synthetic Patient Data Generation",
        "content": """
            <h5><strong>Overview: What is Being Generated?</strong></h5>
            <p>
                The synthetic data mimics real-world immunization records from provincial registries while ensuring
                **FHIR-compliant JSON format** for interoperability. Differences between **BC and ON data models** are accounted for, 
                including variations in fields such as allergy tracking.
            </p>

            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px;">
                <h6><strong>FHIR Patient Resource Structure</strong></h6>
                <p>A **FHIR Patient Resource** consists of core fields and extensions, ensuring consistency across jurisdictions.</p>

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
                    <li>Allergy information is included using **FHIR `AllergyIntolerance` resource**.</li>
                    <li>Uses **SNOMED CT-coded allergy types**, severity levels, and reaction dates.</li>
                </ul>

                <p><strong>Ontario (ON) Specific Fields</strong></p>
                <ul style="margin-top: 5px; margin-bottom: 5px;">
                    <li>Ontario does **not** track allergy information in immunization records.</li>
                    <li>The script **skips allergy generation** for ON patients.</li>
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
                <li><strong>Synthetic but Realistic</strong>: Uses **Faker** for realistic patient data.</li>
                <li><strong>Handles Provincial Variations</strong>: BC and ON have different data models.</li>
                <li><strong>Includes Adverse Reactions & Exemptions</strong>: Adds realism for testing.</li>
            </ul>
        """
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
        """
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
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Date of immunization event.</td>
                        </tr>
                        <tr style="background-color: #f8f9fa;">
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Jurisdiction</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Province where the immunization was recorded (BC, ON).</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Age Group</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Categorized age ranges (e.g., 0-2 years, 3-5 years, etc.).</td>
                        </tr>
                        <tr style="background-color: #f8f9fa;">
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Gender</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Patient's gender (Male, Female, Other).</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Vaccine Type</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Type of vaccine administered (e.g., MMR).</td>
                        </tr>
                        <tr style="background-color: #f8f9fa;">
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Dose Count</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">Total doses given in the reporting period.</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px;">Total Patients Vaccinated</td>
                            <td style="padding: 8px;">Unique number of vaccinated individuals.</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <h6><strong>How Data Aggregation Works</strong></h6>
            <ol style="margin-top: 5px; margin-bottom: 5px; padding-left: 15px;">
                <li>Extract immunization records from FHIR repositories.</li>
                <li>Remove identifiable information (patient names, health card numbers, etc.).</li>
                <li>Categorize data by jurisdiction, age group, gender, and vaccine type.</li>
                <li>Summarize dose counts and calculate total vaccinated individuals.</li>
                <li>Apply privacy filtering to exclude small population counts (e.g., fewer than five patients per category).</li>
                <li>Format the final dataset into a structured report for PHAC analysis.</li>
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

            <h6>Key Components</h6>
            <ul>
                <li><strong>Provincial Immunization Systems</strong>: Each province maintains its own immunization data repository.</li>
                <li><strong>FHIR-Based Data Exchange</strong>: Standardized API interactions ensure compatibility between different systems.</li>
                <li><strong>Access Control Gateway</strong>: Manages authentication, authorization, and data access policies.</li>
                <li><strong>Interoperability Layer</strong>: Enables data transformation and validation to align different provincial data formats.</li>
                <li><strong>Audit & Compliance Framework</strong>: Ensures all data access is logged and follows regulatory requirements.</li>
            </ul>

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
        """
    },
    {
        "title": "Future Roadmap & Next Steps",
        "content": """
        <p>Upcoming developments and the roadmap for the Interoperable Immunization Data Initiative.</p>
        """
    }
]

@app.route('/')
def index():
    return render_template('index.html', entities=entities, collapsible_sections=collapsible_sections)

def check_health(url):
    """Helper function to check service health by making an HTTP request."""
    try:
        response = requests.get(url, timeout=5, allow_redirects=True)
        return response.status_code in (200, 302)  # Consider 200 and 302 as 'healthy'
    except requests.exceptions.RequestException:
        return None  # Any exception means service is unreachable

@app.route('/health-check/<province_name>')
def health_check(province_name):
    """Endpoint to check the health of services per province."""
    province_name = province_name.replace("%20", " ")
    
    if province_name in entities:
        province_health_status = {}
        for service in entities[province_name]:
            result = check_health(service['url'])
            health_status = "healthy" if result else "error" if result is None else "unhealthy"
            province_health_status[service['name']] = health_status
        
        return jsonify({province_name: province_health_status})
    
    return jsonify({"error": "Province not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
