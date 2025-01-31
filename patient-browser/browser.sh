#!/bin/sh

# Log the configuration update process
echo "Starting Nginx configuration update script..."

# TODO: this provices support for previous script behaviour where the old PT env var is set and
# the new FHIR_URL env var isn't. Delete this case statement once the K8s deployments have been
# updated to only use FHIR_URL
if [[ -z "$FHIR_URL" && ! -z "$PT" ]]; then
  FHIR_URL="https://fhir.${PT}.iidi.alpha.phac.gc.ca/fhir"
fi

# Update the FHIR server URL dynamically if FHIR_URL is set
default_url=http://localhost:8080/fhir
if [[ ! -z "$FHIR_URL" ]]; then
    echo "Replacing default FHIR server URL with: ${FHIR_URL}"
    sed -i "s|${default_url}|${FHIR_URL}|g" /usr/share/nginx/html/config/default.json5
else
    echo "FHIR_URL environment variable not set. Using default server URL (${default_url})."
fi

# Start Nginx
echo "Starting Nginx..."
nginx -g 'daemon off;'
