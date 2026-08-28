# Create production frontend Dockerfile
$frontendProd = @"
# Stage 1: Build
FROM node:20-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Nginx Serve
FROM nginx:alpine
# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html
# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"@
Set-Content -Path frontend\Dockerfile.prod -Value $frontendProd

# Create Nginx config for frontend (Proxies API too)
$nginxConf = @"
server {
    listen 80;
    server_name _;

    # Serve static frontend files
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files `$uri `$uri/ /index.html;
    }

    # Proxy API requests to FastAPI backend
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto `$scheme;
    }

    location /health {
        proxy_pass http://backend:8000/health;
        proxy_set_header Host `$host;
    }
}
"@
Set-Content -Path frontend\nginx.conf -Value $nginxConf

# Create production docker-compose
$dockerComposeProd = @"
services:
  db:
    image: postgis/postgis:16-3.4
    restart: always
    env_file: .env
    volumes:
      - pgdata_prod:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U heatwave -d heatwave_ews"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    env_file: .env
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    restart: always
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  pgdata_prod:
"@
Set-Content -Path docker-compose.prod.yml -Value $dockerComposeProd

print("Production config files created!")
