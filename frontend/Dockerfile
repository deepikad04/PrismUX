FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
# Local dev uses static nginx.conf; Cloud Run uses template with envsubst
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80

# If BACKEND_URL is set (Cloud Run), envsubst rewrites the config at startup.
# Otherwise falls back to the static nginx.conf (docker-compose local dev).
CMD ["/bin/sh", "-c", "if [ -n \"$BACKEND_URL\" ]; then envsubst '${BACKEND_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf; fi && nginx -g 'daemon off;'"]
