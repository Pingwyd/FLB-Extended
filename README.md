# FLB Extended — Nigerian Agricultural Platform 🌾

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3.2-green.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-1.4.48-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Active_Development-orange.svg)

**FLB Extended** is a comprehensive agricultural ecosystem platform designed to connect farmers, workers, land owners (realtors), and service providers across Nigeria. The platform bridges critical gaps in the agricultural sector by providing marketplace functionality, AI-powered farming assistants, secure payment solutions, and professional networking tools tailored specifically for the agricultural community.

---

## 📋 Table of Contents

- [Project Vision](#-project-vision)
- [Core Features](#-core-features)
- [User Types & Roles](#-user-types--roles)
- [Technology Stack](#-technology-stack)
- [Installation & Setup](#-installation--setup)
- [API Documentation](#-api-documentation)
- [Business Model](#-business-model)
- [Security & Compliance](#-security--compliance)
- [Project Structure](#-project-structure)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## 🌟 Project Vision

FLB Extended addresses the unique challenges facing both **new and experienced farmers** in Nigeria by creating a unified digital ecosystem that provides:

- **Connection to skilled labor** (laborers, specialists, fumigation experts, fertilizer suppliers)
- **Access to farmland** through real estate listings with optional 3D farm visualization
- **AI-powered farming assistance** for crop selection, cost calculation, and yield optimization
- **Community-driven knowledge sharing** via Reddit-style forums
- **Secure payment infrastructure** with virtual wallets and contract-based transactions
- **Trust and safety** through multi-factor verification and admin moderation systems

---

## ✨ Core Features

### 1. **Marketplace & Listings** 🏪
- Create, edit, and browse agricultural listings (land for lease/sale, equipment, produce)
- Advanced search and filtering by category, location, price range
- Image and video uploads for listings
- **Boost system**: Pay to feature listings at the top of search results
- Hidden/flagged listing management by admins

### 2. **Worker Directory** 👷
- Comprehensive profiles for agricultural workers (laborers, specialists, equipment operators)
- Skill-based search and filtering
- Daily rate display (changed from hourly to daily rates)
- Worker profile boosting for increased visibility
- Portfolio and experience showcasing

### 3. **Jobs System** 💼
- Job posting by farmers/farm owners
- Job application workflow with cover letters
- Application status tracking (pending, accepted, rejected)
- Job owner dashboard to review applications
- Accept/decline functionality with integrated messaging
- **Recently implemented**: Full job application API endpoints

### 4. **Produce Assistant (AI Tools)** 🤖
Three intelligent tools to help farmers make data-driven decisions:

#### a. **Cost Calculator**
- Calculate final produce cost considering:
  - Seasonal factors
  - Harvest size
  - Number of workers
  - Fertilizer and water costs
  - Profit margins
  - Other expenses (equipment, transportation)

#### b. **Shelf Life Predictor**
- Estimate produce freshness duration
- Account for transport conditions (heat, humidity)
- Help reduce waste by predicting spoilage timeline
- Optimize distribution and sales timing

#### c. **Crop Recommendation Engine**
- AI-driven crop suggestions based on:
  - Geographic location (state/region)
  - Available land size
  - Labor force availability
  - Funding/capital
  - Farmer's goals and experience level
  - Seasonal suitability

### 5. **Forum & Community** 💬
- Reddit-style discussion board for farmers
- Create posts, comment, and upvote/downvote
- Category-based organization
- Pin important posts (admin/moderator feature)
- Share farming tips, ask questions, and build community knowledge

### 6. **Messaging System** 📧
- Direct messaging between platform users
- Integrated with job applications (message applicants)
- Message read/unread status tracking
- Conversation history

### 7. **Contract & Payment System** 💰
- **Digital Wallet**: Virtual accounts for all users (farmers, workers, realtors)
- **Interswitch Integration**: Secure payment processing
- **Contract Creation**: Legally binding agreements before transactions
- **Digital Signatures**: Both parties must sign contracts
- **Transaction Types**:
  - Fund wallet via bank transfer/card
  - Pay workers for completed jobs
  - Pay realtors for land leases
  - Withdraw funds to bank accounts
- **Fee Structure**:
  - 1.5% deposit fee (payment processor)
  - ₦50 flat withdrawal fee
  - 5% transaction fee on worker payments
  - 1.5% fee on land transactions (capped at ₦50,000)

### 8. **Verification System** 🔐
- Multi-level user verification:
  - **Government ID**: NIN, Passport, or Driver's License upload
  - **OTP Verification**: Email and SMS (future: WhatsApp/Telegram)
  - **Admin Review**: Manual verification by platform administrators
- Document upload and storage
- Verification status tracking (pending, verified, rejected)
- Verification required for sensitive actions (contracts, high-value transactions)

### 9. **Three-Tier Admin System** 👮
Complete administrative hierarchy:

#### **Moderators** 🛡️
- Review and resolve user reports
- Hide suspicious listings
- Delete fraudulent content
- All actions logged in audit trail

#### **Admins** 🔨
- Ban/unban users with documented reasons
- View all banned users
- All moderator capabilities
- User management dashboard

#### **Super Admins** 👑
- Create moderators and admins
- Access complete audit logs
- Full system oversight
- Cannot be banned or restricted

### 10. **Reporting & Moderation** 🚨
- Users can report:
  - Other users (fraud, harassment)
  - Listings (scams, inappropriate content)
  - Worker profiles (fake credentials)
- Report types: Fraud, Spam, Harassment, Inappropriate Content, Scam, Fake Listing
- Report statuses: Pending, Under Review, Resolved, Dismissed
- Complete audit trail for all moderation actions

### 11. **Rating & Review System** ⭐
- Rate users after completed transactions
- 1-5 star ratings with written reviews
- Average rating display on profiles
- Helps build trust and reputation in the community

### 12. **Boost & Visibility** 🚀
- **Listing Boost**: ₦2,000/week to feature at top of marketplace
- **Worker Profile Boost**: Increased visibility in worker directory
- Wallet-based payment for boosts
- Time-based expiration tracking

---

## 👥 User Types & Roles

### **1. Farmer / Farm Owner** 🌾
- Create marketplace listings (produce, equipment, land)
- Post job openings
- Access Produce Assistant tools
- Hire workers
- Participate in forums
- Rate workers and service providers

### **2. Worker** 👨‍🌾
- Create professional profiles showcasing skills
- Apply to jobs
- Receive payments via digital wallet
- Build reputation through ratings
- Share expertise in forums

### **3. Realtor / Land Owner** 🏞️
- List land for lease or sale
- Upload farm photos/videos (future: 3D models)
- Manage rental agreements
- Receive payments via contracts

### **4. Admin Staff** 🛡️
- **Moderator**: Content moderation and report handling
- **Admin**: User management and ban authority
- **Super Admin**: Full system control and audit access

---

## 🛠️ Technology Stack

### **Backend**
- **Framework**: Flask 2.3.2
- **ORM**: SQLAlchemy 1.4.48
- **Database**: PostgreSQL/SQLite (configurable)
- **Authentication**: Session-based (bcrypt password hashing)
- **API Style**: RESTful JSON endpoints

### **Frontend**
- **Template Engine**: Jinja2
- **CSS Framework**: TailwindCSS (with dark mode support)
- **JavaScript**: Alpine.js for reactive components
- **Icons**: Heroicons

### **Security**
- **Password Hashing**: Bcrypt with salt
- **Rate Limiting**: Flask-Limiter (prevents brute force)
- **CORS**: Flask-CORS
- **Security Headers**: Flask-Talisman
- **Input Validation**: Marshmallow schemas
- **XSS Protection**: Template auto-escaping

### **Payment Integration**
- **Provider**: Interswitch
- **Features**: Card payments, bank transfers, wallet system

### **Testing**
- **Framework**: Pytest 7.4.0
- **Coverage**: pytest-cov
- **Test Types**: Unit tests, integration tests, manual test suites

### **Documentation**
- **API Spec**: OpenAPI 3.0 (Swagger UI available at `/api/docs`)

---

## 🚀 Installation & Setup

### **Prerequisites**
- Python 3.13+ (3.8+ compatible)
- PostgreSQL or SQLite
- pip (Python package manager)
- Virtual environment tool (venv, virtualenv, or conda)

### **Step 1: Clone the Repository**
```bash
git clone https://github.com/Pingwyd/FLB-Extended.git
cd FLB-Extended
```

### **Step 2: Create Virtual Environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### **Step 3: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 4: Configure Environment Variables**
Create a `config.py` file (or set environment variables):

```python
import os

# Database
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///flb_extended.db')

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Interswitch Payment Config
INTERSWITCH_MERCHANT_CODE = os.getenv('INTERSWITCH_MERCHANT_CODE')
INTERSWITCH_PAY_ITEM_ID = os.getenv('INTERSWITCH_PAY_ITEM_ID')
INTERSWITCH_MAC_KEY = os.getenv('INTERSWITCH_MAC_KEY')

# Upload Paths
UPLOAD_FOLDER = 'static/uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
```

### **Step 5: Initialize Database**
```bash
# The app automatically creates tables on first run
python app.py
```

### **Step 6: Create Admin Users**
```bash
# Create Super Admin
python "Create Admin/create_super_admin.py"

# Create Admin
python "Create Admin/create_admin_user.py"

# Create Moderator
python "Create Admin/create_moderator.py"
```

### **Step 7: Run the Application**
```bash
python app.py
```

The application will be available at `http://localhost:5000`

### **Step 8: Access API Documentation**
Navigate to `http://localhost:5000/api/docs` for interactive Swagger UI

---

## 📚 API Documentation

The platform exposes comprehensive RESTful APIs. Key endpoint categories include:

### **Authentication & Users**
- `POST /register` - Register new user
- `POST /login` - User authentication
- `POST /auth/request-otp` - Request OTP for verification
- `POST /auth/verify-otp` - Verify OTP code

### **Marketplace Listings**
- `GET /listings` - Browse all listings (with filters)
- `POST /listings/create` - Create new listing
- `GET /listings/<id>` - View listing details
- `PUT /listings/<id>/update` - Update listing
- `DELETE /listings/<id>` - Delete listing
- `POST /listings/<id>/boost` - Boost listing visibility

### **Jobs**
- `GET /api/jobs/list` - List all jobs
- `GET /api/jobs/<id>` - Job details
- `POST /api/jobs/<id>/apply` - Apply to job
- `GET /api/jobs/<id>/applications` - List job applications (owner only)
- `GET /api/jobs/<id>/my-application` - Check application status
- `POST /api/job-applications/<id>/accept` - Accept application
- `POST /api/job-applications/<id>/decline` - Decline application
- `POST /api/job-applications/<id>/message` - Message applicant

### **Workers**
- `GET /api/workers/list` - List all worker profiles
- `GET /workers/<id>` - Worker profile details
- `POST /workers/create-profile` - Create worker profile
- `PUT /workers/<id>` - Update worker profile
- `POST /workers/<id>/boost` - Boost worker visibility

### **Produce Assistant**
- `POST /produce-assistant/calculate-cost` - Calculate produce cost
- `POST /produce-assistant/predict-shelf-life` - Predict shelf life
- `POST /produce-assistant/recommend-crops` - Get crop recommendations
- `GET /produce-assistant/calculations/<user_id>` - Get user's calculations
- `GET /produce-assistant/predictions/<user_id>` - Get user's predictions
- `GET /produce-assistant/recommendations/<user_id>` - Get user's recommendations

### **Messaging & Contracts**
- `POST /messages/send` - Send message
- `GET /messages/<user_id>` - Get user messages
- `PUT /messages/<id>/read` - Mark message as read
- `POST /contracts/create` - Create contract
- `POST /contracts/<id>/sign` - Sign contract
- `GET /contracts/<user_id>` - Get user contracts

### **Wallet & Payments**
- `POST /api/wallet/fund` - Add funds to wallet
- `GET /api/wallet/balance/<user_id>` - Check wallet balance
- `GET /api/wallet/transactions/<user_id>` - Transaction history
- `POST /api/wallet/withdraw` - Withdraw funds
- `POST /api/bank-accounts` - Add bank account
- `GET /api/bank-accounts/<user_id>` - Get user bank accounts

### **Forum**
- `POST /forum/posts` - Create forum post
- `GET /forum/posts` - List all posts
- `GET /forum/posts/<id>` - Get post details
- `POST /forum/posts/<id>/comments` - Add comment
- `POST /forum/posts/<id>/vote` - Vote on post
- `POST /forum/posts/<id>/pin` - Pin post (admin)

### **Admin & Moderation**
- `POST /reports/create` - Create user report
- `GET /reports/my-reports/<user_id>` - View my reports
- `POST /admin/reports` - View all reports (moderator)
- `POST /admin/reports/<id>/resolve` - Resolve report
- `POST /admin/users/<user_id>/ban` - Ban user (admin)
- `POST /admin/users/<user_id>/unban` - Unban user
- `POST /admin/users/banned` - List banned users
- `POST /admin/listings/<id>/hide` - Hide listing
- `DELETE /admin/listings/<id>` - Delete listing
- `POST /admin/audit-logs` - View audit logs (super admin)

### **Ratings**
- `POST /ratings` - Submit rating
- `GET /ratings/user/<user_id>` - Get user ratings

### **Verification**
- `POST /documents/upload` - Upload verification documents
- `GET /documents/<user_id>` - Get user documents
- `POST /documents/verify/<doc_id>` - Verify document (admin)

**Full API documentation** is available via Swagger UI at `/api/docs` when running the application.

---

## 💼 Business Model

FLB Extended operates on a **hybrid revenue model** combining transaction fees and premium services:

### **Revenue Streams**

| Service | Fee | Description |
|---------|-----|-------------|
| **Account Creation** | Free | All user registrations are free |
| **Standard Listings** | Free | Basic marketplace listings |
| **Featured Listings** | ₦2,000/week | Top placement in search results |
| **Worker Hiring** | 5% | Commission on worker payments |
| **Land Transactions** | 1.5% | Fee on leases/sales (capped at ₦50k) |
| **Wallet Deposits** | 1.5% | Payment processor fee (Interswitch) |
| **Withdrawals** | ₦50 flat | Bank transfer processing fee |
| **Profile Boost** | ₦500/day | Enhanced visibility for workers/farmers |

### **Projected Year 1 Metrics**
- **Target Users**: 10,000 (5,000 farmers, 3,000 workers, 2,000 realtors)
- **GMV (Gross Merchandise Value)**: ₦500,000,000
- **Projected Revenue**: ₦15,000,000 (~3% blended take rate)

### **Future Premium Features**
- Advanced analytics dashboard
- Historical price data access
- Bulk hiring tools for commercial farms
- Premium AI recommendations
- Verified Pro badges

See `Docs & business artifacts/business model/BUSINESS_MODEL.md` for detailed financial projections.

---

## 🔒 Security & Compliance

### **Data Protection**
- **Password Security**: Bcrypt hashing with salt (never stored in plaintext)
- **XSS Prevention**: Automatic template escaping
- **CSRF Protection**: Token-based form validation
- **SQL Injection Prevention**: ORM parameterized queries
- **Rate Limiting**: Prevents brute force attacks
- **Security Headers**: Implemented via Flask-Talisman

### **Privacy & Legal**
- **Privacy Policy**: `/legal/privacy` (GDPR-inspired)
- **Terms of Service**: `/legal/tos` (legally binding agreements)
- **Contract System**: Digital signatures for all transactions
- **Audit Logging**: Complete admin action history
- **Data Minimization**: Only collect necessary information
- **Right to Erasure**: User account deletion workflow

### **Verification & Trust**
- Government ID verification (NIN, Passport, Driver's License)
- Email and phone OTP verification
- Admin manual review system
- User reporting and moderation tools
- Three-tier admin oversight

---

## 📁 Project Structure

```
FLB-Extended/
├── app.py                          # Main Flask application
├── models.py                       # SQLAlchemy database models
├── schemas.py                      # Marshmallow validation schemas
├── config.py                       # Configuration and environment variables
├── calculator.py                   # Produce cost calculation logic
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker containerization config
├── openapi.yaml                    # OpenAPI 3.0 specification
│
├── templates/                      # Jinja2 HTML templates
│   ├── base.html                   # Base template with navbar
│   ├── index.html                  # Landing page
│   ├── dashboard.html              # User dashboard
│   ├── login.html                  # Login page
│   ├── register.html               # Registration page
│   ├── marketplace.html            # Listings directory
│   ├── marketplace_detail.html     # Listing details
│   ├── marketplace_create.html     # Create listing form
│   ├── marketplace_edit.html       # Edit listing form
│   ├── jobs.html                   # Jobs directory
│   ├── job_detail.html             # Job details page
│   ├── job_create.html             # Create job form
│   ├── job_edit.html               # Edit job form
│   ├── workers.html                # Worker directory
│   ├── worker_detail.html          # Worker profile
│   ├── messages.html               # Messaging interface
│   ├── contracts.html              # Contracts management
│   ├── wallet.html                 # Wallet dashboard
│   ├── forum.html                  # Community forum
│   ├── produce_assistant.html      # AI tools page
│   ├── profile_settings.html       # User settings
│   ├── public_profile.html         # Public user profile
│   ├── admin_users.html            # Admin user management
│   ├── admin_moderation.html       # Moderation dashboard
│   ├── admin_settings.html         # Admin settings
│   ├── terms.html                  # Terms of Service
│   └── privacy.html                # Privacy Policy
│
├── static/                         # Static assets
│   ├── css/                        # Custom stylesheets
│   ├── js/                         # JavaScript files
│   ├── img/                        # Images and icons
│   └── uploads/                    # User-uploaded files
│       └── listings/               # Listing images/videos
│
├── tests/                          # Test suite
│   ├── conftest.py                 # Pytest configuration
│   ├── test_app.py                 # General app tests
│   ├── test_auth.py                # Authentication tests
│   ├── test_listings.py            # Marketplace tests
│   ├── test_workers.py             # Worker profile tests
│   ├── test_contracts.py           # Contract tests
│   ├── test_messaging.py           # Messaging tests
│   ├── test_forum.py               # Forum tests
│   ├── test_admin.py               # Admin system tests
│   ├── test_ratings.py             # Rating system tests
│   ├── test_verification.py        # Verification tests
│   ├── test_otp.py                 # OTP tests
│   ├── test_boost.py               # Boost feature tests
│   ├── test_audit_logging.py       # Audit log tests
│   └── test_produce_assistant.py   # AI tools tests
│
├── Manual tests/                   # Manual testing scripts
│   ├── test_manual.py
│   ├── test_messaging_contracts_manual.py
│   └── test_verification_manual.py
│
├── Create Admin/                   # Admin creation utilities
│   ├── create_super_admin.py       # Create super admin
│   ├── create_admin_user.py        # Create admin
│   └── create_moderator.py         # Create moderator
│
├── scripts/                        # Database maintenance scripts
│   ├── fix_db_schema.py            # Schema migration
│   ├── verify_schema.py            # Schema validation
│   └── add_contract_signatures.py  # Add signature columns
│
├── legal/                          # Legal documents
│   ├── PRIVACY_POLICY.md           # Privacy policy
│   └── TERMS_OF_SERVICE.md         # Terms of service
│
├── Docs & business artifacts/      # Documentation
│   └── business model/
│       └── BUSINESS_MODEL.md       # Revenue model & projections
│
├── Guides/                         # Implementation guides
│   ├── ADMIN_IMPLEMENTATION_GUIDE.md
│   ├── GITHUB_PROJECT_SETUP.md
│   ├── LEGAL_PROCESS.md
│   └── MILESTONE_6_IMPLEMENTATION.md
│
├── Security/                       # Security documentation
│   └── SECURITY_STRATEGY.md        # Security guidelines
│
└── txts/                           # Project notes
    ├── CHECKLIST.md                # Development checklist
    ├── concept.txt                 # Original concept document
    ├── MILESTONE_6_COMPLETED.md    # Milestone tracking
    └── MILESTONE_7_COMPLETED.md    # Admin system completion
```

---

## 🧪 Testing

### **Run All Tests**
```bash
pytest
```

### **Run with Coverage**
```bash
pytest --cov=. --cov-report=html
```

### **Run Specific Test File**
```bash
pytest tests/test_auth.py
pytest tests/test_admin.py
pytest tests/test_listings.py
```

### **Manual Testing**
```bash
# Run manual test suites
python "Manual tests/test_manual.py"
python "Manual tests/test_messaging_contracts_manual.py"
python "Manual tests/test_verification_manual.py"
```

### **Test Coverage**
Current test suite includes:
- ✅ User authentication and registration
- ✅ Marketplace listings CRUD
- ✅ Worker profiles
- ✅ Job applications
- ✅ Contracts and signatures
- ✅ Messaging system
- ✅ Forum posts and comments
- ✅ Admin moderation tools
- ✅ Rating system
- ✅ Verification workflow
- ✅ OTP authentication
- ✅ Boost functionality
- ✅ Audit logging
- ✅ Produce Assistant tools

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### **1. Fork the Repository**
```bash
git clone https://github.com/YOUR_USERNAME/FLB-Extended.git
```

### **2. Create a Feature Branch**
```bash
git checkout -b feature/your-feature-name
```

### **3. Make Your Changes**
- Follow PEP 8 style guidelines
- Write tests for new features
- Update documentation as needed

### **4. Test Your Changes**
```bash
pytest
```

### **5. Commit and Push**
```bash
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name
```

### **6. Open a Pull Request**
- Provide clear description of changes
- Reference any related issues
- Ensure all tests pass

### **Development Guidelines**
- Use descriptive variable and function names
- Add docstrings to all functions
- Follow existing code structure
- Update `README.md` for major changes
- Add tests for bug fixes

---

## 🛣️ Roadmap

### **Completed (Milestones 1-7)**
- ✅ Core authentication & user management
- ✅ Marketplace with image/video uploads
- ✅ Worker directory and profiles
- ✅ Jobs system with applications
- ✅ Contracts and digital signatures
- ✅ Wallet and payment integration (Interswitch)
- ✅ Messaging system
- ✅ Forum with voting and commenting
- ✅ Produce Assistant (3 AI tools)
- ✅ Verification system (ID + OTP)
- ✅ Three-tier admin system
- ✅ Reporting and moderation
- ✅ Boost functionality
- ✅ Rating system
- ✅ Audit logging
- ✅ Dark mode support

### **In Progress**
- 🔄 Job application frontend UI
- 🔄 Real-time notifications
- 🔄 WhatsApp/Telegram OTP integration

### **Planned (Future Milestones)**
- 📅 3D farm visualization for land listings
- 📅 Mobile app (React Native)
- 📅 Advanced analytics dashboard
- 📅 Bulk hiring tools for commercial farms
- 📅 Multi-language support (Hausa, Yoruba, Igbo)
- 📅 Integration with agricultural databases (NAFDAC, etc.)
- 📅 Insurance marketplace integration
- 📅 Equipment rental marketplace
- 📅 Weather forecasting integration
- 📅 Logistics and delivery tracking

---

## 📄 License

This project is licensed under the **MIT License** - see the LICENSE file for details.

---

## 📞 Contact

**Project Maintainer**: [Pingwyd](https://github.com/Pingwyd)

**Repository**: [https://github.com/Pingwyd/FLB-Extended](https://github.com/Pingwyd/FLB-Extended)

**Issues & Support**: [GitHub Issues](https://github.com/Pingwyd/FLB-Extended/issues)

**Documentation**: See `/api/docs` when running the application

---

## 🙏 Acknowledgments

- Nigerian agricultural community for inspiration and feedback
- Open-source contributors and maintainers
- Flask and SQLAlchemy communities
- TailwindCSS and Alpine.js teams
- Interswitch for payment infrastructure

---

## 📊 Project Status

**Current Version**: Alpha/Beta (Active Development)  
**Last Updated**: December 10, 2025  
**Python Version**: 3.13+  
**Database**: SQLite (dev) / PostgreSQL (production)

**Development Status**:
- ✅ Core features implemented and tested
- ✅ API endpoints functional
- 🔄 Frontend UI refinement ongoing
- 📅 Production deployment pending

---

**Built with ❤️ for Nigerian farmers, workers, and the agricultural ecosystem.**