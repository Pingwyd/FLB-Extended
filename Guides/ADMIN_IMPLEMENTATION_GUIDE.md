# Admin Functionality Implementation Guide

## Where Admin Actions Will Be Implemented in the Codebase

### 1. **Database Models** (models.py)
Location: `models.py`
Milestone: Milestone 7

**Updates Needed:**

```python
# Update User model
class User(Base):
    account_type = Column(String(50))  # farmer, realtor, worker, moderator, admin, super_admin
    is_banned = Column(Boolean, default=False)
    banned_at = Column(DateTime, nullable=True)
    banned_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    ban_reason = Column(Text, nullable=True)

# New Model: AdminAuditLog
class AdminAuditLog(Base):
    __tablename__ = 'admin_audit_logs'
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100))  # 'ban_user', 'delete_listing', 'approve_verification'
    target_type = Column(String(50))  # 'user', 'listing', 'worker_profile'
    target_id = Column(Integer)
    reason = Column(Text)
    ip_address = Column(String(50))
    created_at = Column(DateTime)

# New Model: Report
class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, ForeignKey('users.id'))
    reported_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    reported_listing_id = Column(Integer, ForeignKey('listings.id'), nullable=True)
    reported_worker_id = Column(Integer, ForeignKey('worker_profiles.id'), nullable=True)
    report_type = Column(String(50))  # 'fraud', 'spam', 'harassment', 'inappropriate'
    description = Column(Text)
    status = Column(String(50), default='pending')  # pending, reviewed, resolved
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime)
```

---

### 2. **API Endpoints** (app.py)
Location: `app.py` - New section after worker endpoints
Milestone: Milestone 7

**Moderator Endpoints:**
```python
POST /admin/listings/<id>/delete        # Moderator: Delete fraudulent listing
POST /admin/listings/<id>/hide          # Moderator: Hide listing pending review
GET  /admin/reports                     # Moderator: View all reports
POST /admin/reports/<id>/resolve        # Moderator: Mark report as resolved
GET  /admin/reports/listings            # Moderator: Filter reports by type
```

**Admin Endpoints:**
```python
POST /admin/users/<id>/ban              # Admin: Ban a user
POST /admin/users/<id>/unban            # Admin: Unban a user
GET  /admin/users/banned                # Admin: List all banned users
POST /admin/verification/<id>/approve   # Admin: Already exists, ensure auth
POST /admin/verification/<id>/reject    # Admin: Already exists, ensure auth
GET  /admin/appeals                     # Admin: View ban appeals
```

**Super Admin Endpoints:**
```python
POST /admin/create-moderator            # Super Admin: Create moderator account
POST /admin/create-admin                # Super Admin: Create admin account
DELETE /admin/moderators/<id>           # Super Admin: Remove moderator
DELETE /admin/admins/<id>               # Super Admin: Remove admin
GET  /admin/audit-logs                  # Super Admin: View all audit logs
GET  /admin/financial-reports           # Super Admin: Access transaction data
```

---

### 3. **Authorization Middleware** (app.py or new auth.py)
Location: `app.py` or create new `auth.py`
Milestone: Milestone 7

**Create decorator functions:**
```python
def require_moderator(f):
    """Decorator to require moderator or higher access"""
    # Check if user is moderator, admin, or super_admin
    
def require_admin(f):
    """Decorator to require admin or super_admin access"""
    
def require_super_admin(f):
    """Decorator to require super_admin access only"""

# Usage:
@app.route('/admin/listings/<id>/delete', methods=['DELETE'])
@require_moderator
def delete_listing(id):
    # Implementation
```

---

### 4. **Tests** (tests/)
Location: Create new test files
Milestone: Milestone 7

**New Test Files:**
```
tests/
  test_admin_moderator.py   # Moderator action tests
  test_admin_actions.py     # Admin action tests
  test_super_admin.py       # Super admin tests
  test_reports.py           # Report system tests
  test_audit_logs.py        # Audit logging tests
```

---

### 5. **Account Type Updates** (Registration)
Location: `app.py` - `/register` endpoint
Milestone: Milestone 1 (update existing code)

**Update validation:**
```python
VALID_ROLES = {'farmer', 'realtor', 'worker', 'moderator', 'admin', 'super_admin'}
```

**Note:** Only super_admin can create moderator/admin accounts via special endpoints

---

## Checklist Mapping

| Feature | Checklist Location | File(s) |
|---------|-------------------|---------|
| Admin role types | Milestone 1 (update) | `models.py`, `app.py` |
| Moderator: Delete listings | Milestone 7 | `app.py`, `tests/test_admin_moderator.py` |
| Moderator: Review reports | Milestone 7 | `models.py` (Report), `app.py` |
| Admin: Ban/unban users | Milestone 7 | `models.py` (User updates), `app.py` |
| Admin: Approve verification | Milestone 2 (update auth) | `app.py` (add auth decorator) |
| Super Admin: Manage admins | Milestone 7 | `app.py`, `tests/test_super_admin.py` |
| Audit logging | Milestone 7 | `models.py` (AdminAuditLog), `app.py` |
| OTP for admin login | Milestone 7 or 2 | New `otp.py`, `app.py` |

---

## Implementation Order

1. **Milestone 7 - Phase 1:**
   - Update User model (add moderator, admin, super_admin types)
   - Create Report model
   - Create AdminAuditLog model

2. **Milestone 7 - Phase 2:**
   - Implement authorization decorators
   - Add moderator endpoints (delete listings, review reports)
   - Add admin endpoints (ban/unban users)

3. **Milestone 7 - Phase 3:**
   - Add super admin endpoints
   - Implement audit logging
   - Add OTP for admin/super_admin (if not in Milestone 2)

4. **Milestone 7 - Phase 4:**
   - Write comprehensive tests (RBAC testing crucial!)
   - Test privilege escalation attempts
   - Test audit log integrity

---

## Security Considerations

**Already in Checklist - Milestone 8:**
- Input validation (prevent injection attacks)
- Password hashing (already implemented)
- OTP integration (needed for admin login)

**To Add:**
- IP whitelisting for super_admin (environment variable config)
- Rate limiting on admin endpoints
- Session timeout for admin accounts
- 2FA requirement enforcement
