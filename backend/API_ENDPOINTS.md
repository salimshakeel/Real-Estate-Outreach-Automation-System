# API Endpoints Reference

**Total Endpoints: 35**  
**Base URL:** `http://localhost:8000`  
**Docs:** `http://localhost:8000/docs`

---

## Health Check (3 endpoints)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Root - API welcome message |
| GET | `/health` | Health check - server status |
| GET | `/config` | Config info - app settings (non-sensitive) |

---

## Leads (7 endpoints)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/leads/upload` | Upload CSV file with leads |
| GET | `/api/leads` | List all leads (paginated) |
| GET | `/api/leads/{id}` | Get single lead with history |
| POST | `/api/leads` | Create one lead manually |
| PUT | `/api/leads/{id}` | Update lead details |
| DELETE | `/api/leads/{id}` | Delete lead (cascades) |
| GET | `/api/leads/template/csv` | Download sample CSV template |

---

## Templates (8 endpoints)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/templates` | Create new email template |
| GET | `/api/templates` | List all templates |
| GET | `/api/templates/{id}` | Get single template |
| GET | `/api/templates/default/active` | Get default template |
| PUT | `/api/templates/{id}` | Update template |
| DELETE | `/api/templates/{id}` | Delete template |
| POST | `/api/templates/{id}/preview` | Preview with sample data |
| POST | `/api/templates/seed/defaults` | Create 3 default templates |

---

## Campaigns (11 endpoints)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/campaigns` | Create new campaign (draft) |
| GET | `/api/campaigns` | List all campaigns |
| GET | `/api/campaigns/{id}` | Get campaign with stats |
| PUT | `/api/campaigns/{id}` | Update campaign details |
| DELETE | `/api/campaigns/{id}` | Delete campaign |
| POST | `/api/campaigns/{id}/start` | Start campaign - send emails |
| POST | `/api/campaigns/{id}/pause` | Pause active campaign |
| POST | `/api/campaigns/{id}/resume` | Resume paused campaign |
| POST | `/api/campaigns/{id}/complete` | Mark campaign completed |
| GET | `/api/campaigns/{id}/emails` | View emails sent in campaign |
| POST | `/api/campaigns/quick-start` | Create + start in one call |

---

## Dashboard (6 endpoints)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/dashboard` | Full dashboard (stats + funnel + activity) |
| GET | `/api/dashboard/stats` | Statistics only |
| GET | `/api/dashboard/funnel` | Lead funnel counts |
| GET | `/api/dashboard/activity` | Recent activity feed |
| GET | `/api/dashboard/campaigns` | Campaigns overview |
| GET | `/api/dashboard/quick` | Lightweight quick stats |

---

## Quick Reference by Action

### Upload & Import
- `POST /api/leads/upload` - Import leads from CSV

### View Data
- `GET /api/leads` - All leads
- `GET /api/templates` - All templates
- `GET /api/campaigns` - All campaigns
- `GET /api/dashboard` - Full stats

### Send Emails
- `POST /api/campaigns/{id}/start` - Send to selected leads
- `POST /api/campaigns/quick-start` - One-step send

### Track Progress
- `GET /api/dashboard/funnel` - Lead progression
- `GET /api/dashboard/activity` - Recent actions
- `GET /api/campaigns/{id}/emails` - Email history

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request |
| 404 | Not found |
| 422 | Validation error |
| 500 | Server error |

---

*Generated: January 30, 2026*
