# FLB Extended API Documentation

This document provides an overview of the key API endpoints available in the FLB Extended platform.
For a machine-readable specification, see `openapi.yaml`.

## Base URL
`http://localhost:5000` (Development)

## Authentication
Most endpoints require a valid session. Login via `/login` to establish a session.
Some endpoints (like Admin) require specific roles (`admin`, `moderator`).

---

## 1. Authentication & Users

### `POST /register`
Register a new user.
- **Body:** `{ "full_name": "John Doe", "email": "john@example.com", "password": "StrongPass1", "account_type": "farmer" }`
- **Returns:** `201 Created` with user details.

### `POST /login`
Login a user.
- **Body:** `{ "email": "john@example.com", "password": "StrongPass1" }`
- **Returns:** `200 OK` with user details.

### `GET /users`
List all users.
- **Returns:** `200 OK` with array of user objects.

---

## 2. Verification

### `POST /documents/upload`
Upload a verification document.
- **Body:** `{ "user_id": 1, "document_type": "NIN", "document_number": "12345678901" }`
- **Returns:** `201 Created`

### `POST /documents/verify/<doc_id>`
(Admin Only) Approve or reject a document.
- **Body:** `{ "admin_id": 5, "status": "approved", "admin_notes": "Verified via portal" }`
- **Returns:** `200 OK`

---

## 3. Marketplace & Listings

### `POST /listings/create`
Create a land listing.
- **Body:** `{ "owner_id": 1, "title": "Farmland for Lease", "price": 500000, "location": "Lagos", "listing_type": "land_rent" }`
- **Returns:** `201 Created`

### `GET /listings/search`
Search listings.
- **Query Params:** `location`, `min_price`, `max_price`, `type`
- **Returns:** `200 OK`

---

## 4. Produce Assistant

### `POST /produce/calculate`
Calculate production costs and potential profit.
- **Body:** `{ "crop_name": "Maize", "land_size": 2.5, "season": "dry" }`
- **Returns:** `200 OK` with detailed cost breakdown.

### `POST /produce/shelf-life`
Estimate shelf life.
- **Body:** `{ "produce_type": "Tomato", "harvest_date": "2023-10-01", "storage_condition": "ambient" }`
- **Returns:** `200 OK` with days remaining and quality status.

---

## 5. Wallet & Payments

### `POST /api/wallet/fund`
Initialize a wallet funding transaction via Interswitch.
- **Body:** `{ "user_id": 1, "amount": 5000, "email": "user@example.com" }`
- **Returns:** `200 OK` with `payment_url`, `merchant_code`, and `txn_ref`.

### `GET /api/wallet/balance/<user_id>`
Get current wallet balance.
- **Returns:** `200 OK` with `{ "balance": 5000.00 }`

---

## 6. Forum & Community

### `GET /forum/posts`
Get forum posts.
- **Query Params:** `category`, `sort` (new/top)
- **Returns:** `200 OK`

### `POST /forum/posts`
Create a new discussion.
- **Body:** `{ "author_id": 1, "title": "Best fertilizer for yams?", "content": "...", "category": "planting advice" }`
- **Returns:** `201 Created`

---

## 7. Ratings

### `POST /ratings`
Rate a user.
- **Body:** `{ "rater_id": 1, "rated_user_id": 2, "score": 5, "review": "Great worker!" }`
- **Returns:** `201 Created`
