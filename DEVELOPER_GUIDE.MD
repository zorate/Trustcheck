# TrustCheck Frontend Integration Guide

This guide is for frontend developers integrating with the TrustCheck API.

---

## 1) Base URL & Versioning

All endpoints are mounted under:

- `/api/v1`

---

## 2) Global Request/Response Contract

### Request Headers
Use these headers for authenticated calls:

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`
- Optional: `X-Request-ID` (client-generated for request tracing)

### Unified Success Response
All success responses follow:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": null
}
```

### Unified Error Response
All major error paths follow:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "SOME_CODE",
    "message": "Human-readable message",
    "details": {}
  },
  "meta": {
    "request_id": "..."
  }
}
```

Notes:
- `meta.request_id` is included where available.
- Rate-limited requests include `Retry-After: 60` and a structured error body.

---

## 3) Authentication & Roles

### Authentication
Protected routes require a valid Bearer access token.

### Role hierarchy
- `staff < admin < owner`

Use role checks in the UI for UX (hide/disable actions), but always expect server-side enforcement.

---

## 4) Endpoints by Module

---

## A) System

### 1) Health Check
**GET** `/api/v1/health`
- Auth: No
- Response: `APIResponse<dict>`

Example `data`:
```json
{
  "status": "ok|degraded",
  "database": "connected|unreachable",
  "version": "x.y.z",
  "environment": "dev|prod|..."
}
```

### 2) Audit Logs
**GET** `/api/v1/audit-logs`
- Auth: Yes (`owner`)
- Query Params:
  - `page` (int, default `1`, min `1`)
  - `page_size` (int, default `50`, min `1`, max `200`)
  - `action` (optional string)
- Response:
  - `data`: `AuditLogOut[]`
  - `meta`: `{ total, page, page_size, has_more }`

`AuditLogOut` fields:
- `id`, `business_id`, `actor_id`, `action`, `resource_type`, `resource_id`, `ip_address`, `created_at`

---

## B) Auth

Route prefix: `/api/v1/auth`

### 1) Register Business
**POST** `/api/v1/auth/register`
- Auth: No
- Status: `201`
- Body (`BusinessRegisterRequest`):
  - `business_name` (2..200)
  - `business_type` (`sme | landlord | cooperative | vendor`)
  - `email` (valid email)
  - `password` (8..128; must include uppercase, lowercase, digit)
  - `full_name` (2..200)
  - `phone` (optional, max 20)
- Response `data` (`AuthResponse`):
  - `user` (`BusinessUserOut`)
  - `tokens` (`TokenResponse`)

### 2) Login
**POST** `/api/v1/auth/login`
- Auth: No
- Body (`LoginRequest`):
  - `email`
  - `password`
- Response `data`: `AuthResponse`

### 3) Refresh Token
**POST** `/api/v1/auth/refresh`
- Auth: No
- Body (`RefreshRequest`):
  - `refresh_token`
- Response `data` (`TokenResponse`):
  - `access_token`
  - `refresh_token`
  - `token_type` (`bearer`)
  - `expires_in`

---

## C) Business

Route prefix: `/api/v1/business`

### 1) Get Business Profile
**GET** `/api/v1/business/profile`
- Auth: Yes (authenticated user)
- Response `data`: `BusinessOut`
  - `id`, `name`, `email`, `phone`, `address`, `business_type`, `is_active`, `created_at`

### 2) List Staff
**GET** `/api/v1/business/staff`
- Auth: Yes (`admin`+)
- Response `data`: `StaffOut[]`

### 3) Create Staff
**POST** `/api/v1/business/staff`
- Auth: Yes (`owner`)
- Status: `201`
- Body (`CreateStaffRequest`):
  - `email`
  - `full_name` (2..200)
  - `password` (8..128)
  - `role` (`admin | staff`)
- Response `data`: `StaffOut`

### 4) Update Staff
**PATCH** `/api/v1/business/staff/{staff_id}`
- Auth: Yes (`admin`+)
- Body (`UpdateStaffRequest`):
  - `full_name?`
  - `role?` (`admin | staff`)
  - `is_active?`
- Response `data`: `StaffOut`

### 5) Deactivate Staff
**DELETE** `/api/v1/business/staff/{staff_id}`
- Auth: Yes (`owner`)
- Response `data`: `null`

---

## D) Persons

Route prefix: `/api/v1/persons`

### 1) Add Person
**POST** `/api/v1/persons`
- Auth: Yes (`staff`+)
- Status: `201`
- Body (`AddPersonRequest`):
  - `full_name` (2..200)
  - `phone` (7–15 digits after normalization)
  - `capacity_level` (`none | basic | verified`, default `none`)
  - `notes?` (max 1000)
  - `relationship_type` (`customer | tenant | member | vendor_client`)
  - `relationship_start` (datetime)
- Response `data`: `PersonOut`

### 2) List Persons
**GET** `/api/v1/persons`
- Auth: Yes
- Query Params:
  - `page` (default `1`, min `1`)
  - `page_size` (default `20`, min `1`, max `100`)
- Response:
  - `data`: `PersonOut[]`
  - `meta`: `{ total, page, page_size, has_more }`

### 3) Lookup by Phone
**GET** `/api/v1/persons/lookup?phone=...`
- Auth: Yes
- Response `data`: `PersonOut`

### 4) Get Person by ID
**GET** `/api/v1/persons/{person_id}`
- Auth: Yes
- Response `data`: `PersonOut`

### 5) Update Person
**PATCH** `/api/v1/persons/{person_id}`
- Auth: Yes (`staff`+)
- Body (`UpdatePersonRequest`):
  - `full_name?`
  - `capacity_level?` (`none|basic|verified`)
  - `notes?`
- Response `data`: `PersonOut`

### 6) Deactivate Person
**DELETE** `/api/v1/persons/{person_id}`
- Auth: Yes (`admin`+)
- Response `data`: `null`

---

## E) Payments

Route prefix: `/api/v1/payments`

### 1) Record Payment
**POST** `/api/v1/payments`
- Auth: Yes (`staff`+)
- Status: `201`
- Body (`RecordPaymentRequest`):
  - `person_id`
  - `relationship_id`
  - `amount` (int > 0, smallest currency unit)
  - `currency` (default `NGN`, uppercased)
  - `description` (1..500)
  - `due_date` (datetime)
  - `paid_date?` (datetime)
  - `status` (`pending | paid | late | missed`, default `pending`)
- Response `data`: `PaymentOut`

### 2) List Payments for Person
**GET** `/api/v1/payments/person/{person_id}`
- Auth: Yes
- Query Params:
  - `page` (default `1`, min `1`)
  - `page_size` (default `20`, min `1`, max `100`)
  - `status?` (optional filter)
- Response:
  - `data`: `PaymentOut[]`
  - `meta`: `{ total, page, page_size, has_more }`

### 3) Get Payment
**GET** `/api/v1/payments/{payment_id}`
- Auth: Yes
- Response `data`: `PaymentOut`

### 4) Update Payment Status
**PATCH** `/api/v1/payments/{payment_id}/status`
- Auth: Yes (`staff`+)
- Body (`UpdatePaymentStatusRequest`):
  - `status` (`pending | paid | late | missed`)
  - `paid_date?`
- Response `data`: `PaymentOut`

---

## F) Scores

Route prefix: `/api/v1/scores`

### 1) Compute Score
**POST** `/api/v1/scores/compute/{person_id}`
- Auth: Yes (`staff`+)
- Response `data` (`ComputeScoreResponse`):
  - `person_id`, `total_score`, `risk_band`, `recommendation`, `cold_start`, `computed_at`

### 2) Get Score Summary
**GET** `/api/v1/scores/{person_id}`
- Auth: Yes
- Response `data` (`ScoreSummaryOut`):
  - `person_id`, `risk_band`, `recommendation`, `cold_start`, `computed_at?`

### 3) Get Score Breakdown
**GET** `/api/v1/scores/{person_id}/breakdown`
- Auth: Yes (`admin`+)
- Response `data` (`ScoreBreakdownOut`):
  - detailed component scores and labels + totals/risk metadata

### 4) Add Reference
**POST** `/api/v1/scores/references`
- Auth: Yes (`staff`+)
- Status: `201`
- Body (`AddReferenceRequest`):
  - `person_id`
  - `reference_type` (`informal | guarantor | member`)
  - `description?` (max 500)
- Response `data`: `ReferenceOut`

### 5) Revoke Reference
**DELETE** `/api/v1/scores/references/{reference_id}`
- Auth: Yes (`admin`+)
- Response `data`: `null`

---

## 5) Frontend Implementation Rules (Must Follow)

1. Always parse the envelope first: `success`, `data`, `error`, `meta`.
2. For list endpoints, use pagination values from `meta`.
3. Delete endpoints return `data: null` on success.
4. On `401`, try refresh token once, retry request once, otherwise logout.
5. Show validation errors from `error.details` in forms.
6. Handle `RATE_LIMIT_EXCEEDED` by showing cooldown + retry control.

---

## 6) Error Handling Mapping (UI)

- `VALIDATION_ERROR` → show field-level form errors.
- `PYDANTIC_VALIDATION_ERROR` → show validation banner.
- `HTTP_401` → refresh/login flow.
- `HTTP_403` → insufficient permission state.
- `HTTP_404` → not-found state.
- `RATE_LIMIT_EXCEEDED` → throttle message and delay.
- `INTERNAL_SERVER_ERROR` → generic fallback + retry.

---

## 7) Recommended Integration Workflow

1. Build a single API client wrapper for all requests.
2. Centralize auth token storage and refresh logic.
3. Centralize error normalization from API envelope.
4. Build feature modules per route group (`auth`, `business`, `persons`, `payments`, `scores`, `system`).
5. Add request/response logging in development using `request_id` for tracing.
6. Add integration tests for happy path + 401/403/422/429/500 handling.

---

## 8) Quick Start Checklist for Frontend Team

- [ ] Set API base URL to `/api/v1`
- [ ] Implement unified response parser
- [ ] Implement token refresh flow
- [ ] Implement role-gated UI actions
- [ ] Wire list pagination to `meta`
- [ ] Wire form validation error display from `error.details`
- [ ] Add standardized toast/banner for API errors

---

## 9) Notes

- This contract is now consistent and ready for frontend integration.
- Because there are no active consumers yet, this is an ideal baseline to build on.
