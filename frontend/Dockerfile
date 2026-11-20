# Shared Moments frontend for Cloud Run.
# Stage 1 builds the Vite app with Bun; stage 2 serves the static files with nginx on port 8080.

# Same Bun version as local development (bun.lock uses lockfile format v2)
FROM oven/bun:1.4.2-alpine AS build
WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile
COPY . .
RUN bun run build

FROM nginx:1.27-alpine
# The API service address; override with --set-env-vars API_HOST=... on Cloud Run
ENV API_HOST=shared-moments-api-894074329443.asia-south1.run.app
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
# Cloud Run sends traffic to $PORT, which is 8080 by default
EXPOSE 8080
