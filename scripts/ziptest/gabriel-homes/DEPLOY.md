# DEPLOY.md — Gabriel Homes

Deployment guide for Gabriel Homes on a single Linux server (Ubuntu 22.04+).
Covers Nginx + Gunicorn + PostgreSQL + media storage + backups.

## 1. Server prerequisites

- Ubuntu 22.04 LTS (or later)
- 2 GB RAM minimum (4 GB recommended)
- Python 3.12
- PostgreSQL 15+
- Nginx
- Certbot (for Let's Encrypt SSL)

```bash
sudo apt update && sudo apt install -y python3.12 python3.12-venv python3-pip \
  postgresql postgresql-contrib nginx certbot python3-certbot-nginx
```

## 2. Database setup

```bash
sudo -u postgres psql <<'SQL'
CREATE USER gabriel WITH PASSWORD 'change-me';
CREATE DATABASE gabriel_homes OWNER gabriel;
SQL
```

## 3. Application user + directory

```bash
sudo useradd --system --create-home --shell /bin/bash gabriel
sudo mkdir -p /opt/gabriel-homes
sudo chown gabriel:gabriel /opt/gabriel-homes
```

## 4. Clone + install

```bash
sudo -u gabriel -H bash <<'BASH'
cd /opt/gabriel-homes
git clone <repo-url> .
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
BASH
```

## 5. Environment variables

Copy `.env.example` to `.env` and fill in production values:

```bash
sudo -u gabriel -H bash <<'BASH'
cd /opt/gabriel-homes
cp .env.example .env
# Generate a real secret key:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
BASH
```

Edit `.env`:

```
DJANGO_SETTINGS_MODULE=config.settings.prod
SECRET_KEY=<generated-50+-char-key>
DEBUG=False
ALLOWED_HOSTS=gabrielhomes.co.ke,www.gabrielhomes.co.ke
DATABASE_URL=postgres://gabriel:change-me@localhost:5432/gabriel_homes
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=hello@gabrielhomes.co.ke
SITE_DOMAIN=https://gabrielhomes.co.ke
SECURE_SSL_REDIRECT=True
```

## 6. Migrate + collect static + seed

```bash
sudo -u gabriel -H bash <<'BASH'
cd /opt/gabriel-homes
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_demo --no-images --target=80  # optional: seed demo data
python manage.py createsuperuser
BASH
```

## 7. Gunicorn systemd service

Create `/etc/systemd/system/gabriel-homes.service`:

```ini
[Unit]
Description=Gabriel Homes Gunicorn
After=network.target

[Service]
Type=notify
User=gabriel
Group=www-data
WorkingDirectory=/opt/gabriel-homes
EnvironmentFile=/opt/gabriel-homes/.env
ExecStart=/opt/gabriel-homes/.venv/bin/gunicorn \
  --workers 3 \
  --bind unix:/opt/gabriel-homes/gabriel-homes.sock \
  --access-logfile - \
  --error-logfile - \
  config.wsgi:application
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable gabriel-homes
sudo systemctl start gabriel-homes
sudo systemctl status gabriel-homes
```

## 8. Nginx config

Create `/etc/nginx/sites-available/gabriel-homes`:

```nginx
server {
    listen 80;
    server_name gabrielhomes.co.ke www.gabrielhomes.co.ke;

    # Redirect to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name gabrielhomes.co.ke www.gabrielhomes.co.ke;

    # SSL certs (via Certbot)
    ssl_certificate /etc/letsencrypt/live/gabrielhomes.co.ke/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/gabrielhomes.co.ke/privkey.pem;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Static files (WhiteNoise handles compression + hashing)
    location /static/ {
        alias /opt/gabriel-homes/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files (user uploads)
    location /media/ {
        alias /opt/gabriel-homes/media/;
        expires 7d;
    }

    # Gunicorn
    location / {
        proxy_pass http://unix:/opt/gabriel-homes/gabriel-homes.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/gabriel-homes /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d gabrielhomes.co.ke -d www.gabrielhomes.co.ke
```

## 9. Backups

### Database backup (daily cron)

Create `/opt/gabriel-homes/scripts/backup-db.sh`:

```bash
#!/bin/bash
set -euo pipefail
BACKUP_DIR=/opt/gabriel-homes/backups
mkdir -p "$BACKUP_DIR"
DATE=$(date +%Y%m%d-%H%M%S)
pg_dump -U gabriel -h localhost gabriel_homes | gzip > "$BACKUP_DIR/gabriel-homes-$DATE.sql.gz"
# Keep last 30 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete
```

```bash
sudo chmod +x /opt/gabriel-homes/scripts/backup-db.sh
sudo crontab -e -u gabriel
# Add:
0 3 * * * /opt/gabriel-homes/scripts/backup-db.sh
```

### Media backup (weekly)

```bash
0 4 * * 0 tar czf /opt/gabriel-homes/backups/media-$(date +\%Y\%m\%d).tar.gz /opt/gabriel-homes/media/
```

### Off-site backup (recommended)

Sync backups to S3 / Backblaze B2 / rsync.net:

```bash
0 5 * * * aws s3 sync /opt/gabriel-homes/backups s3://gabriel-homes-backups/ --delete
```

## 10. Deploy checklist

Before each deploy:

- [ ] `python manage.py check` passes
- [ ] `python manage.py check --deploy` passes (0 warnings)
- [ ] `python manage.py makemigrations --check --dry-run` reports "No changes"
- [ ] `pytest -q` passes
- [ ] `.env` has the correct `ALLOWED_HOSTS` + `SECRET_KEY`
- [ ] `DEBUG=False` in `.env`

Deploy steps:

```bash
sudo -u gabriel -H bash <<'BASH'
cd /opt/gabriel-homes
git pull
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
BASH
sudo systemctl restart gabriel-homes
```

## 11. Monitoring

```bash
# Check Gunicorn
sudo systemctl status gabriel-homes
sudo journalctl -u gabriel-homes -f

# Check Nginx
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log

# Check the site
curl -I https://gabrielhomes.co.ke/
curl -I https://gabrielhomes.co.ke/sitemap.xml
curl -I https://gabrielhomes.co.ke/robots.txt
```

## 12. Troubleshooting

### Gunicorn won't start
- Check the socket: `ls -la /opt/gabriel-homes/gabriel-homes.sock`
- Check permissions: the `www-data` group needs access to the socket dir
- Check the journal: `sudo journalctl -u gabriel-homes -n 50`

### 502 Bad Gateway
- Gunicorn isn't running: `sudo systemctl status gabriel-homes`
- Socket path mismatch between Nginx and systemd

### Static files 404
- Run `python manage.py collectstatic --noinput`
- Check `STATIC_ROOT` in `.env` matches the Nginx alias

### Media files 404
- Check `MEDIA_ROOT` in `.env`
- Check Nginx `location /media/` alias
- Check file permissions on the media dir

### Database connection
- `psql -U gabriel -h localhost gabriel_homes`
- Check `DATABASE_URL` in `.env`
- Check `pg_hba.conf` allows the `gabriel` user
