# Frontend Dockerfile

# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund

# Copy source and build
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

ENV FRONTEND_PORT=5274 \
    BACKEND_HOST=backend \
    BACKEND_PORT=8050

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx template (rendered by nginx entrypoint with env vars)
COPY nginx.conf /etc/nginx/templates/default.conf.template

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
