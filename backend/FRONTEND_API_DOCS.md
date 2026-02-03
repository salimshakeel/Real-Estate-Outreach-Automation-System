# Frontend API Documentation

**Base URL:** `http://localhost:8000`  
**Interactive Docs:** `http://localhost:8000/docs`

---

# Table of Contents

1. [Health Check](#health-check)
2. [Leads](#leads)
3. [Templates](#templates)
4. [Campaigns](#campaigns)
5. [Dashboard](#dashboard)

---

# Health Check

## GET `/`

**Purpose:** Root endpoint - API welcome message

**Response:**
```json
{
  "message": "Real Estate Outreach API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

## GET `/health`

**Purpose:** Check if server is running

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-30T10:30:00.000Z"
}
```

---

## GET `/config`

**Purpose:** Get non-sensitive app configuration

**Response:**
```json
{
  "app_name": "Real Estate Outreach API",
  "version": "1.0.0",
  "environment": "development",
  "debug": true,
  "sendgrid_configured": false,
  "openai_configured": false
}
```

---

# Leads

## POST `/api/leads/upload`

**Purpose:** Upload CSV file with leads

**Content-Type:** `multipart/form-data`

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | CSV file with leads |

**CSV Columns (flexible mapping):**
| Column | Required | Aliases |
|--------|----------|---------|
| email | Yes | Email, EMAIL, e-mail |
| first_name | Yes | FirstName, First Name, first |
| last_name | No | LastName, Last Name, last |
| phone | No | Phone, PHONE, telephone |
| address | No | Address, ADDRESS, property_address |
| property_type | No | PropertyType, Property Type, type |
| estimated_value | No | EstimatedValue, Value, price |
| company | No | Company, COMPANY, organization |

**Response (Success):**
```json
{
  "filename": "leads.csv",
  "total_rows": 50,
  "valid_rows": 48,
  "invalid_rows": 2,
  "duplicates": 3,
  "created": 45,
  "errors": [
    "Row 5: Invalid email format",
    "Row 12: Missing required field 'first_name'"
  ]
}
```

---

## GET `/api/leads`

**Purpose:** Get paginated list of leads

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number (starts at 1) |
| per_page | int | 20 | Items per page (max 100) |
| status | string | null | Filter by status |
| search | string | null | Search by email or name |

**Status Values:** `uploaded`, `contacted`, `replied`, `interested`, `booked`, `closed`

**Example Request:**
```
GET /api/leads?page=1&per_page=10&status=contacted&search=john
```

**Response:**
```json
{
  "total": 150,
  "page": 1,
  "per_page": 10,
  "total_pages": 15,
  "items": [
    {
      "id": 1,
      "email": "john.doe@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "company": "ABC Realty",
      "phone": "555-1234",
      "address": "123 Oak Street, Miami FL",
      "property_type": "Single Family",
      "estimated_value": "$450,000",
      "status": "contacted",
      "notes": null,
      "created_by": null,
      "created_at": "2026-01-30T10:00:00.000Z",
      "updated_at": "2026-01-30T10:00:00.000Z"
    }
  ]
}
```

---

## GET `/api/leads/{lead_id}`

**Purpose:** Get single lead with full history

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| lead_id | int | Yes | Lead ID |

**Response:**
```json
{
  "lead": {
    "id": 1,
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "company": "ABC Realty",
    "phone": "555-1234",
    "address": "123 Oak Street, Miami FL",
    "property_type": "Single Family",
    "estimated_value": "$450,000",
    "status": "replied",
    "notes": "Interested in selling Q2",
    "created_by": null,
    "created_at": "2026-01-30T10:00:00.000Z",
    "updated_at": "2026-01-30T12:00:00.000Z"
  },
  "email_sequences": [
    {
      "id": 1,
      "sequence_day": 1,
      "email_subject": "Quick question about 123 Oak Street",
      "status": "sent",
      "sent_at": "2026-01-30T10:30:00.000Z",
      "opened_at": "2026-01-30T11:00:00.000Z",
      "replied_at": "2026-01-30T12:00:00.000Z"
    }
  ],
  "replies": [
    {
      "id": 1,
      "email_from": "john.doe@example.com",
      "email_subject": "Re: Quick question about 123 Oak Street",
      "email_body": "Yes, I'm interested in discussing...",
      "sentiment": "interested",
      "confidence_score": 0.92,
      "received_at": "2026-01-30T12:00:00.000Z"
    }
  ],
  "bookings": [
    {
      "id": 1,
      "scheduled_time": "2026-02-05T14:00:00.000Z",
      "calendly_response_status": "confirmed"
    }
  ]
}
```

---

## POST `/api/leads`

**Purpose:** Create a single lead manually

**Content-Type:** `application/json`

**Request Body:**
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| email | string | Yes | Valid email format |
| first_name | string | Yes | 1-100 characters |
| last_name | string | No | Max 100 characters |
| company | string | No | Max 100 characters |
| phone | string | No | Max 20 characters |
| address | string | No | Max 255 characters |
| property_type | string | No | Max 100 characters |
| estimated_value | string | No | Max 50 characters |
| notes | string | No | Any length |
| created_by | string | No | Max 100 characters |

**Example Request:**
```json
{
  "email": "jane.smith@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "phone": "555-5678",
  "address": "456 Pine Avenue, Miami FL",
  "property_type": "Condo",
  "estimated_value": "$320,000"
}
```

**Response:**
```json
{
  "id": 51,
  "email": "jane.smith@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "company": null,
  "phone": "555-5678",
  "address": "456 Pine Avenue, Miami FL",
  "property_type": "Condo",
  "estimated_value": "$320,000",
  "status": "uploaded",
  "notes": null,
  "created_by": null,
  "created_at": "2026-01-30T10:00:00.000Z",
  "updated_at": "2026-01-30T10:00:00.000Z"
}
```

---

## PUT `/api/leads/{lead_id}`

**Purpose:** Update an existing lead

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| lead_id | int | Yes | Lead ID |

**Request Body:** (all fields optional)
| Field | Type | Validation |
|-------|------|------------|
| email | string | Valid email format |
| first_name | string | Max 100 characters |
| last_name | string | Max 100 characters |
| company | string | Max 100 characters |
| phone | string | Max 20 characters |
| address | string | Max 255 characters |
| property_type | string | Max 100 characters |
| estimated_value | string | Max 50 characters |
| status | string | One of: uploaded, contacted, replied, interested, booked, closed |
| notes | string | Any length |

**Example Request:**
```json
{
  "status": "interested",
  "notes": "Very interested, wants to meet next week"
}
```

**Response:** Updated lead object (same as POST response)

---

## DELETE `/api/leads/{lead_id}`

**Purpose:** Delete a lead (cascades to related records)

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| lead_id | int | Yes | Lead ID |

**Response:**
```json
{
  "message": "Lead 'john.doe@example.com' deleted successfully",
  "success": true
}
```

---

## GET `/api/leads/template/csv`

**Purpose:** Download sample CSV template

**Response:** CSV file download

**File Content:**
```csv
email,first_name,last_name,phone,address,property_type,estimated_value,company
john.doe@example.com,John,Doe,555-1234,123 Main St,Single Family,$450000,ABC Corp
```

---

# Templates

## POST `/api/templates`

**Purpose:** Create a new email template

**Request Body:**
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| name | string | Yes | 1-255 characters, unique |
| subject | string | Yes | 1-255 characters |
| body | string | Yes | Min 1 character |
| is_default | boolean | No | Default: false |
| created_by | string | No | Max 100 characters |

**Placeholders Available:**
- `{{first_name}}` - Lead's first name
- `{{last_name}}` - Lead's last name
- `{{full_name}}` - First + Last name
- `{{email}}` - Lead's email
- `{{phone}}` - Lead's phone
- `{{address}}` - Property address
- `{{property_type}}` - Property type
- `{{estimated_value}}` - Estimated value

**Example Request:**
```json
{
  "name": "Initial Outreach",
  "subject": "Quick question about {{address}}",
  "body": "Hi {{first_name}},\n\nI noticed your property at {{address}} and wanted to reach out.\n\nWould you be open to a quick chat?\n\nBest regards",
  "is_default": true
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Initial Outreach",
  "subject": "Quick question about {{address}}",
  "body": "Hi {{first_name}},\n\nI noticed your property...",
  "is_default": true,
  "created_by": null,
  "created_at": "2026-01-30T10:00:00.000Z",
  "updated_at": "2026-01-30T10:00:00.000Z"
}
```

---

## GET `/api/templates`

**Purpose:** Get all templates with pagination

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| per_page | int | 20 | Items per page (max 100) |
| search | string | null | Search by name |

**Response:**
```json
{
  "total": 5,
  "page": 1,
  "per_page": 20,
  "total_pages": 1,
  "items": [
    {
      "id": 1,
      "name": "Initial Outreach",
      "subject": "Quick question about {{address}}",
      "body": "Hi {{first_name}}...",
      "is_default": true,
      "created_by": null,
      "created_at": "2026-01-30T10:00:00.000Z",
      "updated_at": "2026-01-30T10:00:00.000Z"
    }
  ]
}
```

---

## GET `/api/templates/{template_id}`

**Purpose:** Get single template

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| template_id | int | Yes | Template ID |

**Response:** Single template object

---

## GET `/api/templates/default/active`

**Purpose:** Get the default template

**Response:** Single template object (or 404 if no default set)

---

## PUT `/api/templates/{template_id}`

**Purpose:** Update a template

**Request Body:** (all fields optional)
| Field | Type | Validation |
|-------|------|------------|
| name | string | Max 255 characters |
| subject | string | Max 255 characters |
| body | string | Any length |
| is_default | boolean | Sets as default (unsets others) |

**Response:** Updated template object

---

## DELETE `/api/templates/{template_id}`

**Purpose:** Delete a template

**Response:**
```json
{
  "message": "Template 'Initial Outreach' deleted successfully",
  "success": true
}
```

---

## POST `/api/templates/{template_id}/preview`

**Purpose:** Preview template with sample data

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| template_id | int | Yes | Template ID |

**Request Body:** (optional - custom sample data)
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "address": "123 Oak Street"
}
```

**Response:**
```json
{
  "template_id": 1,
  "template_name": "Initial Outreach",
  "original": {
    "subject": "Quick question about {{address}}",
    "body": "Hi {{first_name}}..."
  },
  "personalized": {
    "subject": "Quick question about 123 Oak Street",
    "body": "Hi John..."
  },
  "placeholders_found": ["first_name", "address"],
  "sample_data_used": {
    "first_name": "John",
    "address": "123 Oak Street"
  }
}
```

---

## POST `/api/templates/seed/defaults`

**Purpose:** Create default starter templates

**Response:**
```json
{
  "message": "Created 3 default templates",
  "success": true
}
```

**Templates Created:**
1. "Initial Outreach" (default)
2. "Follow Up #1"
3. "Market Update"

---

# Campaigns

## POST `/api/campaigns`

**Purpose:** Create a new campaign (draft status)

**Request Body:**
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| name | string | Yes | 1-255 characters |
| description | string | No | Any length |
| email_template | string | No | Raw template text |
| created_by | string | No | Max 100 characters |

**Example Request:**
```json
{
  "name": "Q1 2026 Outreach",
  "description": "First quarter outreach to Miami properties"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Q1 2026 Outreach",
  "description": "First quarter outreach to Miami properties",
  "email_template": null,
  "status": "draft",
  "started_at": null,
  "ended_at": null,
  "created_by": null,
  "created_at": "2026-01-30T10:00:00.000Z",
  "updated_at": "2026-01-30T10:00:00.000Z"
}
```

---

## GET `/api/campaigns`

**Purpose:** Get all campaigns with pagination

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| per_page | int | 20 | Items per page (max 100) |
| status | string | null | Filter: draft, scheduled, active, completed, paused |
| search | string | null | Search by name |

**Response:**
```json
{
  "total": 3,
  "page": 1,
  "per_page": 20,
  "total_pages": 1,
  "items": [
    {
      "id": 1,
      "name": "Q1 2026 Outreach",
      "description": "First quarter outreach",
      "email_template": null,
      "status": "active",
      "started_at": "2026-01-30T10:30:00.000Z",
      "ended_at": null,
      "created_by": null,
      "created_at": "2026-01-30T10:00:00.000Z",
      "updated_at": "2026-01-30T10:30:00.000Z"
    }
  ]
}
```

---

## GET `/api/campaigns/{campaign_id}`

**Purpose:** Get campaign with statistics

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| campaign_id | int | Yes | Campaign ID |

**Response:**
```json
{
  "campaign": {
    "id": 1,
    "name": "Q1 2026 Outreach",
    "status": "active",
    "started_at": "2026-01-30T10:30:00.000Z"
  },
  "stats": {
    "total_leads": 50,
    "emails_sent": 48,
    "emails_opened": 25,
    "emails_replied": 8,
    "emails_bounced": 2,
    "open_rate": 52.08,
    "reply_rate": 16.67
  }
}
```

---

## PUT `/api/campaigns/{campaign_id}`

**Purpose:** Update campaign details

**Request Body:** (all fields optional)
| Field | Type | Validation |
|-------|------|------------|
| name | string | Max 255 characters |
| description | string | Any length |
| email_template | string | Any length |
| status | string | draft, scheduled, paused, completed (not active) |

**Note:** Cannot change status to "active" via this endpoint. Use `/start` instead.

---

## DELETE `/api/campaigns/{campaign_id}`

**Purpose:** Delete campaign (only if not active)

**Response:**
```json
{
  "message": "Campaign 'Q1 2026 Outreach' deleted successfully",
  "success": true
}
```

---

## POST `/api/campaigns/{campaign_id}/start`

**Purpose:** Start campaign - send emails to leads

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| campaign_id | int | Yes | Campaign ID |

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| lead_ids | array[int] | Yes | List of lead IDs to email |
| email_template_id | int | No* | Template to use |
| subject | string | No* | Custom subject |
| body | string | No* | Custom body |

*Either `email_template_id` OR both `subject` and `body` required

**Example Request (using template):**
```json
{
  "lead_ids": [1, 2, 3, 4, 5],
  "email_template_id": 1
}
```

**Example Request (custom email):**
```json
{
  "lead_ids": [1, 2, 3],
  "subject": "Hi {{first_name}}, about your property",
  "body": "Hello {{first_name}},\n\nI wanted to reach out about {{address}}..."
}
```

**Response:**
```json
{
  "campaign_id": 1,
  "total_leads": 5,
  "emails_sent": 5,
  "emails_failed": 0,
  "details": [
    {
      "lead_id": 1,
      "email": "john@example.com",
      "success": true,
      "message_id": "mock_abc123"
    },
    {
      "lead_id": 2,
      "email": "jane@example.com",
      "success": true,
      "message_id": "mock_def456"
    }
  ],
  "campaign": {
    "id": 1,
    "name": "Q1 2026 Outreach",
    "status": "active",
    "started_at": "2026-01-30T10:30:00.000Z"
  }
}
```

---

## POST `/api/campaigns/{campaign_id}/pause`

**Purpose:** Pause an active campaign

**Response:** Updated campaign object with status: "paused"

---

## POST `/api/campaigns/{campaign_id}/resume`

**Purpose:** Resume a paused campaign

**Response:** Updated campaign object with status: "active"

---

## POST `/api/campaigns/{campaign_id}/complete`

**Purpose:** Mark campaign as completed

**Response:** Updated campaign object with status: "completed" and ended_at timestamp

---

## GET `/api/campaigns/{campaign_id}/emails`

**Purpose:** Get emails sent in this campaign

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| per_page | int | 50 | Items per page |
| status | string | null | Filter: pending, scheduled, sent, opened, replied, bounced |

**Response:**
```json
{
  "campaign": {
    "id": 1,
    "name": "Q1 2026 Outreach"
  },
  "page": 1,
  "per_page": 50,
  "emails": [
    {
      "id": 1,
      "lead_id": 1,
      "lead_name": "John Doe",
      "lead_email": "john@example.com",
      "subject": "Quick question about 123 Oak Street",
      "status": "opened",
      "sent_at": "2026-01-30T10:30:00.000Z",
      "opened_at": "2026-01-30T11:00:00.000Z",
      "replied_at": null
    }
  ]
}
```

---

## POST `/api/campaigns/quick-start`

**Purpose:** Create and start campaign in one call

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | Yes | Campaign name |
| lead_ids | string | Yes | Comma-separated lead IDs |
| template_id | int | No* | Template ID to use |
| subject | string | No* | Custom subject |
| body | string | No* | Custom body |

*Either `template_id` OR both `subject` and `body` required

**Example Request:**
```
POST /api/campaigns/quick-start?name=Quick Test&lead_ids=1,2,3&template_id=1
```

**Response:** Same as `/start` endpoint

---

# Dashboard

## GET `/api/dashboard`

**Purpose:** Get complete dashboard (stats + funnel + activity)

**Response:**
```json
{
  "stats": {
    "total_leads": 150,
    "leads_by_status": {
      "uploaded": 50,
      "contacted": 60,
      "replied": 20,
      "interested": 12,
      "booked": 5,
      "closed": 3
    },
    "total_emails_sent": 180,
    "emails_opened": 95,
    "emails_replied": 25,
    "emails_bounced": 5,
    "open_rate": 52.78,
    "reply_rate": 13.89,
    "total_replies": 25,
    "replies_by_sentiment": {
      "interested": 12,
      "not_now": 8,
      "unsubscribe": 2,
      "other": 3
    },
    "total_bookings": 8,
    "upcoming_bookings": 3,
    "emails_sent_today": 15,
    "emails_sent_this_week": 45,
    "replies_today": 3,
    "bookings_this_week": 2
  },
  "funnel": {
    "uploaded": 50,
    "contacted": 60,
    "replied": 20,
    "interested": 12,
    "booked": 5,
    "closed": 3
  },
  "recent_activity": [
    {
      "type": "email_sent",
      "lead_id": 45,
      "lead_name": "John Doe",
      "description": "Email sent: Quick question about 123 Oak...",
      "timestamp": "2026-01-30T10:30:00.000Z"
    },
    {
      "type": "reply_received",
      "lead_id": 32,
      "lead_name": "Jane Smith",
      "description": "Reply received (interested)",
      "timestamp": "2026-01-30T10:15:00.000Z"
    },
    {
      "type": "booking_created",
      "lead_id": 28,
      "lead_name": "Bob Wilson",
      "description": "Meeting scheduled for Feb 05 at 02:00 PM",
      "timestamp": "2026-01-30T09:45:00.000Z"
    }
  ]
}
```

---

## GET `/api/dashboard/stats`

**Purpose:** Get statistics only

**Response:** `stats` object from full dashboard

---

## GET `/api/dashboard/funnel`

**Purpose:** Get lead funnel counts

**Response:**
```json
{
  "uploaded": 50,
  "contacted": 60,
  "replied": 20,
  "interested": 12,
  "booked": 5,
  "closed": 3
}
```

---

## GET `/api/dashboard/activity`

**Purpose:** Get recent activity feed

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | int | 20 | Number of items |

**Response:** Array of activity objects

---

## GET `/api/dashboard/campaigns`

**Purpose:** Get campaigns overview

**Response:**
```json
{
  "total": 5,
  "by_status": {
    "draft": 1,
    "active": 2,
    "completed": 2
  },
  "active_campaigns": [
    {
      "id": 3,
      "name": "Q1 2026 Outreach",
      "started_at": "2026-01-30T10:00:00.000Z"
    }
  ]
}
```

---

## GET `/api/dashboard/quick`

**Purpose:** Lightweight quick stats (fast loading)

**Response:**
```json
{
  "leads": 150,
  "emails_sent": 180,
  "replies": 25,
  "bookings": 8
}
```

---

# Error Responses

## 400 Bad Request

```json
{
  "detail": "Error description here"
}
```

## 404 Not Found

```json
{
  "detail": "Lead with ID 999 not found"
}
```

## 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

# Frontend Integration Tips

## Axios Example

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Get leads
const getLeads = async (page = 1, status = null) => {
  const params = { page, per_page: 20 };
  if (status) params.status = status;
  const response = await api.get('/api/leads', { params });
  return response.data;
};

// Upload CSV
const uploadCSV = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/api/leads/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

// Start campaign
const startCampaign = async (campaignId, leadIds, templateId) => {
  const response = await api.post(`/api/campaigns/${campaignId}/start`, {
    lead_ids: leadIds,
    email_template_id: templateId
  });
  return response.data;
};

// Get dashboard
const getDashboard = async () => {
  const response = await api.get('/api/dashboard');
  return response.data;
};
```

---

*Documentation Generated: January 30, 2026*
