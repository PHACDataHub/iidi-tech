FROM node:22-alpine3.21

ENV NODE_ENV production

WORKDIR /app

COPY . .
RUN npm ci

USER node

CMD npm --no-update-notifier start
