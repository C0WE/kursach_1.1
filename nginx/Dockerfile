FROM nginx:alpine

COPY conf.d/default.conf /etc/nginx/conf.d/default.conf
COPY ssl/ /etc/nginx/ssl/

EXPOSE 80 443

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
