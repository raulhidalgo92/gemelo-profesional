# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
FROM node:22-alpine AS base
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

# Desarrollo: servidor con recarga en caliente
FROM base AS desarrollo
ENV API_URL=http://backend:8000
EXPOSE 4200
CMD ["npx", "ng", "serve", "--host", "0.0.0.0", "--poll", "1000"]

# Compilación de producción
FROM base AS compilacion
RUN npx ng build --configuration production

# Producción: ficheros estáticos servidos por nginx
FROM nginx:1.27-alpine AS produccion
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=compilacion /app/dist/frontend/browser /usr/share/nginx/html
EXPOSE 80
