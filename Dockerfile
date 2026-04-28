# syntax=docker/dockerfile:1

FROM node:22-alpine AS frontend-build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_PUBLISHABLE_KEY
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_PUBLISHABLE_KEY=$VITE_SUPABASE_PUBLISHABLE_KEY
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# PocketBase binary
COPY infra/pocketbase/pocketbase /usr/local/bin/pocketbase
RUN chmod +x /usr/local/bin/pocketbase

# Backend
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app

# Frontend static
COPY --from=frontend-build /app/dist ./static

# Supervisord runs both pocketbase + uvicorn
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*
COPY infra/supervisord.conf /etc/supervisor/conf.d/auditos.conf

EXPOSE 8000 8090
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/auditos.conf"]
