# FLB Extended — Security Strategy & Audit Plan

## 1. Current Security Posture
We have implemented a "Defense in Depth" approach to secure user data and financial transactions.

### A. Application Security
- **HTTPS Enforcement:** All production traffic is forced over HTTPS using `Flask-Talisman`.
- **Input Validation:** Strict schema validation using `Marshmallow` to prevent injection attacks.
- **Rate Limiting:** `Flask-Limiter` protects authentication and sensitive endpoints from brute-force attacks.
- **Secure Headers:** HSTS, X-Content-Type-Options, and X-Frame-Options are enabled.

### B. Data Protection
- **Password Storage:** Passwords are hashed using strong algorithms (PBKDF2/Argon2 via `werkzeug.security`).
- **Verification Documents:** Access to uploaded ID documents is restricted to authorized Admins only and logged via `AdminAuditLog`.
- **Payment Data:** We do **not** store credit card numbers. All sensitive payment data is handled directly by Interswitch (PCI-DSS Level 1 certified).

## 2. Third-Party Audit Strategy

### A. Trigger Events
We will engage a third-party cybersecurity firm for a full audit upon reaching any of the following milestones:
1.  **User Base:** 10,000 active users.
2.  **Transaction Volume:** Monthly Gross Merchandise Value (GMV) exceeding ₦10,000,000.
3.  **Major Feature Release:** Before launching the "Wallet Card" feature.

### B. Audit Scope
The audit will focus on:
- **Penetration Testing:** Attempting to bypass authentication, manipulate wallet balances, or access unauthorized data.
- **Code Review:** Deep dive into `app.py` payment logic (`fund_wallet`, `payment_callback`) to identify race conditions or logic flaws.
- **Infrastructure:** Review of cloud configuration (AWS/Azure) for open ports or weak permissions.

## 3. Compliance Roadmap

### A. NDPR (Nigeria Data Protection Regulation)
- **Status:** Compliant.
- **Action:** Annual data privacy audit to ensure user rights (access, deletion) are respected.

### B. PCI-DSS (Payment Card Industry Data Security Standard)
- **Status:** Compliant via Third-Party (SAQ A).
- **Details:** Since we use Interswitch's redirect/popup model, we qualify for the simplest compliance level (SAQ A), as we do not touch card data.

## 4. Incident Response Plan
In the event of a suspected breach:
1.  **Containment:** Immediately disable the affected module (e.g., suspend wallet withdrawals).
2.  **Notification:** Notify affected users within 24 hours and the relevant regulatory bodies (NITDA) within 72 hours.
3.  **Forensics:** Preserve logs (`AdminAuditLog`, server logs) for investigation.
