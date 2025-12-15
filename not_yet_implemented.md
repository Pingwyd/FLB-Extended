# Not Yet Implemented - Frontend Features

This document lists all features that exist in the backend but are either not implemented in the frontend or are not functional.

## Critical Issues

### 1. Workers Page - Empty/Not Functional ⚠️
**Status:** Backend exists, Frontend broken  
**Issue:** The workers directory page (`/workers-directory`) shows no workers even though workers are registered on the platform.

**Root Cause:**
- Frontend calls `/api/workers/list` endpoint
- Backend endpoint exists at line 3874 in `app.py`
- Need to verify if endpoint returns data correctly
- Possible issue with worker profile creation or data retrieval

**Files Involved:**
- `templates/workers.html` (lines 136-158)
- `app.py` (line 3874)

**What Needs to be Done:**
- Debug why `/api/workers/list` returns empty array
- Verify worker profiles are being created when users register as workers
- Ensure worker data is properly formatted for frontend display

---

### 2. Listing Update/Edit Functionality ⚠️
**Status:** Partially implemented  
**Issue:** The edit listing page exists but doesn't actually update images, videos, price, or title.

**What's Missing:**
- Backend route `/marketplace/<id>/edit` (POST) to handle updates
- Logic to update media files (images/videos)
- Logic to update listing details (title, price, description, location)
- File upload handling for replacing existing media

**Files Involved:**
- `templates/marketplace_edit.html`
- `app.py` (needs new route)

**What Needs to be Done:**
- Create POST endpoint `/listings/<id>/update` or `/marketplace/<id>/edit`
- Handle multipart/form-data for media updates
- Allow partial updates (only update fields that changed)
- Delete old media files when replaced with new ones

---

### 3. Realtor Dashboard - Listing View ❓
**Status:** Unclear purpose  
**Issue:** The "View" icon (eye icon) on realtor dashboard listings - what is it supposed to do?

**Current Behavior:**
- Links to `/marketplace/{listing.id}`
- Shows listing detail page

**Question:**
- Is this the intended behavior?
- Should it show analytics/views/statistics instead?
- Should it preview how the listing appears to others?

**Files Involved:**
- `templates/dashboard.html` (lines 129-131)

---

## Features from Checklist Not Visible in Frontend

### 4. Verification System - Incomplete UI
**Backend:** ✅ Complete  
**Frontend:** ⚠️ Partial

**What's Missing:**
- Document upload UI for users (NIN, Passport, Driver's License)
- KYC review workflow UI for admins
- OTP verification flow in frontend
- Cloudflare human check integration (optional)

**What Exists:**
- Verification badge display on dashboard
- Link to settings page for verification

**What Needs to be Done:**
- Create `/settings` page with verification tab
- Add document upload form
- Add OTP input/verification flow
- Admin verification review interface

---

### 5. Profile Boost/Visibility Feature
**Backend:** ✅ Complete (boost fields exist in models)  
**Frontend:** ❌ Not implemented

**What's Missing:**
- UI to purchase boost/visibility for profiles
- Payment flow for boost feature
- Display of boosted status on profiles
- Boost expiry handling

**Files Involved:**
- Models have `is_boosted` and `boost_expiry` fields
- No frontend implementation

---

### 6. Contract Generation/Signing
**Backend:** ✅ Complete  
**Frontend:** ⚠️ Limited

**What's Missing:**
- UI to view contract details before signing
- Digital signature interface
- Contract PDF download
- Contract breach reporting UI
- Appeal process UI

**What Exists:**
- Contract data shown in dashboard
- Basic contract status display

---

### 7. 3D Model/Virtual Tour Upload
**Backend:** ✅ Field exists (`model_3d_url` in Listing model)  
**Frontend:** ❌ Not implemented

**What's Missing:**
- Input field for 3D model URL in listing creation form
- Display of 3D models on listing detail page
- Virtual tour viewer integration

---

### 8. Produce Assistant Features - No Frontend
**Backend:** ✅ Complete (18 + 20 + 19 = 57 tests passing)  
**Frontend:** ❌ Not implemented

**Missing Pages:**
- Produce cost calculator UI
- Shelf-life calculator UI
- AI Assistant for crop recommendations UI

**APIs Available:**
- Cost calculator endpoint
- Shelf-life estimator endpoint
- AI crop recommender endpoint

---

### 9. Forum/Community Features
**Backend:** ✅ Complete (5 tests passing)  
**Frontend:** ❌ Not implemented

**What's Missing:**
- Forum listing page
- Create post/question UI
- Comment/reply system UI
- Mark helpful answers UI
- Voting system UI
- Category filters UI
- Location/crop type filters

---

### 10. Rating & Review System - Limited UI
**Backend:** ✅ Complete  
**Frontend:** ⚠️ Partial

**What's Missing:**
- UI to submit ratings for users/workers
- Review text input
- Display of reviews on profiles
- Average rating calculation display

**What Exists:**
- Rating display on worker cards (stars)
- Rating number shown

---

### 11. Wallet & Payments - No Frontend
**Backend:** ✅ Complete  
**Frontend:** ❌ Not implemented

**What's Missing:**
- Wallet balance display
- Transaction history page
- Deposit/withdrawal UI
- Payment flow integration
- Interswitch PSP integration UI
- Bank account linking for withdrawals

---

### 12. Messaging System - No Frontend
**Backend:** ✅ Complete  
**Frontend:** ❌ Not implemented

**What's Missing:**
- Inbox/messages page
- Chat interface
- Send message UI
- Message notifications
- Conversation threads

---

### 13. Job Listings - Partial Implementation
**Backend:** ✅ Complete  
**Frontend:** ⚠️ Partial

**What Exists:**
- Job creation form
- Job listing on dashboard
- Job edit page

**What's Missing:**
- Public job browsing page
- Job detail page
- Job application flow
- Job search/filters

---

### 14. Admin Tools - Limited UI
**Backend:** ✅ Complete  
**Frontend:** ⚠️ Partial

**What Exists:**
- User management page
- Moderation page
- Ban/unban functionality

**What's Missing:**
- Verification document review UI
- Audit log viewer
- Report resolution workflow UI
- Appeal review interface

---

### 15. Legal Pages - Missing
**Backend:** ✅ Routes exist  
**Frontend:** ❌ Not implemented

**What's Missing:**
- Terms of Service page
- Privacy Policy page

---

## Summary Statistics

- **Total Backend Features:** ~15 major feature sets
- **Fully Implemented in Frontend:** ~3 (20%)
- **Partially Implemented:** ~6 (40%)
- **Not Implemented:** ~6 (40%)

## Priority Recommendations

### High Priority (Critical for MVP)
1. Fix workers page (empty data issue)
2. Implement listing edit/update functionality
3. Add wallet/payment UI
4. Add messaging system UI
5. Implement verification document upload

### Medium Priority
6. Add produce assistant calculators UI
7. Implement forum/community features
8. Add rating/review submission UI
9. Complete job browsing functionality

### Low Priority (Nice to have)
10. 3D model/virtual tour integration
11. Profile boost purchase UI
12. Legal pages (Terms/Privacy)

---

*Last Updated: 2025-11-25*
