#!/bin/sh
# This script runs as part of nginx's docker-entrypoint.d hooks
# It automatically selects the appropriate nginx configuration based on SSL certificate availability

# Check if SSL certificates exist
if [ -f /etc/letsencrypt/live/node.lilms.top/fullchain.pem ]; then
    echo "SSL certificates found, using HTTPS configuration"
    cp /etc/nginx/nginx-https.conf /etc/nginx/conf.d/default.conf
else
    echo "SSL certificates not found, using initial HTTP-only configuration"
    cp /etc/nginx/nginx-init.conf /etc/nginx/conf.d/default.conf
fi

