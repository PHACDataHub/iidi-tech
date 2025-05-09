# 1. Building static react app
FROM node:22-alpine3.21 AS build

WORKDIR /app

COPY package.json /app/package.json
COPY package-lock.json /app/package-lock.json
RUN npm ci

COPY . /app

# These env vars need to exist at build-time, setting them on the container at run-time doesn't change
# the values in the static content generated here and served when the container is run
ARG ON_OUTBOUND_URL="https://transfer-outbound.on.iidi.alpha.phac.gc.ca"
ARG BC_OUTBOUND_URL="https://transfer-outbound.bc.iidi.alpha.phac.gc.ca"

RUN npm run build

# 2. Serve static app via nginx
FROM docker.io/library/nginx:1.27.3

RUN chown -R 1000:1000 /var/cache/nginx /var/run/ 

# Copy config nginx
COPY --from=build /app/.nginx/nginx.conf /etc/nginx/conf.d/default.conf

WORKDIR /usr/share/nginx/html

# Remove default nginx static assets
RUN rm -rf ./*

# Copy static assets from builder stage
COPY --from=build /app/dist .

USER 1000
EXPOSE 3000

# Containers run nginx with global directives and daemon off
ENTRYPOINT ["nginx", "-g", "daemon off;"]