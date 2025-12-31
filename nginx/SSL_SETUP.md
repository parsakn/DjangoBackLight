# SSL/HTTPS Setup Guide

This guide explains how to set up SSL certificates using Let's Encrypt and configure nginx for HTTPS.

## Prerequisites

1. Your domain `node.lilms.top` must point to your server's IP address
2. Ports 80 and 443 must be open in your firewall
3. Docker and Docker Compose must be installed

## Initial Setup

1. **Start the services with the initial nginx configuration:**
   ```bash
   docker compose up -d
   ```

2. **Edit the SSL initialization script** (if needed):
   - Open `nginx/init-letsencrypt.sh`
   - Update the `domains` array if your domain is different
   - Optionally set the `email` variable for Let's Encrypt notifications
   - Set `staging=0` for production certificates (use `staging=1` for testing)

3. **Run the SSL initialization script:**
   ```bash
   ./nginx/init-letsencrypt.sh
   ```

   This script will:
   - Create dummy SSL certificates so nginx can start
   - Start nginx with HTTP-only configuration
   - Request real certificates from Let's Encrypt
   - Switch nginx to HTTPS configuration
   - Reload nginx

## What Happens

1. **Initial State**: nginx starts with `nginx-init.conf` which:
   - Listens on port 80
   - Allows Let's Encrypt challenges at `/.well-known/acme-challenge/`
   - Returns 503 for other requests

2. **After Certificate Generation**: The script switches to `nginx-https.conf` which:
   - Redirects HTTP (port 80) to HTTPS (port 443)
   - Serves HTTPS with SSL certificates
   - Proxies requests to backend and frontend services

## Certificate Renewal

Certificates are automatically renewed by the `certbot` service in docker-compose.yml. It runs every 12 hours and renews certificates when they're within 30 days of expiration.

## Manual Certificate Renewal

If you need to manually renew certificates:

```bash
docker compose run --rm certbot renew
docker compose exec nginx nginx -s reload
```

## Troubleshooting

### Check nginx logs:
```bash
docker compose logs nginx
```

### Check certbot logs:
```bash
docker compose logs certbot
```

### Test nginx configuration:
```bash
docker compose exec nginx nginx -t
```

### Restart services:
```bash
docker compose restart nginx
```

## Configuration Files

- `nginx/nginx-init.conf`: Initial HTTP-only config for certificate generation
- `nginx/nginx-https.conf`: Full HTTPS configuration (used after certificates are obtained)
- `nginx/nginx-http-includes.conf`: HTTP-level directives (rate limiting, upstreams)
- `nginx/init-letsencrypt.sh`: SSL certificate initialization script

## Security Notes

- SSL certificates are stored in Docker volumes (`certbot-conf` and `certbot-www`)
- The nginx configuration includes security headers (HSTS, X-Frame-Options, etc.)
- Rate limiting is configured for API endpoints
- HTTPS is enforced in production (when `DEBUG=False` in Django settings)

