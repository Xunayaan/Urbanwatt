FROM nginx:1.27-alpine

# Configuration nginx : fichiers statiques + proxy /api -> conteneur "api"
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Interface (HTML / CSS / JS : aucune étape de build)
COPY index.html /usr/share/nginx/html/index.html
COPY css /usr/share/nginx/html/css
COPY js /usr/share/nginx/html/js

EXPOSE 80
