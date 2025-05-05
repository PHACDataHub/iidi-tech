# Migration Testing Checklist

## End to end functionality of deployed components

High level spot checks to confirm services exist and can communicate with eachother as expected. This checklist is a procedure for testing deployed's infrastructure and high level configuration, not the implementation of buisness logic or other low level details.

### Demo Portal

Note: for steps mentioning existance and functionality of any links, don't require that the services behind the links work for these checks to pass, just that the links are valid and in-sync with the configured locations of the relevant serivces.

- [ ] portal is accessible at the configured location
- [ ] Federal section exists and has functional links to the
  - [ ] R-Shiny Dashboard
  - [ ] Federator API
- [ ] B.C. and ON section exits, and have links to their respective
  - [ ] Patient Browser
  - [ ] FHIR Server
  - [ ] Patient Transfer Dashboard
- [ ] (optional) if all other services are in known-good states, the status indicator circles on the left of each of the three sections should be green

### FHIR Server + synthetic records + Patient Browser

For each of the provinces found on the Demo Portal:

- [ ] open the FHIR Server's web interface. You should be on the `/home` route and under "Resources" on the left hand side you should see non-zero counts displayed for the following resource types
  - [ ] `Patient`
  - [ ] `Immunization`
  - [ ] `AllergyIntolerance`(O.N only\*)
    - \*unless transfers from O.N. to BC have been performed, in which case B.C. will have the `AllergyIntolerance` records of the transfered patients
- [ ] from the Demo Portal, open the Patient Browser of the same province and confirm that there is a non-zero number of viewable records
- [ ] on the Patient Browser, to confirm that it's connecting to the expected FHIR server, pick a random patient record and
  1. note the patient's `ID` value
  2. in another tab, return to the corresponding FHIR server and replace `/home` in the address bar with `/fhir/Patient/{ID}`, substituting `{ID}` for the ID from the previous step
  3. confirm that the raw data viewed on the FHIR server matches the summary displayed in the Patient Browser

### UJ1: PT to PT transfer

Dependent on FHIR Server + synthetic records, testing procedure supported by the Patient Browser

For each of the provinces found on the Demo Portal:

- [ ] open the province's Patient Transfer Dashboard. Confirm that it loads and that the page's title contains the correct province's name
- [ ] select a patient to transfer in following steps. You can use the province's Patient Browser to quickly pick one
- [ ] on the Patient Browser, to confirm that it's connecting to the expected FHIR server, pick a random patient record and
  1. note the patient's `ID` value
  2. in another tab, return to the corresponding FHIR server and replace `/home` in the address bar with `/fhir/Patient/{ID}`, substituting `{ID}` for the ID from the previous step
  3. confirm that the patient record does not have `"active": false` and any `"link"` values with `"type": "replaced-by"`. If it does then this record has been transfered already, pick another
- [ ] return to the province's Transfer Dashboard and initiate a transfer for the selected `ID`
- [ ] confirm that a success notice is displayed containing the transfer job ID for the transfer request
- [ ] continue to refresh the Transfer Request table until the corresponding Transfer Status column is "Success"
- [ ] note the "Patient ID in receiving system" value in the corresponding Result column
- [ ] on the current province's FHIR server, using the original patient `ID`, return to `/fhir/Patient/{ID}` and confirm that the record now has `"active": false` and a `"link"` value with `"type": "replaced-by"`
- [ ] on the **receiving province's** FHIR server, using the new ID providied in the Transfer Dashboard's Transfer Requests table's Result column, visit `/fhir/Patient/{new ID}` and confirm that the information matches the record from the originating FHIR server

### UJ2: PT to PHAC federation

Dependent on FHIR Server + synthetic records

- [ ] from the Demo Portal, open the Federal Dashboard link, confirm it loads and has data
- [ ] to spot check the data, record the displayed "Total Immunizations" value. Confirm that this is equal to the sum of the `Patient` record counts found on each province's FHIR Server homepage

## CI/CD Capabilities & Cluster Behaviour

### Existence, configuration, and functionality of cloudbuild triggers

Expect to exist in an IIDI specific project, separate from the multi-tenant cluster's project? Make sure they can push to the appropriate artifact registry (probably in the IIDI project, but possibly the tenant cluster?).

- for every following cloud build file
  - [ ] trigger exists
  - [ ] triggers on "push to branch"
  - [ ] trigger sends logs to GitHub
  - [ ] trigger has a file filter scoped to its file's parent directory
- [ ] /cloudbuild.yaml
- [ ] /aggregator/cloudbuild.yaml
- [ ] /demo-portal/cloudbuild.yaml
- [ ] /demo-transfer-dashboard/cloudbuild.yaml
- [ ] /federator/cloudbuild.yaml
- [ ] /patient-browser/cloudbuild.yaml
- [ ] /rshiny-dashboard/cloudbuild.yaml
- [ ] /synthesizer/cloudbuild.yaml
- [ ] /transfer-outbund/cloudbuild.yaml
- [ ] /transfer-inbound/cloudbuild.yaml
- [ ] /transfer-outbund/cloudbuild.yaml

### Continuous deployment

Likely transitioning from Flux to ArgoCD. At a high level, require that

- [ ] syncs the cluster against changes in the repo's `/k8s` directory, when committed to main
- [ ] reflects image tag updates to cluster manifests for new container images pushed to the appropriate artifact registry

Or equivalent, if there's a change in our practices (e.g. using fixed tags like "latest" for images to deploy, which bypasses the need for the second functionality).
