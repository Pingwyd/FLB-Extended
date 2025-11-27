# FLB Extended — Nigerian Agricultural Platform

A comprehensive platform connecting farmers, workers, realtors, and service providers across Nigeria's agricultural ecosystem.

## 🌟 Project Overview

FLB Extended is a full-stack agricultural marketplace and assistance platform built with Flask and SQLAlchemy. The platform provides farmers with AI-powered tools for crop selection, cost management, and post-harvest storage, while also facilitating connections between farmers, agricultural workers, and land opportunities.

## ✅ Completed Milestones (11/11)

### Milestone 1: Authentication & User Management ✅
- User registration and login
- Multi-role support (Farmer, Worker, Landowner, Realtor)
- Password policy and rate limiting
- **Tests:** Passing

### Milestone 2: Document Verification ✅
- Document upload for user verification
- Admin approval workflow
- Audit logging for admin access
- **Tests:** Passing

### Milestone 3: Messaging & Contracts ✅
- Direct messaging between users
- Contract creation and digital signatures
- Two-party contract signing workflow
- **Tests:** Passing

### Milestone 4: Payments & Wallet ✅
- Virtual wallet system
- Interswitch integration (Sandbox)
- Transaction history and withdrawals
- **Tests:** Passing

### Milestone 5: Marketplace ✅
- **Real Estate Listings:** Land for sale/lease with filtering
- **Worker Profiles:** Skilled agricultural workers directory
- Full CRUD operations with authorization
- **Tests:** Passing

### Milestone 6: Produce Assistant ✅
- Cost Calculator
- Shelf Life Calculator
- AI Crop Recommender
- **Tests:** 57 passing

### Milestone 7: Admin System ✅
- Ban/Unban users
- Report system
- Audit logs
- **Tests:** Passing

### Milestone 8: Forum ✅
- Community discussions
- Q&A with voting
- Categories and moderation
- **Tests:** Passing

### Milestone 9: Ratings & Reviews ✅
- 5-star rating system
- Reviews for workers and realtors
- **Tests:** Passing

### Milestone 10: Security & Compliance ✅
- Secure headers (Talisman)
- Rate limiting
- Input validation
- Legal documents (ToS, Privacy Policy)

### Milestone 11: Testing & Deployment ✅
- CI/CD pipeline ready
- Docker support
- High test coverage

## 📊 Test Coverage

**Total: >150 Tests (All Passing)** 🎉
```
tests/test_app.py
tests/test_auth.py
tests/test_contracts.py
tests/test_listings.py
tests/test_messaging.py
tests/test_produce_assistant.py
tests/test_verification.py
tests/test_workers.py
tests/test_admin.py
tests/test_forum.py
tests/test_ratings.py
tests/test_payment_manual.py
tests/test_audit_logging.py
```

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Windows PowerShell (or bash/zsh on Linux/Mac)

### Installation

```powershell
# Clone the repository
git clone <repository-url>
cd "FLB extended"

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
# source .venv/bin/activate    # Linux/Mac

# Install dependencies
python -m pip install -r requirements.txt
```

### Running the Application

```powershell
# Start the Flask development server
python app.py

# The API will be available at http://localhost:5000
```

### Running Tests

```powershell
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_produce_assistant.py

# Run specific test class
python -m pytest tests/test_produce_assistant.py::TestCropRecommender
```

## 📁 Project Structure

```
FLB extended/
├── app.py                          # Main Flask application (1480+ lines)
├── models.py                       # SQLAlchemy models (513 lines)
├── calculator.py                   # Produce assistant algorithms (850+ lines)
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── tests/                          # Test suite (108 tests)
│   ├── conftest.py                # Test fixtures
│   ├── test_app.py                # Basic app tests
│   ├── test_auth.py               # Authentication tests
│   ├── test_contracts.py          # Contract workflow tests
│   ├── test_listings.py           # Real estate tests
│   ├── test_messaging.py          # Messaging tests
│   ├── test_produce_assistant.py  # Produce assistant tests (57 tests)
│   ├── test_verification.py       # Document verification tests
│   └── test_workers.py            # Worker profile tests
├── Guides/                         # Implementation guides
│   ├── MILESTONE_6_IMPLEMENTATION.md
│   ├── ADMIN_IMPLEMENTATION_GUIDE.md
│   └── GITHUB_PROJECT_SETUP.md
└── txts/                           # Documentation
    ├── MILESTONE_6_COMPLETED.md   # Detailed completion report
    └── CHECKLIST.md               # Project checklist
```

## 🔧 Tech Stack

- **Backend:** Flask 2.3.2
- **Database:** SQLAlchemy 1.4.48 (SQLite for development)
- **Authentication:** Flask-JWT-Extended 4.5.2
- **Password Hashing:** Werkzeug security
- **Testing:** pytest 7.4.0
- **Python:** 3.13.9

## 📱 API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login

### Verification
- `POST /verification/upload` - Upload verification document
- `GET /verification/documents/<user_id>` - Get user's documents
- `POST /verification/verify/<doc_id>` - Admin document approval

### Messaging
- `POST /messaging/send` - Send message
- `GET /messaging/<user_id>` - Get user's messages
- `POST /messaging/read/<message_id>` - Mark message as read

### Contracts
- `POST /contracts/create` - Create contract
- `POST /contracts/<contract_id>/sign` - Sign contract
- `GET /contracts/user/<user_id>` - Get user's contracts

### Marketplace - Real Estate
- `POST /listings` - Create listing
- `GET /listings` - Get all listings (with filters)
- `GET /listings/<listing_id>` - Get single listing
- `PUT /listings/<listing_id>` - Update listing
- `DELETE /listings/<listing_id>` - Delete listing
- `GET /listings/user/<user_id>` - Get user's listings

### Marketplace - Workers
- `POST /workers` - Create worker profile
- `GET /workers` - Get all workers (with filters)
- `GET /workers/<worker_id>` - Get single worker
- `PUT /workers/<worker_id>` - Update worker profile
- `GET /workers/user/<user_id>` - Get worker by user ID

### Produce Assistant - Cost Calculator
- `POST /produce-assistant/calculate-cost` - Calculate production costs
- `GET /produce-assistant/calculations/<user_id>` - Get user's calculations
- `GET /produce-assistant/calculation/<calc_id>` - Get calculation details

### Produce Assistant - Shelf Life
- `POST /produce-assistant/predict-shelf-life` - Predict shelf life
- `GET /produce-assistant/predictions/<user_id>` - Get user's predictions
- `GET /produce-assistant/prediction/<pred_id>` - Get prediction details

### Produce Assistant - Crop Recommender
- `POST /produce-assistant/recommend-crops` - Get crop recommendations
- `GET /produce-assistant/recommendations/<user_id>` - Get user's recommendations
- `GET /produce-assistant/recommendation/<rec_id>` - Get recommendation details

## 🌾 Produce Assistant Features

### Cost Calculator
Calculate complete production costs with breakdown:
- Land preparation
- Seeds/seedlings
- Fertilizers
- Labor
- Irrigation
- Pesticides
- Harvesting
- Transportation

**Output:** Total cost, profit projections, cost-per-kg, profitability rating

### Shelf Life Calculator
Predict storage duration for 23 produce types:
- **Vegetables:** Tomato, Onion, Pepper, Cabbage, Okra, Lettuce, Cucumber
- **Fruits:** Watermelon, Orange, Banana, Mango, Pineapple, Pawpaw
- **Grains:** Maize, Rice, Sorghum, Millet
- **Legumes:** Beans, Groundnut, Soybean
- **Tubers:** Cassava, Yam, Sweet Potato

**Output:** Shelf life days, quality timeline, optimal storage conditions, cost estimates

### AI Crop Recommender
Get data-driven crop recommendations based on:
- Soil type (loamy, sandy, clay, etc.)
- Soil pH (4.5-8.0 range)
- Climate zone (tropical, arid, temperate)
- Rainfall (300-2000mm/year)
- Temperature (15-35°C)
- Growing season (rainy/dry/year-round)
- Experience level (beginner/intermediate/expert)
- Budget category (low/medium/high)
- Irrigation availability

**15 Nigerian Crops:** Maize, Rice, Cassava, Yam, Tomato, Pepper, Beans, Groundnut, Sorghum, Millet, Okra, Watermelon, Cucumber, Cabbage, Onion

**Output:** Top 5 recommendations, suitability scores, risk factors, success factors, market potential

## 🎯 Upcoming Milestones

### Milestone 4: Payments & Wallet System (Pending)
- Wallet functionality
- Payment integration
- Transaction history
- Escrow for contracts

### Milestone 7: Admin System
- Super Admin (platform management)
- Moderators (content/user moderation)
- Support Staff (customer assistance)
- Three-tier privilege system

### Milestone 7.5: Community Forum
- Discussion boards
- Knowledge sharing
- Farmer-to-farmer support
- Topic categorization

### Milestone 8: Security Hardening
- Input sanitization
- Rate limiting
- SQL injection prevention
- XSS protection
- Security audit

### Milestone 9: CI/CD & Deployment
- Automated testing pipeline
- GitHub Actions integration
- Production deployment
- Monitoring & logging
- Performance optimization

## 📝 Documentation

Detailed documentation available in:
- `txts/MILESTONE_6_COMPLETED.md` - Complete Milestone 6 report
- `Guides/MILESTONE_6_IMPLEMENTATION.md` - Implementation guide
- `Guides/ADMIN_IMPLEMENTATION_GUIDE.md` - Admin system planning
- `Guides/GITHUB_PROJECT_SETUP.md` - GitHub project setup

## 🤝 Contributing

This is a learning project. Contributions, suggestions, and feedback are welcome!

## 📄 License

[Your License Here]

## 👨‍💻 Author

Prosperr

---

**Project Status:** Active Development | **Completion:** 67% (6/9 milestones)
#   F L B - E x t e n d e d  
 #   F L B - E x t e n d e d  
 