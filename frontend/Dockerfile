# NeuroShield Frontend - Docker Container
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --silent
COPY . .
RUN npm run build

# Production stage using nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html

# nginx config: proxy /api/* → Flask backend
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
