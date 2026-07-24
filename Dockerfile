FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html privacy.html terms.html icon.png social-card.png robots.txt sitemap.xml /usr/share/nginx/html/
RUN chmod 0555 /usr/share/nginx/html && chmod 0444 /usr/share/nginx/html/*
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
