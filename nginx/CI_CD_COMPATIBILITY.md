# CI/CD Pipeline Compatibility with SSL/HTTPS Setup

## Overview

The SSL/HTTPS setup is fully compatible with your existing CI/CD pipeline. Here's what was done to ensure compatibility:

## Changes Made

### 1. **Automatic Configuration Detection**
   - Added `nginx-entrypoint.sh` script that automatically detects SSL certificates
   - Nginx will use HTTP-only config initially, then switch to HTTPS config when certificates are available
   - This happens automatically on container startup, so no manual intervention needed after first SSL setup

### 2. **Volume Persistence**
   - SSL certificates are stored in Docker volumes (`certbot-conf` and `certbot-www`)
   - These volumes persist across deployments, so certificates won't be lost when containers are recreated
   - The `--force-recreate` flag in CI/CD is safe to use

### 3. **Updated CI/CD Pipeline**
   - Modified `.github/workflows/ci-cd.yml` to handle nginx properly
   - Added nginx reload step to pick up configuration changes
   - Added reminder message about SSL setup for first-time deployments

## Deployment Flow

### First Deployment (No SSL Yet)
1. CI/CD pipeline deploys all services
2. Nginx starts with HTTP-only configuration (`nginx-init.conf`)
3. Site is accessible via HTTP only
4. **Manual step required**: Run `./nginx/init-letsencrypt.sh` on the server to obtain SSL certificates
5. After SSL setup, nginx will automatically use HTTPS config on next restart

### Subsequent Deployments (SSL Already Configured)
1. CI/CD pipeline pulls latest images
2. Runs `docker compose up -d --force-recreate`
3. Nginx container restarts
4. `nginx-entrypoint.sh` detects SSL certificates exist
5. Automatically switches to HTTPS configuration
6. Nginx reloads to apply changes
7. Site continues to work with HTTPS

## Important Notes

### First-Time SSL Setup
After the first deployment, you **must** run the SSL initialization script manually:
```bash
./nginx/init-letsencrypt.sh
```

This is a one-time setup. After that, the CI/CD pipeline will handle everything automatically.

### Certificate Renewal
- Certbot service runs automatically in the background
- Certificates are renewed every 12 hours (when within 30 days of expiration)
- No action needed from CI/CD pipeline

### Volume Management
- SSL certificates are stored in persistent Docker volumes
- These volumes are **not** removed by `docker compose up -d --force-recreate`
- To completely reset SSL (not recommended), you would need to manually remove volumes:
  ```bash
  docker compose down -v  # WARNING: This removes ALL volumes including data
  ```

## Testing the Setup

### Verify SSL is Working
After deployment, check:
```bash
# Check if nginx is using HTTPS config
docker compose exec nginx cat /etc/nginx/conf.d/default.conf | grep ssl_certificate

# Check SSL certificate expiration
docker compose exec certbot certbot certificates

# Test HTTPS connection
curl -I https://node.lilms.top
```

### Check CI/CD Deployment
The pipeline will show:
- All containers starting successfully
- Nginx reload message (or skip message if not running yet)
- Reminder about SSL setup if certificates don't exist

## Troubleshooting

### Nginx Fails to Start
- Check if SSL certificates exist but nginx-https.conf has errors
- Verify volumes are mounted correctly: `docker compose exec nginx ls -la /etc/letsencrypt/live/`

### SSL Not Working After Deployment
- Ensure certificates exist: `docker compose exec nginx test -f /etc/letsencrypt/live/node.lilms.top/fullchain.pem`
- Check nginx config: `docker compose exec nginx nginx -t`
- Restart nginx: `docker compose restart nginx`

### CI/CD Deployment Fails
- Check if nginx directory exists on server
- Verify file permissions on nginx config files
- Check docker compose logs: `docker compose logs nginx`

## Summary

✅ **Fully Compatible**: The SSL setup works seamlessly with your existing CI/CD pipeline  
✅ **Automatic**: Nginx automatically detects and uses SSL certificates  
✅ **Persistent**: Certificates survive container recreations  
✅ **Zero Downtime**: Deployments don't interrupt SSL functionality  

The only manual step is the initial SSL certificate setup, which is a one-time operation.

