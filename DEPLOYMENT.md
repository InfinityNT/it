# IT Django Application - Server Deployment Guide

## Overview
This guide covers deploying the IT Django application to your production server with Traefik reverse proxy.

## Prerequisites
- Docker and Docker Compose installed on server
- Traefik already running (as shown in your main docker-compose.yml)
- Domain `it.emurh.com` pointing to your server

## Deployment Steps

### 1. On Your Server

Create the project directory:
```bash
mkdir -p ~/it
cd ~/it
```

### 2. Clone or Copy the Repository

```bash
# If using Git
git clone <your-repo-url> .

# Or copy files via SCP from your local machine
# scp -r /path/to/it user@server:~/it/
```

### 3. Create Environment File

```bash
# Copy the template
cp .env.server .env

# Generate a secure secret key
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Edit the .env file
nano .env
```

Add this content (replace SECRET_KEY with generated value):
```env
SECRET_KEY=your-generated-secret-key-from-above

# Optional: For first deployment to create admin user
AUTO_CREATE_SUPERUSER=true
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@emurh.com
DJANGO_SUPERUSER_PASSWORD=YourSecurePassword123!
```

### 4. Update Main docker-compose.yml

Add the IT service to your existing docker-compose.yml (or use docker-compose.server.yml):

```yaml
services:
  # ... your existing traefik, tms, redis, postgres services ...

  it:
    build: ./it
    container_name: it_django
    env_file:
      - ./it/.env
    environment:
      - DEBUG=0
      - DJANGO_ALLOWED_HOSTS=it.emurh.com,localhost,127.0.0.1
      - CSRF_TRUSTED_ORIGINS=https://it.emurh.com
      - SECURE_SSL_REDIRECT=True
      - SESSION_COOKIE_SECURE=True
      - CSRF_COOKIE_SECURE=True
    volumes:
      - it_database:/app/data
      - it_static:/app/staticfiles
      - it_media:/app/media
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.it-http.rule=Host(`it.emurh.com`)"
      - "traefik.http.routers.it-http.entrypoints=web"
      - "traefik.http.routers.it-http.middlewares=it-redirect"
      - "traefik.http.routers.it-https.rule=Host(`it.emurh.com`)"
      - "traefik.http.routers.it-https.entrypoints=websecure"
      - "traefik.http.routers.it-https.tls.certresolver=myresolver"
      - "traefik.http.routers.it-https.middlewares=it-headers"
      - "traefik.http.services.it.loadbalancer.server.port=8000"
      - "traefik.http.middlewares.it-redirect.redirectscheme.scheme=https"
      - "traefik.http.middlewares.it-redirect.redirectscheme.permanent=true"
      - "traefik.http.middlewares.it-headers.headers.frameDeny=true"
      - "traefik.http.middlewares.it-headers.headers.contentTypeNosniff=true"
      - "traefik.http.middlewares.it-headers.headers.browserXssFilter=true"
    expose:
      - "8000"
    restart: unless-stopped

volumes:
  # ... your existing volumes ...
  it_database:
  it_static:
  it_media:
```

### 5. Build and Deploy

```bash
# Build the image
docker-compose build it

# Start the container
docker-compose up -d it

# Check logs
docker-compose logs -f it
```

### 6. Verify Deployment

Check container status:
```bash
docker-compose ps it
```

Check logs for any errors:
```bash
docker-compose logs it --tail=100
```

Test the application:
```bash
# Should return HTTP 200
curl -I http://localhost:8000/admin/login/

# Or test via domain (after DNS propagates)
curl -I https://it.emurh.com/admin/login/
```

### 7. Access the Application

Open browser to: `https://it.emurh.com`

Login with the superuser credentials you set in .env

### 8. Post-Deployment Security

**IMPORTANT**: After first login, immediately:

1. Change the admin password via the web interface
2. Remove or comment out these lines from .env:
   ```env
   # AUTO_CREATE_SUPERUSER=true
   # DJANGO_SUPERUSER_USERNAME=admin
   # DJANGO_SUPERUSER_EMAIL=admin@emurh.com
   # DJANGO_SUPERUSER_PASSWORD=YourSecurePassword123!
   ```

3. Restart the container:
   ```bash
   docker-compose restart it
   ```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs it

# Check if port 8000 is available inside container
docker-compose exec it curl http://localhost:8000/admin/login/
```

### Permission Denied on entrypoint.sh
```bash
# Rebuild the image (permissions are set in Dockerfile)
docker-compose build --no-cache it
docker-compose up -d it
```

### Database Not Accessible
```bash
# Check if data directory has correct permissions
docker-compose exec it ls -la /app/data/

# Check database file
docker-compose exec it ls -la /app/db.sqlite3
```

### Static Files Not Loading
```bash
# Collect static files manually
docker-compose exec it python manage.py collectstatic --noinput --clear
```

### 502 Bad Gateway from Traefik
```bash
# Verify container is healthy
docker-compose ps it

# Check if Gunicorn is running
docker-compose exec it ps aux | grep gunicorn

# Verify port 8000 is exposed
docker-compose exec it netstat -tulpn | grep 8000
```

### CSRF Issues
Make sure `CSRF_TRUSTED_ORIGINS` includes your domain with https:// protocol:
```env
CSRF_TRUSTED_ORIGINS=https://it.emurh.com
```

## Maintenance

### View Logs
```bash
# Follow logs in real-time
docker-compose logs -f it

# Last 100 lines
docker-compose logs it --tail=100
```

### Restart Container
```bash
docker-compose restart it
```

### Update Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose build it
docker-compose up -d it
```

### Backup Database
```bash
# Copy database file from container
docker cp it_django:/app/db.sqlite3 ./backup-$(date +%Y%m%d).sqlite3
```

### Run Django Commands
```bash
# Create superuser
docker-compose exec it python manage.py createsuperuser

# Run migrations
docker-compose exec it python manage.py migrate

# Access Django shell
docker-compose exec it python manage.py shell

# Setup groups
docker-compose exec it python manage.py setup_groups
```

## Monitoring

### Health Check
The container includes a health check that tests `/admin/login/` every 30 seconds.

Check health status:
```bash
docker inspect it_django | grep Health -A 10
```

### Resource Usage
```bash
# Container stats
docker stats it_django

# Disk usage
docker system df
```

## Network Configuration

The IT application connects to Traefik via Docker networking:
- **Internal Port**: 8000 (Gunicorn)
- **External Access**: via Traefik (ports 80/443)
- **Protocol**: HTTP internally, HTTPS externally via Traefik

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | - | Django secret key |
| `DEBUG` | No | 0 | Debug mode (0=off, 1=on) |
| `DJANGO_ALLOWED_HOSTS` | No | it.emurh.com | Comma-separated hosts |
| `CSRF_TRUSTED_ORIGINS` | No | https://it.emurh.com | Comma-separated origins |
| `AUTO_CREATE_SUPERUSER` | No | false | Auto-create admin on startup |
| `DJANGO_SUPERUSER_USERNAME` | No | admin | Admin username |
| `DJANGO_SUPERUSER_EMAIL` | No | - | Admin email |
| `DJANGO_SUPERUSER_PASSWORD` | No | - | Admin password |
| `LOG_LEVEL` | No | INFO | Logging level |

## Files and Directories

```
/app/
├── db.sqlite3              # Database (if not using /app/data/)
├── data/                   # Persistent database directory
│   └── db.sqlite3         # Database file
├── staticfiles/           # Collected static files
├── media/                 # Uploaded media files
├── manage.py              # Django management
├── DMP/                   # Django project
└── entrypoint.sh          # Startup script
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs it`
2. Verify environment variables are set correctly
3. Check Traefik dashboard at: `http://your-server:8080` (if enabled)
4. Ensure domain DNS is pointing to your server
