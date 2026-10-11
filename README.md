# Madeni

Receivables assistant for small Kenyan suppliers: log who owes you, get a tone-matched
reminder (heads-up / gentle / firm / final) ready to send on WhatsApp, record payments,
and see who pays late.

```
python -m venv .venv && .venv\Scripts\pip install django
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py seed_demo      # optional demo data
.venv\Scripts\python manage.py runserver
```

Messages are sent manually via a wa.me link (no API costs, no WhatsApp Business approval).
Test: `python manage.py test`.
