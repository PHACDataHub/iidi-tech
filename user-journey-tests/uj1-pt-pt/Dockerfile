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

# Use a non-root user for security
USER node

# Start the application
CMD ["npm", "run", "test:integration"]
