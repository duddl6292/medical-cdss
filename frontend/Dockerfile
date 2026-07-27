FROM node:24-alpine AS builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build


FROM nginx:1.29-alpine

COPY frontend/nginx/default.conf.template \
    /etc/nginx/templates/default.conf.template
COPY --from=builder /app/dist /usr/share/nginx/html

ENV PORT=8080
ENV BACKEND_ORIGIN=http://localhost:8000

EXPOSE 8080
