#!/bin/bash
# Host-side script to reload nginx after certificate renewal
# This script should be run as a cron job on the host system
# 
# Add to crontab (runs daily at 3 AM):
# 0 3 * * * cd /path/to/DjangoBackLight && ./nginx/reload-nginx-after-renewal.sh >> /var/log/nginx-renewal.log 2>&1
#
# This script safely reloads nginx. It's safe to run even if certificates weren't renewed,
# as nginx reload is non-blocking and only reloads configuration if it's valid.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(dirname "$SCRIPT_DIR")"

cd "$COMPOSE_DIR" || exit 1

# Reload nginx to pick up any renewed certificates
# This is safe to run even if certificates weren't renewed
echo "$(date): Checking for certificate renewals and reloading nginx..."

if docker compose ps nginx | grep -q "Up"; then
    docker compose exec -T nginx nginx -s reload 2>/dev/null && {
        echo "Nginx reloaded successfully"
        exit 0
    } || {
        echo "Warning: Failed to reload nginx (may not be running or config error)"
        exit 1
    }
else
    echo "Nginx container is not running, skipping reload"
    exit 0
fi

