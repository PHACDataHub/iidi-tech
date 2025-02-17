#!/bin/sh

# Log the configuration update process
echo "Starting Nginx configuration update script..."

# Default FHIR URL inside Nginx app
DEFAULT_URL="http://localhost:8080/fhir"

# Check if FHIR_URL is set, otherwise use the default
if [ -n "$FHIR_URL" ]; then
    echo "Replacing default FHIR server URL with: ${FHIR_URL}"
    sed -i "s|${DEFAULT_URL}|${FHIR_URL}|g" /usr/share/nginx/html/config/default.json5
else
    echo "FHIR_URL environment variable not set. Using default server URL (${DEFAULT_URL})."
fi

# Start Nginx
echo "Starting Nginx..."
exec nginx -g 'daemon off;'