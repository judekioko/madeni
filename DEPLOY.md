# Deploying Madeni (cPanel Python app)

1. cPanel -> Setup Python App: Python 3.11+, app root = the cloned repo, startup file `passenger_wsgi.py`,
   entry point `application`. Pick a domain/subdomain (e.g. madeni.example.com).
2. In the app's virtualenv: `pip install -r requirements.txt`.
3. Environment variables (Setup Python App -> Environment variables):
   - `MADENI_SECRET_KEY` = long random string (`python -c "import secrets;print(secrets.token_urlsafe(60))"`)
   - `MADENI_DEBUG` = `0`
   - `MADENI_HOSTS` = your domain, e.g. `madeni.example.com`
   - `MADENI_SITE_URL` = `https://madeni.example.com`
   - `MADENI_DB` = absolute path outside the code folder, e.g. `/home/USER/madeni-data/db.sqlite3`
   - Email (for the daily summary): `MADENI_EMAIL_HOST`, `MADENI_EMAIL_PORT`, `MADENI_EMAIL_USER`, `MADENI_EMAIL_PASSWORD`, `MADENI_FROM`
4. Run once: `python manage.py migrate && python manage.py collectstatic --noinput`, then restart the app.
5. Daily summary cron (cPanel -> Cron Jobs), 7:00 Nairobi = `0 4 * * *` on a UTC server:
   `cd /home/USER/madeni && /home/USER/virtualenv/madeni/3.11/bin/python manage.py send_summary`
6. Back up the SQLite file (`MADENI_DB`) with your normal cPanel backups.
