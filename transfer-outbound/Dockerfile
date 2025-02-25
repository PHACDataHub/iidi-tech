FROM node:22-alpine3.21

ENV NODE_ENV production

WORKDIR /app

COPY . .
RUN npm ci

USER root
RUN apk add --no-cache redis

USER node

CMD ["npm", "--no-update-notifier", "start"]