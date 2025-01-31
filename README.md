# Interoperable Immunization Data Initiative (IIDI)

## One-liner summary

TODO

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
      - not yet implemented
    - http://localhost:8080/fed/shiny-dashboard
      - not yet implemented
