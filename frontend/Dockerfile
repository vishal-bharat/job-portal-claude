# ---------- Build stage ----------
FROM node:20-alpine AS build
WORKDIR /app

# Allow the API URL to be set at build time
ARG VITE_API_URL=http://localhost:8080
ENV VITE_API_URL=$VITE_API_URL

COPY package.json ./
# package-lock is optional; use install (not ci) so first build works without one
RUN npm install --no-audit --no-fund

COPY . .
RUN npm run build

# ---------- Runtime stage ----------
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
