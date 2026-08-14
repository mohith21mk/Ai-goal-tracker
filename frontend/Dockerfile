# Multi-stage Dockerfile for React SPA with Vite & Nginx

# Stage 1: Build static assets
FROM node:20-alpine AS builder

WORKDIR /app

# Production: empty string means same-origin (nginx proxies /api to backend)
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Serve using Nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
