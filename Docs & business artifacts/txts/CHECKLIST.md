# FLB Extended — Project Checklist

This checklist captures the product and technical work required to deliver the FLB platform described in `concept.txt`.
Use it as a living artifact: check items when done and add subtasks as needed.

---

## High-level product features
- [x] Accounts and roles
  - [x] Farmer / Farm Owner
  - [x] Realtor
  - [x] Worker
  - [x] Admin (platform moderation, appeals)
- [ ] Verification system
  - [x] Document upload (NIN, Passport, Driver's License)
  - [x] KYC review workflow for admins
  - [x] OTP/email/phone verification (WhatsApp/Telegram optional)
  - [ ] Integrate Cloudflare human check (optional)
- [ ] Profiles & visibility
  - [x] Profile pages for all account types
  - [x] Paid "boost" / visibility feature
- [x] Messaging & Contracts
  - [x] In-app messaging between users
  - [x] Contract generation/signing before payments
  - [x] Contract breach handling / fines / appeal
- [x] Marketplace & Real Estate
  - [x] Listings for land to let
  - [x] Option to attach 3D model / images / virtual tour
- [x] Worker marketplace
  - [x] Worker listings by skill (fumigation, fertilizer, specialist)
  - [x] Hire flow and payout tracking
- [x] Produce Assistant features
  - [x] Produce cost calculator (season, size, workers, margins, expenses) — 18 tests
  - [x] Shelf-life calculator (post-transport heat exposure model) — 20 tests
  - [x] AI Assistant (crop recommendations based on soil, climate, location) — 19 tests
- [x] Rating & Reporting system
  - [x] Ratings for Farmers, Realtors, Workers
  - [x] Report user / admin review flow
- [x] Payments & virtual wallet
  - [x] Virtual wallet per user
  - [x] Integrate Interswitch (or chosen PSP)
  - [x] Withdrawals to bank accounts
  - [x] Transaction fees, withdrawal fees, settlement flows
  - [ ] Optional future: wallet-backed payment card
- [x] Admin tools
  - [x] Ban/unban users, review appeals
  - [x] Review verification docs and onboarded personnel
- [x] Legal & compliance
  - [x] Terms of Service and Privacy Policy pages
  - [x] Legal team process for contracts and litigation

---

## Implementation roadmap (milestones)

### Milestone 0 — Project foundation ✅ COMPLETE
- [x] Repo scaffold: `app.py`, `models.py`, `config.py`, `requirements.txt`, tests
- [x] Basic endpoints: `/health`, `/users` (safe fallback mode without DB)
- [x] CI-friendly tests (pytest)

### Milestone 1 — Core accounts & auth ✅ COMPLETE
- [x] User registration & login (email/password)
- [x] Password hashing (werkzeug.security or passlib)
- [x] Account roles and role-based access control (RBAC)
- [x] Endpoints: create/list/user detail
- [x] Tests: registration/login, RBAC

### Milestone 2 — Verification & profile ✅ COMPLETE
- [x] Document upload API (store securely, link to user)
- [x] Admin verification workflow UI/API
- [x] OTP via SMS/email (OTP service integration)
- [x] Tests: upload + verification transitions

### Milestone 3 — Messaging & Contracts ✅ COMPLETE
- [x] Messaging model & API (DB-backed)
- [x] Contract template generation (PDF or structured JSON)
- [x] Signed contract storage and enforcement flags
- [x] Tests: message exchange, contract lifecycle

### Milestone 4 — Payments & Wallet ✅ COMPLETE
- [x] Virtual wallet model and endpoints
- [x] PSP integration (Interswitch) sandbox flows
- [x] Withdrawals and transaction ledger
- [x] Tests: simulated payments, balance updates

### Milestone 5 — Marketplace, Listings & 3D tours ✅ COMPLETE
- [x] Land listing model + CRUD (Real Estate: land_sale, land_rent)
- [x] Worker marketplace model + CRUD (Workers: fumigation, labor, specialist, etc.)
- [x] File/image uploads, 3D model attachments (links)
- [x] Search and filters for listings (location, price, type)
- [x] Search and filters for workers (specialization, location, rate, availability)
- [x] 13 worker tests + 13 listing tests (26 total marketplace tests)

### Milestone 6 — Produce Assistant & AI prototype ✅ COMPLETE
- [x] Implement deterministic produce cost calculator API (18 tests passing)
- [x] Implement shelf-life estimator API (20 tests passing)
- [x] AI Assistant: crop recommender based on soil, climate, location (19 tests passing)
- [x] Tests for calculators (edge cases, validation, multi-scenario)
- [x] 57 total tests for Produce Assistant module
- [x] Comprehensive documentation (MILESTONE_6_COMPLETED.md)

### Milestone 7 — Admin System ✅ COMPLETE
- [x] Admin roles (Moderator, Admin, Super Admin)
- [x] Ban/Unban users with reason tracking
- [x] Report system (create, resolve, dismiss)
- [x] Audit logs for admin actions
- [x] Hardened endpoints (rate limiting, schema validation)
- [x] Tests: admin actions, role hierarchy, report lifecycle (30 tests passing)

### Milestone 8 — Community & Farmer Advice Forum ✅ COMPLETE
- [x] Forum post model (questions, discussions, advice)
- [x] Comment/reply system
- [x] Categories (planting advice, pest control, equipment, general farming)
- [x] Mark helpful answers / voting system
- [x] Filter by location, crop type, category
- [x] Moderation tools for forum content (via existing admin endpoints + lock/pin flags)
- [x] Tests for forum CRUD and interactions (5 tests passing)

### Milestone 9 — Ratings & Reviews ✅ COMPLETE
- [x] Rating model (score 1-5, review text)
- [x] Update User and WorkerProfile with average ratings
- [x] Endpoints to submit and retrieve ratings
- [x] Tests: rating submission, average calculation, duplicate prevention

### Milestone 10 — Security, Privacy, Compliance ✅ COMPLETE
- [x] Password & secrets handling (no plaintext)
- [x] Input validation and SQL injection protection (via Marshmallow & SQLAlchemy)
- [x] CSRF/XSS mitigation (Flask-Talisman & CORS)
- [x] Secure storage for card/payment data (or use tokenized PSP flows)
- [x] Pen-test checklist and privacy review

### Milestone 11 — Testing, CI/CD, Deploy ✅ COMPLETE
- [x] Unit tests (>= 70% coverage target for core modules) - Achieved 83%
- [x] Integration tests for payment and messaging flows (mock PSPs)
- [x] CI pipeline (GitHub Actions / CI of choice)
- [x] Dockerfile and deployment manifest (optional)

---

## Security & data handling checklist
- [x] Never store passwords in plain text (use strong hashing + salt)
- [x] Enforce password policy (min length, complexity, rate-limit attempts)
- [x] Validate and sanitize all inputs (avoid SQL injection and XSS)
- [x] Log access to verification docs and restrict viewer roles
- [x] Use TLS for all network traffic in production
- [x] Consider third-party audits for payment flows (See `SECURITY_STRATEGY.md`)

---

## Testing & QA
- [x] Add unit tests for all API endpoints
- [x] Add tests for error flows and invalid inputs
- [x] Add end-to-end tests for critical flows (registration, hire, payment)
- [x] Add test fixtures to mock PSP (Email/SMS/Human Check pending implementation)

---

## Docs & business artifacts
- [x] `README.md` (usage, run, test steps) — done
- [x] `CHECKLIST.md` (this file) — done
- [x] API docs (OpenAPI / Swagger)
- [x] Terms of Service & Privacy Policy drafts
- [x] Business model and pricing doc (fees, premium features)

---

## Acceptance criteria (definition of done)
- Core account creation, verification, and messaging flows have tests and pass in CI
- Payments sandbox integration completed and ledger shows consistent balances
- Admin can review/ban/unban users with audit logs
- Produce Assistant provides reproducible outputs with unit tests
- The project builds in CI and passes test suite on PRs

---

## Open questions / decisions to make
- Preferred auth approach: session cookies or token-based (JWT)? - session cookies
- Payment service provider final choice (Interswitch as proposed, confirm) - Interswitch is choosen
- AI Assistant: do we want to use GPT-style API (cost) or open-source models? - GPT style, or give other examples of models that can be used
- Hosting platform target (Heroku, AWS ECS, Azure, DigitalOcean, etc.)

---

## Quick start tasks (for immediate next 2 weeks)
- [x] Lock package versions for compatibility and set up `pyproject.toml` or `requirements.txt` with pinned versions
- [x] Implement registration/login with tests
- [x] Add verification doc upload + admin approval flow
- [x] Add wallet model and sandbox payment endpoint
- [x] Add produce cost calculator module and API



*File created: `CHECKLIST.md`*
