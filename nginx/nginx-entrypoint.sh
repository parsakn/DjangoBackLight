#!/bin/sh
# This script runs as part of nginx's docker-entrypoint.d hooks
# It automatically selects the appropriate nginx configuration based on SSL certificate availability

# Check if SSL certificates exist
if [ -f /etc/letsencrypt/live/node.lilms.top/fullchain.pem ]; then
    echo "SSL certificates found, using HTTPS configuration"
    # Copy HTTPS config to default.conf
    cp /etc/nginx/nginx-https.conf /etc/nginx/conf.d/default.conf
    # Remove init config to avoid conflicting server names
    rm -f /etc/nginx/conf.d/default-init.conf
else
    echo "SSL certificates not found, using initial HTTP-only configuration"
    # Copy init config as default
    cp /etc/nginx/conf.d/default-init.conf /etc/nginx/conf.d/default.conf
fi

