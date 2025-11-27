from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import declarative_base, relationship, backref
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    full_name = Column(String(200), nullable =False)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    account_type = Column(String(50), nullable=False)  # farmer, realtor, worker, moderator, admin, super_admin
    profile_picture = Column(String(500), nullable=True) # URL to profile picture
    phone_number = Column(String(20), nullable=True)
    bio = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)
    verified = Column(Boolean, default=False) # KYC Verification
    email_verified = Column(Boolean, default=False) # Email Verification
    otp_code = Column(String(6), nullable=True)
    otp_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    # Admin-related fields
    is_banned = Column(Boolean, default=False)
    banned_at = Column(DateTime, nullable=True)
    banned_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    ban_reason = Column(Text, nullable=True)
    
    # Rating fields
    average_rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        # Do not expose password hash
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'account_type': self.account_type,
            'profile_picture': self.profile_picture,
            'phone_number': self.phone_number,
            'bio': self.bio,
            'location': self.location,
            'verified': self.verified,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'is_banned': self.is_banned,
            'banned_at': self.banned_at.isoformat() if self.banned_at is not None else None,
            'ban_reason': self.ban_reason,
            'average_rating': self.average_rating,
            'rating_count': self.rating_count
        }


class VerificationDocument(Base):
    __tablename__ = 'verification_documents'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    document_type = Column(String(50), nullable=False)  # NIN, passport, drivers_license
    document_number = Column(String(100), nullable=False)
    document_path = Column(String(500), nullable=True)  # Optional: path to uploaded file
    status = Column(String(50), default='pending')  # pending, approved, rejected
    admin_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relationships
    user = relationship('User', foreign_keys=[user_id], backref='verification_documents')
    reviewer = relationship('User', foreign_keys=[reviewed_by])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'document_type': self.document_type,
            'document_number': self.document_number,
            'document_path': self.document_path,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewed_by': self.reviewed_by
        }


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    recipient_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    subject = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    read_at = Column(DateTime, nullable=True)

    # Relationships
    sender = relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = relationship('User', foreign_keys=[recipient_id], backref='received_messages')

    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'subject': self.subject,
            'content': self.content,
            'read': self.read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }


class Contract(Base):
    __tablename__ = 'contracts'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    party_a_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Creator
    party_b_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Other party
    terms = Column(Text, nullable=False)  # Contract terms/conditions
    amount = Column(Float, nullable=True)  # Amount in Naira
    status = Column(String(50), default='draft')  # draft, pending, signed, breached, cancelled
    party_a_signed = Column(Boolean, default=False)
    party_b_signed = Column(Boolean, default=False)
    party_a_signed_at = Column(DateTime, nullable=True)
    party_b_signed_at = Column(DateTime, nullable=True)
    party_a_signature = Column(Text, nullable=True) # Base64 encoded signature image
    party_b_signature = Column(Text, nullable=True) # Base64 encoded signature image
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    party_a = relationship('User', foreign_keys=[party_a_id], backref='contracts_created')
    party_b = relationship('User', foreign_keys=[party_b_id], backref='contracts_received')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'party_a_id': self.party_a_id,
            'party_b_id': self.party_b_id,
            'terms': self.terms,
            'amount': self.amount,
            'status': self.status,
            'party_a_signed': self.party_a_signed,
            'party_b_signed': self.party_b_signed,
            'party_a_signed_at': self.party_a_signed_at.isoformat() if self.party_a_signed_at else None,
            'party_b_signed_at': self.party_b_signed_at.isoformat() if self.party_b_signed_at else None,
            'party_a_signature': self.party_a_signature,
            'party_b_signature': self.party_b_signature,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class Listing(Base):
    __tablename__ = 'listings'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    listing_type = Column(String(50), nullable=False)  # land_sale, land_rent
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Location details
    location_state = Column(String(100), nullable=True)
    location_area = Column(String(200), nullable=True)
    location_address = Column(Text, nullable=True)
    
    # Land/property specific fields
    size_value = Column(Integer, nullable=True)  # Numeric size
    size_unit = Column(String(50), nullable=True)  # hectares, acres, sqm
    
    # Pricing
    price = Column(Float, nullable=False)  # Price in Naira
    price_type = Column(String(50), default='sale')  # sale, rent_monthly, rent_yearly
    
    # Media attachments
    images = Column(Text, nullable=True)  # JSON array of image URLs/paths
    videos = Column(Text, nullable=True)  # JSON array of video URLs/paths
    model_3d_url = Column(String(500), nullable=True)  # URL to 3D model/virtual tour
    
    # Status and visibility
    status = Column(String(50), default='active')  # active, sold, rented, inactive
    featured = Column(Boolean, default=False)  # Premium/boosted listing
    boost_expiry = Column(DateTime, nullable=True)  # When the boost expires
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))
    views = Column(Integer, default=0)
    
    # Relationship
    owner = relationship('User', foreign_keys=[owner_id], backref='listings')
    
    def to_dict(self):
        import json
        # Parse images if stored as JSON string
        images_list = None
        if self.images:
            try:
                images_list = json.loads(self.images)
            except:
                images_list = []
        
        # Parse videos if stored as JSON string
        videos_list = None
        if self.videos:
            try:
                videos_list = json.loads(self.videos)
            except:
                videos_list = []
        
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'listing_type': self.listing_type,
            'title': self.title,
            'description': self.description,
            'location_state': self.location_state,
            'location_area': self.location_area,
            'location_address': self.location_address,
            'size_value': self.size_value,
            'size_unit': self.size_unit,
            'price': self.price,
            'price_type': self.price_type,
            'images': images_list,
            'videos': videos_list,
            'model_3d_url': self.model_3d_url,
            'status': self.status,
            'featured': self.featured,
            'boost_expiry': self.boost_expiry.isoformat() if self.boost_expiry else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'views': self.views
        }


class WorkerProfile(Base):
    __tablename__ = 'worker_profiles'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    # Worker details
    specialization = Column(String(100), nullable=False)  # fumigation, fertilizer, labor, specialist
    bio = Column(Text, nullable=True)
    experience_years = Column(Integer, nullable=True)
    
    # Skills (stored as JSON array)
    skills = Column(Text, nullable=True)  # JSON array: ["planting", "irrigation", "pesticide application"]
    
    # Availability and rates
    available = Column(Boolean, default=True)
    hourly_rate = Column(Float, nullable=True)  # Rate in Naira per hour
    daily_rate = Column(Float, nullable=True)  # Rate in Naira per day
    
    # Location
    location_state = Column(String(100), nullable=True)
    location_area = Column(String(200), nullable=True)
    willing_to_travel = Column(Boolean, default=False)
    
    # Portfolio/certifications
    certifications = Column(Text, nullable=True)  # JSON array of certification names/URLs
    portfolio_images = Column(Text, nullable=True)  # JSON array of image URLs
    
    # Rating and statistics
    rating = Column(Integer, default=0)  # Average rating (0-5 scale, store as 0-50 for decimals)
    total_jobs = Column(Integer, default=0)
    
    # Boost/Visibility
    is_boosted = Column(Boolean, default=False)
    boost_expiry = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    # Relationship
    user = relationship('User', foreign_keys=[user_id], backref='worker_profile')
    
    def to_dict(self):
        import json
        
        # Parse JSON fields
        skills_list = []
        if self.skills:
            try:
                skills_list = json.loads(self.skills)
            except:
                skills_list = []
        
        certifications_list = []
        if self.certifications:
            try:
                certifications_list = json.loads(self.certifications)
            except:
                certifications_list = []
        
        portfolio_list = []
        if self.portfolio_images:
            try:
                portfolio_list = json.loads(self.portfolio_images)
            except:
                portfolio_list = []
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.user.full_name if self.user else "Unknown",
            'verified': self.user.is_verified if self.user else False,
            'specialization': self.specialization,
            'bio': self.bio,
            'experience_years': self.experience_years,
            'skills': skills_list,
            'available': self.available,
            'hourly_rate': self.hourly_rate,
            'daily_rate': self.daily_rate,
            'location_state': self.location_state,
            'location_area': self.location_area,
            'willing_to_travel': self.willing_to_travel,
            'certifications': certifications_list,
            'portfolio_images': portfolio_list,
            'rating': self.rating,
            'total_jobs': self.total_jobs,
            'is_boosted': self.is_boosted,
            'boost_expiry': self.boost_expiry.isoformat() if self.boost_expiry else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ProduceCalculation(Base):
    __tablename__ = 'produce_calculations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Input parameters
    crop_type = Column(String(100), nullable=False)
    season = Column(String(50), nullable=True)  # dry, rainy, harmattan
    land_size_hectares = Column(Integer, nullable=True)
    expected_yield_kg = Column(Integer, nullable=False)
    
    # Labor costs
    num_workers = Column(Integer, nullable=True)
    labor_cost = Column(Float, default=0)  # Total labor cost in Naira
    
    # Material costs
    seed_cost = Column(Float, default=0)
    fertilizer_cost = Column(Float, default=0)
    pesticide_cost = Column(Float, default=0)
    water_cost = Column(Float, default=0)
    electricity_cost = Column(Float, default=0)
    transport_cost = Column(Float, default=0)
    other_expenses = Column(Float, default=0)
    
    # Financial calculations (computed)
    total_cost = Column(Float, nullable=False)  # Sum of all costs
    profit_margin_percent = Column(Integer, nullable=False)  # Desired profit %
    cost_per_kg = Column(Float, nullable=False)  # Cost per kg in Naira
    selling_price_per_kg = Column(Float, nullable=False)  # Suggested selling price in Naira
    total_revenue = Column(Float, nullable=False)  # If sold at suggested price
    total_profit = Column(Float, nullable=False)  # Revenue - Cost
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    # Relationship
    user = relationship('User', foreign_keys=[user_id], backref='produce_calculations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'crop_type': self.crop_type,
            'season': self.season,
            'land_size_hectares': self.land_size_hectares,
            'expected_yield_kg': self.expected_yield_kg,
            'num_workers': self.num_workers,
            'labor_cost': self.labor_cost,
            'seed_cost': self.seed_cost,
            'fertilizer_cost': self.fertilizer_cost,
            'pesticide_cost': self.pesticide_cost,
            'water_cost': self.water_cost,
            'electricity_cost': self.electricity_cost,
            'transport_cost': self.transport_cost,
            'other_expenses': self.other_expenses,
            'total_cost': self.total_cost,
            'profit_margin_percent': self.profit_margin_percent,
            'cost_per_kg': self.cost_per_kg,
            'selling_price_per_kg': self.selling_price_per_kg,
            'total_revenue': self.total_revenue,
            'total_profit': self.total_profit,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'breakdown': {
                'labor': self.labor_cost,
                'seeds': self.seed_cost,
                'fertilizer': self.fertilizer_cost,
                'pesticide': self.pesticide_cost,
                'water': self.water_cost,
                'electricity': self.electricity_cost,
                'transport': self.transport_cost,
                'other': self.other_expenses
            }
        }


class ShelfLifePrediction(Base):
    """Model for produce shelf life predictions"""
    __tablename__ = 'shelf_life_predictions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Input parameters
    produce_type = Column(String(100), nullable=False)  # e.g., 'tomato', 'maize', 'rice'
    quantity_kg = Column(Float, nullable=False)
    harvest_date = Column(DateTime, nullable=False)
    
    # Storage conditions
    storage_method = Column(String(50), nullable=False)  # e.g., 'cold_storage', 'room_temp', 'refrigerated', 'warehouse'
    storage_temperature_celsius = Column(Float, nullable=True)  # Actual or estimated temp
    storage_humidity_percent = Column(Float, nullable=True)  # Humidity level
    packaging_type = Column(String(50), nullable=True)  # e.g., 'sealed', 'open', 'vacuum', 'crates'
    
    # Predictions
    predicted_shelf_life_days = Column(Integer, nullable=False)
    quality_degradation_rate = Column(Float, nullable=False)  # Percentage quality loss per day
    optimal_sell_by_date = Column(DateTime, nullable=False)  # Best quality date
    spoilage_date = Column(DateTime, nullable=False)  # Estimated spoilage date
    
    # Quality milestones
    excellent_quality_until = Column(DateTime, nullable=True)  # 100-90% quality
    good_quality_until = Column(DateTime, nullable=True)  # 89-70% quality
    fair_quality_until = Column(DateTime, nullable=True)  # 69-50% quality
    
    # Additional info
    storage_cost_per_day = Column(Float, nullable=True, default=0)  # In Naira
    estimated_total_storage_cost = Column(Float, nullable=True, default=0)  # In Naira
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    # Relationship
    user = relationship('User')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'produce_type': self.produce_type,
            'quantity_kg': self.quantity_kg,
            'harvest_date': self.harvest_date.isoformat() if self.harvest_date else None,
            'storage_method': self.storage_method,
            'storage_temperature_celsius': self.storage_temperature_celsius,
            'storage_humidity_percent': self.storage_humidity_percent,
            'packaging_type': self.packaging_type,
            'predicted_shelf_life_days': self.predicted_shelf_life_days,
            'quality_degradation_rate': self.quality_degradation_rate,
            'optimal_sell_by_date': self.optimal_sell_by_date.isoformat() if self.optimal_sell_by_date else None,
            'spoilage_date': self.spoilage_date.isoformat() if self.spoilage_date else None,
            'excellent_quality_until': self.excellent_quality_until.isoformat() if self.excellent_quality_until else None,
            'good_quality_until': self.good_quality_until.isoformat() if self.good_quality_until else None,
            'fair_quality_until': self.fair_quality_until.isoformat() if self.fair_quality_until else None,
            'storage_cost_per_day': self.storage_cost_per_day,
            'estimated_total_storage_cost': self.estimated_total_storage_cost,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'storage_conditions': {
                'method': self.storage_method,
                'temperature': self.storage_temperature_celsius,
                'humidity': self.storage_humidity_percent,
                'packaging': self.packaging_type
            }
        }


class CropRecommendation(Base):
    """Model for AI-powered crop recommendations"""
    __tablename__ = 'crop_recommendations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Input parameters (land conditions)
    location = Column(String(200), nullable=False)  # State/region
    soil_type = Column(String(100), nullable=False)  # e.g., 'loamy', 'sandy', 'clay', 'silt'
    soil_ph = Column(Float, nullable=True)  # pH level 0-14
    land_size_hectares = Column(Float, nullable=False)
    
    # Climate data
    climate_zone = Column(String(100), nullable=False)  # e.g., 'tropical', 'arid', 'temperate'
    average_rainfall_mm = Column(Float, nullable=True)  # Annual rainfall
    average_temperature_celsius = Column(Float, nullable=True)  # Average temperature
    season = Column(String(50), nullable=False)  # e.g., 'dry_season', 'rainy_season', 'harmattan'
    
    # Farming preferences
    irrigation_available = Column(Boolean, default=False)
    budget_category = Column(String(50), nullable=True)  # e.g., 'low', 'medium', 'high'
    experience_level = Column(String(50), nullable=True)  # e.g., 'beginner', 'intermediate', 'expert'
    
    # Top recommendations (stored as JSON-like text for simplicity)
    recommended_crops = Column(Text, nullable=False)  # Top 5 crops with scores
    
    # Analysis results
    confidence_score = Column(Float, nullable=False)  # 0-100 overall confidence
    market_potential = Column(String(50), nullable=True)  # e.g., 'high', 'medium', 'low'
    estimated_yield_range = Column(String(100), nullable=True)  # e.g., '2000-3000 kg/hectare'
    
    # Additional insights
    risk_factors = Column(Text, nullable=True)  # Potential challenges
    success_factors = Column(Text, nullable=True)  # Keys to success
    alternative_crops = Column(Text, nullable=True)  # Backup options
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    # Relationship
    user = relationship('User')
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'user_id': self.user_id,
            'location': self.location,
            'land_conditions': {
                'soil_type': self.soil_type,
                'soil_ph': self.soil_ph,
                'land_size_hectares': self.land_size_hectares
            },
            'climate_data': {
                'climate_zone': self.climate_zone,
                'average_rainfall_mm': self.average_rainfall_mm,
                'average_temperature_celsius': self.average_temperature_celsius,
                'season': self.season
            },
            'farming_preferences': {
                'irrigation_available': self.irrigation_available,
                'budget_category': self.budget_category,
                'experience_level': self.experience_level
            },
            'recommended_crops': json.loads(self.recommended_crops) if self.recommended_crops else [],
            'confidence_score': self.confidence_score,
            'market_potential': self.market_potential,
            'estimated_yield_range': self.estimated_yield_range,
            'risk_factors': json.loads(self.risk_factors) if self.risk_factors else [],
            'success_factors': json.loads(self.success_factors) if self.success_factors else [],
            'alternative_crops': json.loads(self.alternative_crops) if self.alternative_crops else [],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Report(Base):
    """Model for user reports of violations (fraud, spam, harassment, inappropriate content)"""
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reported_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    reported_listing_id = Column(Integer, ForeignKey('listings.id'), nullable=True)
    reported_worker_id = Column(Integer, ForeignKey('worker_profiles.id'), nullable=True)
    report_type = Column(String(50), nullable=False)  # fraud, spam, harassment, inappropriate, scam, fake_listing
    description = Column(Text, nullable=False)
    status = Column(String(50), default='pending')  # pending, under_review, resolved, dismissed
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'reporter_id': self.reporter_id,
            'reported_user_id': self.reported_user_id,
            'reported_listing_id': self.reported_listing_id,
            'reported_worker_id': self.reported_worker_id,
            'report_type': self.report_type,
            'description': self.description,
            'status': self.status,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'resolution_notes': self.resolution_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AdminAuditLog(Base):
    """Model for tracking all admin/moderator actions for accountability and security"""
    __tablename__ = 'admin_audit_logs'
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action = Column(String(100), nullable=False)  # ban_user, unban_user, delete_listing, hide_listing, approve_verification, reject_verification, resolve_report, create_moderator, create_admin
    target_type = Column(String(50), nullable=False)  # user, listing, worker_profile, verification_document, report
    target_id = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    details = Column(Text, nullable=True)  # JSON or additional context
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'action': self.action,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'reason': self.reason,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ForumPost(Base):
    __tablename__ = 'forum_posts'
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # planting_advice, pest_control, equipment, general, marketplace
    location_state = Column(String(100), nullable=True) # For location-specific advice
    crop_type = Column(String(100), nullable=True) # For crop-specific advice
    
    upvotes = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    comments = relationship("ForumComment", backref="post", cascade="all, delete-orphan")
    author = relationship("User", backref="forum_posts")
    
    def to_dict(self):
        return {
            'id': self.id,
            'author_id': self.author_id,
            'author_name': self.author.full_name if self.author else 'Unknown',
            'author_is_banned': self.author.is_banned if self.author else False,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'location_state': self.location_state,
            'crop_type': self.crop_type,
            'upvotes': self.upvotes,
            'view_count': self.view_count,
            'is_pinned': self.is_pinned,
            'is_locked': self.is_locked,
            'comments_count': len(self.comments),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ForumComment(Base):
    __tablename__ = 'forum_comments'
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('forum_posts.id'), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('forum_comments.id'), nullable=True) # For nested comments
    content = Column(Text, nullable=False)
    upvotes = Column(Integer, default=0)
    is_accepted_answer = Column(Boolean, default=False) # For Q&A style
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    # Relationships
    author = relationship("User", backref="forum_comments")
    replies = relationship("ForumComment", 
                          backref=backref('parent', remote_side=[id]),
                          cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'author_id': self.author_id,
            'author_name': self.author.full_name if self.author else 'Unknown',
            'author_is_banned': self.author.is_banned if self.author else False,
            'parent_id': self.parent_id,
            'content': self.content,
            'upvotes': self.upvotes,
            'is_accepted_answer': self.is_accepted_answer,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'replies': [reply.to_dict() for reply in self.replies]
        }


class ForumVote(Base):
    __tablename__ = 'forum_votes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('forum_posts.id'), nullable=True)
    comment_id = Column(Integer, ForeignKey('forum_comments.id'), nullable=True)
    vote_type = Column(String(10), default='upvote') # upvote, downvote

class Wallet(Base):
    __tablename__ = 'wallets'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    balance = Column(Float, default=0.0)
    currency = Column(String(3), default='NGN')
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'balance': self.balance,
            'currency': self.currency,
            'updated_at': self.updated_at.isoformat() if self.updated_at else self.created_at.isoformat()
        }

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey('wallets.id'), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(20), nullable=False)  # deposit, withdrawal, payment, refund
    status = Column(String(20), default='pending')  # pending, success, failed
    reference = Column(String(100), unique=True, nullable=False) # Payment gateway reference
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'wallet_id': self.wallet_id,
            'amount': self.amount,
            'transaction_type': self.transaction_type,
            'status': self.status,
            'reference': self.reference,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class BankAccount(Base):
    __tablename__ = 'bank_accounts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    bank_name = Column(String(100), nullable=False)
    account_number = Column(String(20), nullable=False)
    account_name = Column(String(200), nullable=False)
    bank_code = Column(String(10), nullable=True) # Bank code for transfers
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    # Relationship
    user = relationship('User', backref='bank_accounts')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'bank_name': self.bank_name,
            'account_number': self.account_number,
            'account_name': self.account_name,
            'bank_code': self.bank_code,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Rating(Base):
    __tablename__ = 'ratings'
    id = Column(Integer, primary_key=True)
    rater_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    rated_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    rating_value = Column(Integer, nullable=False) # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    # Relationships
    rater = relationship('User', foreign_keys=[rater_id], backref='ratings_given')
    rated_user = relationship('User', foreign_keys=[rated_user_id], backref='ratings_received')

    def to_dict(self):
        return {
            'id': self.id,
            'rater_id': self.rater_id,
            'rated_user_id': self.rated_user_id,
            'rating_value': self.rating_value,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    employer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)
    salary_range = Column(String(100), nullable=True)
    status = Column(String(50), default='open')  # open, closed, filled
    
    # Boost/Visibility
    is_boosted = Column(Boolean, default=False)
    boost_expiry = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    # Relationship
    employer = relationship('User', backref='jobs_posted')

    def to_dict(self):
        return {
            'id': self.id,
            'employer_id': self.employer_id,
            'title': self.title,
            'description': self.description,
            'requirements': self.requirements,
            'location': self.location,
            'salary_range': self.salary_range,
            'status': self.status,
            'is_boosted': self.is_boosted,
            'boost_expiry': self.boost_expiry.isoformat() if self.boost_expiry else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class JobApplication(Base):
    __tablename__ = 'job_applications'
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    applicant_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(50), default='pending')  # pending, accepted, rejected
    cover_letter = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    job = relationship('Job', backref='applications')
    applicant = relationship('User', backref='job_applications')

    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'applicant_id': self.applicant_id,
            'applicant_name': self.applicant.full_name if self.applicant else "Unknown",
            'applicant_email': self.applicant.email if self.applicant else "",
            'status': self.status,
            'cover_letter': self.cover_letter,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
