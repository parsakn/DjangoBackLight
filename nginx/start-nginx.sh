#!/bin/sh

# Wait for certificates to be available
if [ -f /etc/letsencrypt/live/node.lilms.top/fullchain.pem ]; then
    echo "SSL certificates found, using HTTPS configuration"
    # Copy the full nginx config
    cp /etc/nginx/templates/nginx-https.conf /etc/nginx/conf.d/default.conf
else
    echo "SSL certificates not found, using initial HTTP-only configuration"
    # Keep the initial config that allows certbot challenges
fi

# Start nginx
exec nginx -g "daemon off;"

