# Federal API Federation Server

## Endpoints

- GET `/aggregated-data`
  - sends a request to the `/aggregated-data` endpoint of each URL in `AGGREGATOR_URLS` envrionment variable
  - response is of type of `application/json` and has the form `{ data, errors }` where
    - `data` is a flattened array of all data returned across the PT endpoints
    - `errors` is an array of error messages corresponding to not-ok responses from any PT aggregators
  - has status `200` if `errors` is empty, `500` if any errors exist
