# First stage: Build the project
FROM node:16-alpine AS build

# Install required tools
RUN apk add --no-cache git

# Set working directory
WORKDIR /app

# Clone the repository
RUN git clone --depth=1 https://github.com/smart-on-fhir/patient-browser.git .

# Copy configuration file from the host
COPY ./default.json5 .

# Install dependencies and build the project
RUN npm install colors request commander@2.15.1 && \
    npm ci && \
    NODE_ENV=production npm run build

# Move configuration file to the build directory
RUN mv default.json5 ./dist/config/

# Second stage: Set up Nginx for serving the app
FROM nginx:alpine

# Copy the built application from the previous stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy the runtime configuration script
COPY ./browser.sh /

# Entrypoint to handle configuration and start the server
CMD ["/browser.sh"]
