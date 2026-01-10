# API documentation

Base path: `/api/v1`

## Auth

### POST `/auth/register`
- **Body:** `RegisterBusinessRequest`
- **Response:** `TokenResponse`
- Creates a business and admin user; returns tokens.

### POST `/auth/login`
- **Body:** `LoginRequest`
- **Response:** `TokenResponse`
- Logs in staff/admin; returns tokens.

### POST `/auth/refresh`
- **Body:** `RefreshRequest`
- **Response:** `TokenResponse`
- Exchanges refresh token for new tokens.

### GET `/auth/me`
- **Auth:** Bearer access token
- **Response:** `MeResponse`

## Business ops

### GET `/business/profile`
- **Auth:** staff/admin
- **Response:** `BusinessResponse`

### POST `/business/staff`
- **Auth:** admin
- **Body:** `CreateStaffRequest`
- **Response:** `StaffResponse`

### GET `/users/`
- **Auth:** staff/admin
- **Response:** `StaffResponse[]`

## Person management

### POST `/persons/`
- **Auth:** staff/admin
- **Body:** `AddPersonRequest`
- **Response:** `PersonResponse`
- Adds or updates a person (phone hashed internally).

### PUT `/persons/{person_id}`
- **Auth:** staff/admin
- **Body:** `UpdatePersonRequest`
- **Response:** `PersonResponse`

### POST `/persons/relationships`
- **Auth:** staff/admin
- **Body:** `RelationshipRequest`
- **Response:** `RelationshipResponse`

## Payments

### POST `/payments/`
- **Auth:** staff/admin
- **Body:** `RecordPaymentRequest`
- **Response:** `PaymentResponse`

### PUT `/payments/{payment_id}/status`
- **Auth:** staff/admin
- **Body:** `UpdatePaymentStatusRequest`
- **Response:** `PaymentResponse`

### GET `/payments/`
- **Auth:** staff/admin
- **Query:** `limit`, `offset`
- **Response:** `PaymentResponse[]`

## Scoring

### POST `/scoring/compute`
- **Auth:** staff/admin
- **Body:** `ComputeScoreRequest`
- **Response:** `TrustScoreResponse`

### GET `/scoring/summary/{person_id}`
- **Auth:** staff/admin
- **Response:** `TrustSummaryResponse`

### GET `/scoring/explain/{person_id}`
- **Auth:** staff/admin
- **Response:** `TrustScoreResponse`

## System

### GET `/system/health`
- **Response:** `{ status: "ok" }`

### GET `/system/audit`
- **Auth:** admin
- **Response:** `AuditLogResponse[]`
