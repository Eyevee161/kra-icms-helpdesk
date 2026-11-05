# KRA ICMS Help Desk — Ticketing System (MVP)

Simple Django prototype for handling taxpayer complaints related to the Kenya Revenue Authority Integrated Customs Management System (ICMS).

## Features

- **Public**
  - Submit complaint (with optional file attachment)
  - Track ticket status by ticket number + email
  - View ticket details and public updates

- **Staff / Admin**
  - Dashboard with key metrics
  - Ticket list with filters (status, assignee, search)
  - Assign tickets to agents
  - Change status & priority
  - Internal notes + public comments
  - Ticket history log
  - Basic reports & analytics
  - Full Django Admin interface

- **Notifications**
  - Confirmation email on ticket submission (console backend in MVP)

## Quick Start

```bash
cd kra_icms_helpdesk
# Ensure Django is installed: pip install django pillow
python manage.py migrate          # if needed
python manage.py runserver 0.0.0.0:8000
```

Open http://127.0.0.1:8000

### Default Accounts

| Username | Password  | Role          |
|----------|-----------|---------------|
| admin    | admin123  | Superuser     |
| agent1   | agent123  | Staff agent   |

## Ticket Number Format

`KRA-ICMS-YYYYMMDD-XXXX` (e.g. `KRA-ICMS-20261102-0001`)

## Project Structure

```
kra_icms_helpdesk/
├── config/          # Django project settings & urls
├── tickets/         # Main app (models, views, forms, admin)
├── templates/       # Bootstrap 5 templates
├── media/           # Uploaded attachments
├── manage.py
└── README.md
```

## Production Notes (beyond MVP)

- Switch `EMAIL_BACKEND` to SMTP (or use a service like SendGrid)
- Add real SMS gateway (Africa's Talking, Twilio, etc.) for Kenya
- Use PostgreSQL instead of SQLite
- Add authentication for taxpayers (iTax / eCitizen integration)
- Add rate limiting, CAPTCHA on public form
- Deploy behind HTTPS with proper `ALLOWED_HOSTS` and `SECRET_KEY`
- Consider Celery for async notifications

## Categories Seeded

- Customs Declaration Issues
- Payment & Receipts
- System Access / Login
- Cargo Release / Clearance
- Tariff / Classification
- Bond & Guarantees
- Other / General Enquiry

---
**Disclaimer:** This is a demonstration MVP prototype only. Not connected to any official KRA systems.
