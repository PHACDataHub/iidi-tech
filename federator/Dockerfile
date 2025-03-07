FROM node:22-alpine3.21

# Set environment to production
ENV NODE_ENV=production

# Set working directory
WORKDIR /app

# Copy package files first to leverage caching
COPY package.json package-lock.json ./

# Install dependencies securely
RUN npm ci --omit=dev

# Copy the rest of the application files
COPY . .

# Ensure the /secrets directory exists for the private key
RUN mkdir -p /secrets && chown -R node /secrets

# Use a non-root user for security
USER node

# Set an environment variable for the private key location
ENV PRIVATE_KEY_PATH="/secrets/private_key.pem"

# Start the application
CMD ["npm", "--no-update-notifier", "start"]
