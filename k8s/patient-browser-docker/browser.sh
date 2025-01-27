#!/bin/sh

# Log the configuration update process
echo "Starting Nginx configuration update script..."

# Update the FHIR server URL dynamically if PT is set
if [[ ! -z "$PT" ]]; then
    echo "Replacing default FHIR server URL with: https://fhir.$PT.iidi.alpha.phac.gc.ca/fhir"
    sed -i "s|http://localhost:8080/fhir|https://fhir.$PT.iidi.alpha.phac.gc.ca/fhir|g" /usr/share/nginx/html/config/default.json5
else
    echo "PT environment variable not set. Using default configuration."
fi

# Start Nginx
echo "Starting Nginx..."
nginx -g 'daemon off;'
