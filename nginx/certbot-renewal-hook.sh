#!/bin/sh
# Certbot post-renewal hook script
# This script runs after certbot successfully renews certificates
# 
# NOTE: This script runs inside the certbot container and cannot directly reload nginx.
# The certbot container doesn't have access to docker CLI by default for security reasons.
#
# Solutions:
# 1. Use the host-side cron job script: nginx/reload-nginx-after-renewal.sh (recommended)
# 2. Install docker CLI in certbot container (security risk, not recommended)
# 3. Use certbot's nginx plugin instead of webroot method
#
# The host-side script should be run daily via cron to check for renewals and reload nginx.

echo "Certificate renewed successfully!"
echo "Note: Nginx will be reloaded by the host-side cron job (see nginx/reload-nginx-after-renewal.sh)"
echo "Or reload manually: docker compose exec nginx nginx -s reload"
exit 0
