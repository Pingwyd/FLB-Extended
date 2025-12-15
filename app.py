import werkzeug
if not hasattr(werkzeug, '__version__'):
    # Some werkzeug builds don't expose __version__; provide a fallback so Flask test client can set a user-agent.
    setattr(werkzeug, '__version__', '0')

import os
import logging
import requests
import uuid
import re
import time
import shutil
import json
import csv
import io
from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for, Response
import config
import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from schemas import BanUserSchema, CreateModeratorSchema, CreateAdminSchema, ResolveReportSchema
from marshmallow import ValidationError
from flask_talisman import Talisman
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint


def create_app():
    app = Flask(__name__)
    # record process start time for uptime reporting
    app.start_time = time.time()
    # Ensure data directory and health history persistence exist on startup
    try:
        DATA_DIR_STARTUP = os.path.join(config.BASE_DIR, 'data')
        os.makedirs(DATA_DIR_STARTUP, exist_ok=True)
        history_path_startup = os.path.join(DATA_DIR_STARTUP, 'health_history.json')
        # If no history exists but a seed file is present, copy it; otherwise create an empty list
        if not os.path.exists(history_path_startup):
            seed_path = os.path.join(config.BASE_DIR, 'data', 'health_history_seed.json')
            if os.path.exists(seed_path):
                try:
                    shutil.copy(seed_path, history_path_startup)
                except Exception:
                    with open(history_path_startup, 'w', encoding='utf-8') as hf:
                        json.dump([], hf)
            else:
                with open(history_path_startup, 'w', encoding='utf-8') as hf:
                    json.dump([], hf)
    except Exception:
        # Non-fatal: continue even if data dir bootstrap fails
        pass
    
    # Enable CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Enable security headers
    # Define Content Security Policy to allow CDNs for Tailwind, Alpine, etc.
    csp = {
        'default-src': ["'self'"],
        'script-src': [
            "'self'",
            "'unsafe-inline'",
            "'unsafe-eval'",
            "cdn.tailwindcss.com",
            "cdn.jsdelivr.net",
            "cdnjs.cloudflare.com"
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",
            "fonts.googleapis.com",
            "cdnjs.cloudflare.com"
        ],
        'font-src': [
            "'self'",
            "fonts.gstatic.com",
            "cdnjs.cloudflare.com"
        ],
        'img-src': ["'self'", "data:", "https:"],
        'connect-src': ["'self'", "https:"]
    }

    # Force HTTPS only in production to avoid issues during local testing
    Talisman(app, 
             force_https=os.environ.get('FLASK_ENV') == 'production',
             content_security_policy=csp
    )

    # Initialize Limiter
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "100 per hour"],
        storage_uri=os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    )

    # Swagger UI configuration
    # Serve swagger UI at a dedicated path so /api/docs can be a documentation landing page
    SWAGGER_URL = '/api/docs/ui'
    API_URL = '/static/openapi.yaml'

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "FLB Extended API"
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    # Initialize database per app instance
    db_available = False
    session_local = None
    user_model = None
    verification_doc_model = None
    message_model = None
    contract_model = None
    listing_model = None
    worker_profile_model = None
    produce_calculation_model = None
    shelf_life_prediction_model = None
    crop_recommendation_model = None
    report_model = None
    admin_audit_log_model = None
    forum_post_model = None
    forum_comment_model = None
    forum_vote_model = None
    rating_model = None
    wallet_model = None
    transaction_model = None
    bank_account_model = None
    task_model = None
    
    try:
        from sqlalchemy import create_engine, func
        from sqlalchemy.orm import sessionmaker, joinedload
        from models import (
            Base,
            User as ModelUser,
            VerificationDocument as VerificationDocModel,
            Message as MessageModel,
            Contract as ContractModel,
            Listing as ListingModel,
            WorkerProfile as WorkerProfileModel,
            ProduceCalculation as ProduceCalculationModel,
            ShelfLifePrediction as ShelfLifePredictionModel,
            CropRecommendation as CropRecommendationModel,
            Report as ReportModel,
            AdminAuditLog as AdminAuditLogModel,
            ForumPost as ForumPostModel,
            ForumComment as ForumCommentModel,
            ForumVote as ForumVoteModel,
            Rating as RatingModel,
            Wallet as WalletModel,
            Transaction as TransactionModel,
            BankAccount as BankAccountModel,
            Job as JobModel,
            JobApplication as JobApplicationModel,
            Task as TaskModel,
        )

        engine = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=False)
        session_local = sessionmaker(bind=engine)

        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)

        user_model = ModelUser
        verification_doc_model = VerificationDocModel
        job_model = JobModel
        job_application_model = JobApplicationModel
        task_model = TaskModel
        message_model = MessageModel
        contract_model = ContractModel
        listing_model = ListingModel
        worker_profile_model = WorkerProfileModel
        produce_calculation_model = ProduceCalculationModel
        shelf_life_prediction_model = ShelfLifePredictionModel
        crop_recommendation_model = CropRecommendationModel
        report_model = ReportModel
        admin_audit_log_model = AdminAuditLogModel
        forum_post_model = ForumPostModel
        forum_comment_model = ForumCommentModel
        forum_vote_model = ForumVoteModel
        rating_model = RatingModel
        wallet_model = WalletModel
        transaction_model = TransactionModel
        bank_account_model = BankAccountModel
        produce_calculation_model = ProduceCalculationModel
        shelf_life_prediction_model = ShelfLifePredictionModel
        crop_recommendation_model = CropRecommendationModel
        report_model = ReportModel
        admin_audit_log_model = AdminAuditLogModel
        forum_post_model = ForumPostModel
        forum_comment_model = ForumCommentModel
        forum_vote_model = ForumVoteModel
        db_available = True
    except Exception:
        # SQLAlchemy or model initialization failed
        db_available = False

    # ========== Authorization Decorators ==========
    from functools import wraps
    
    def require_moderator(f):
        """Decorator to require moderator, admin, or super_admin access"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not db_available:
                return jsonify({'error': 'Database not available'}), 500
            
            # Get user_id from request (json body or query param)
            user_id = None
            if request.is_json:
                user_id = request.json.get('admin_id')
            if not user_id:
                user_id = request.args.get('admin_id')
                
            if not user_id:
                return jsonify({'error': 'admin_id required'}), 401
            
            session = session_local()
            user = session.query(user_model).filter_by(id=user_id).first()
            session.close()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if user.account_type not in ['moderator', 'admin', 'super_admin']:
                return jsonify({'error': 'Moderator access required'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    
    def require_admin(f):
        """Decorator to require admin or super_admin access"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not db_available:
                return jsonify({'error': 'Database not available'}), 500
            
            # Get user_id from request (json body or query param)
            user_id = None
            if request.is_json:
                user_id = request.json.get('admin_id')
            if not user_id:
                user_id = request.args.get('admin_id')

            if not user_id:
                return jsonify({'error': 'admin_id required'}), 401
            
            session = session_local()
            user = session.query(user_model).filter_by(id=user_id).first()
            session.close()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if user.account_type not in ['admin', 'super_admin']:
                return jsonify({'error': 'Admin access required'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    
    def require_super_admin(f):
        """Decorator to require super_admin access only"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not db_available:
                return jsonify({'error': 'Database not available'}), 500
            
            # Get user_id from request (json body or query param)
            user_id = None
            if request.is_json:
                user_id = request.json.get('admin_id')
            if not user_id:
                user_id = request.args.get('admin_id')

            if not user_id:
                return jsonify({'error': 'admin_id required'}), 401
            
            session = session_local()
            user = session.query(user_model).filter_by(id=user_id).first()
            session.close()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if user.account_type != 'super_admin':
                return jsonify({'error': 'Super Admin access required'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    
    def log_admin_action(admin_id, action, target_type, target_id, reason=None, details=None):
        """Helper function to log admin actions to audit log"""
        if not db_available:
            return
        
        session = session_local()
        try:
            log_entry = admin_audit_log_model(
                admin_id=admin_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                reason=reason,
                details=details,
                ip_address=request.remote_addr if request else None
            )
            session.add(log_entry)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    def record_admin_action(action, target_type='admin_page', target_id=None):
        """Try to extract an admin_id from the request and write an audit log entry."""
        admin_id = None
        try:
            if request.is_json:
                admin_id = request.json.get('admin_id')
        except Exception:
            pass
        if not admin_id:
            admin_id = request.args.get('admin_id')
        # fallback to flask session if present
        try:
            from flask import session as flask_session
            if not admin_id and flask_session is not None:
                admin_id = flask_session.get('user_id')
        except Exception:
            pass

        if admin_id:
            try:
                log_admin_action(admin_id=admin_id, action=action, target_type=target_type, target_id=target_id)
            except Exception:
                pass

    @app.route('/api/admin/verifications', methods=['GET'])
    @require_admin
    def api_admin_verifications():
        """Return pending verification documents grouped with user info for admin UI"""
        if not db_available or session_local is None or verification_doc_model is None:
            return jsonify({'error': 'database not available'}), 503

        session = session_local()
        try:
            pending_docs = session.query(verification_doc_model).filter_by(status='pending').all()
            results = []
            for doc in pending_docs:
                user = session.query(user_model).filter_by(id=doc.user_id).first()
                results.append({
                    'doc': doc.to_dict(),
                    'user': user.to_dict() if user else None
                })
            try:
                record_admin_action('api_view_verifications', 'verification')
            except Exception:
                pass
            return jsonify(results), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    # Expose a human-friendly API docs landing page at /api/docs (does not auto-open Swagger UI)
    @app.route('/api/docs', strict_slashes=False)
    def api_docs_page():
        return render_template('api_docs.html')

    # Frontend Routes
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login-page')
    def login_page():
        return render_template('login.html')

    @app.route('/register-page')
    def register_page():
        return render_template('register.html')

    @app.route('/dashboard')
    def dashboard_page():
        return render_template('dashboard.html')

    @app.route('/admin/dashboard')
    def admin_dashboard_page():
        try:
            record_admin_action('view_admin_dashboard', 'admin_page')
        except Exception:
            pass
        return render_template('admin_dashboard.html')

    @app.route('/api/admin/stats', methods=['GET'])
    @require_admin
    def get_admin_stats():
        """Get system statistics for admin dashboard"""
        if not db_available or session_local is None:
            return jsonify({'error': 'database not available'}), 503
            
        session = session_local()
        try:
            user_count = session.query(user_model).count()
            # Count only active/open items to match admin UI labels
            try:
                job_count = session.query(job_model).filter_by(status='open').count()
            except Exception:
                job_count = session.query(job_model).count()
            try:
                listing_count = session.query(listing_model).filter_by(status='active').count()
            except Exception:
                listing_count = session.query(listing_model).count()
            pending_verifications = session.query(verification_doc_model).filter_by(status='pending').count()
            unverified_users = session.query(user_model).filter_by(verified=False).count()
            
            # Calculate total platform revenue (fees)
            # Sum all transactions with type 'fee'
            total_fees = session.query(transaction_model).filter_by(transaction_type='fee').with_entities(func.sum(transaction_model.amount)).scalar() or 0.0

            # Compute withdrawal-specific fees (description contains 'withdraw' or 'withdrawal')
            try:
                from sqlalchemy import or_
                withdrawal_fees_q = session.query(transaction_model).filter(
                    transaction_model.transaction_type == 'fee',
                    or_(transaction_model.description.ilike('%withdraw%'), transaction_model.description.ilike('%withdrawal%'))
                ).with_entities(func.sum(transaction_model.amount)).scalar() or 0.0
            except Exception:
                # Fallback to total_fees if description filtering not supported
                withdrawal_fees_q = 0.0

            withdrawal_fees = float(withdrawal_fees_q)
            
            # Record admin access to stats if admin_id present
            try:
                record_admin_action('view_admin_stats', 'admin_stats')
            except Exception:
                pass

            # Return stats
            return jsonify({
                'users': user_count,
                'unverified_users': unverified_users,
                'jobs': job_count,
                'listings': listing_count,
                'pending_verifications': pending_verifications,
                'total_revenue': float(total_fees),
                'withdrawal_fees': withdrawal_fees
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/legal/privacy')
    def privacy_page():
        return render_template('privacy.html')

    @app.route('/legal/tos')
    def terms_page():
        return render_template('terms.html')

    @app.route('/marketplace')
    def marketplace_page():
        return render_template('marketplace.html')

    @app.route('/workers-directory')
    def workers_page():
        return render_template('workers.html')

    @app.route('/forum')
    def forum_page():
        return render_template('forum.html')

    @app.route('/admin/users-page')
    def admin_users_page():
        try:
            record_admin_action('view_users_page', 'admin_page')
        except Exception:
            pass
        return render_template('admin_users.html')

    @app.route('/admin/verifications')
    def admin_verifications_page():
        try:
            record_admin_action('view_verifications_page', 'admin_page')
        except Exception:
            pass
        return render_template('admin_verifications.html')

    @app.route('/admin/audit-logs', methods=['GET'])
    def admin_audit_logs_page():
        """Render the admin audit logs page (UI). The API for fetching logs is a POST at the same path."""
        try:
            record_admin_action('view_audit_logs_page', 'admin_page')
        except Exception:
            pass
        return render_template('admin_audit_logs.html')

    @app.route('/admin/health')
    def admin_health_page():
        try:
            record_admin_action('view_health_page', 'admin_page')
        except Exception:
            pass
        return render_template('admin_health.html')

    @app.route('/admin/moderation-page')
    def admin_moderation_page():
        try:
            record_admin_action('view_moderation_page', 'admin_page')
        except Exception:
            pass
        return render_template('admin_moderation.html')

    @app.route('/admin/settings')
    def admin_settings_page():
        try:
            record_admin_action('view_settings', 'admin_page')
        except Exception:
            pass
        return render_template('admin_settings.html')

    @app.route('/marketplace/create')
    def marketplace_create_page():
        return render_template('marketplace_create.html')

    @app.route('/marketplace/<int:id>')
    def marketplace_detail_page(id):
        return render_template('marketplace_detail.html')

    @app.route('/marketplace/<int:id>/edit')
    def marketplace_edit_page(id):
        return render_template('marketplace_edit.html')

    @app.route('/settings')
    def profile_settings_page():
        return render_template('profile_settings.html')

    @app.route('/workers/<int:id>')
    def worker_detail_page(id):
        return render_template('worker_detail.html')

    @app.route('/jobs/history')
    def job_history_page():
        return render_template('job_history.html')

    @app.route('/reviews')
    def reviews_page():
        return render_template('reviews.html')

    @app.route('/profile/<int:id>')
    def public_profile_page(id):
        return render_template('public_profile.html')

    @app.route('/messages')
    def messages_page():
        return render_template('messages.html')

    @app.route('/contracts')
    def contracts_page():
        return render_template('contracts.html')

    @app.route('/wallet')
    def wallet_page():
        return render_template('wallet.html')

    @app.route('/tools/produce-assistant')
    def produce_assistant_page():
        return render_template('produce_assistant.html')

    @app.route('/static/openapi.yaml')
    def serve_openapi_spec():
        return send_from_directory(config.BASE_DIR, 'openapi.yaml')
    
    # ---------------- Job application endpoints ----------------
    @app.route('/api/jobs/<int:job_id>/apply', methods=['POST'])
    def apply_to_job(job_id):
        if not db_available or session_local is None or job_model is None or job_application_model is None or user_model is None:
            return jsonify({'error': 'database not available'}), 503

        data = request.get_json() or {}
        user_id = data.get('user_id')
        cover_letter = data.get('cover_letter')

        if not user_id:
            return jsonify({'error': 'user_id required'}), 400

        session = session_local()
        try:
            job = session.query(job_model).filter_by(id=job_id).first()
            if not job:
                return jsonify({'error': 'Job not found'}), 404

            # Prevent employer from applying to own job
            if job.employer_id == int(user_id):
                return jsonify({'error': 'Employer cannot apply to own job'}), 400

            existing = session.query(job_application_model).filter_by(job_id=job_id, applicant_id=user_id).first()
            if existing:
                return jsonify({'message': 'Already applied', 'application': existing.to_dict()}), 200

            application = job_application_model(job_id=job_id, applicant_id=user_id, cover_letter=cover_letter)
            session.add(application)
            session.commit()
            session.refresh(application)

            return jsonify({'message': 'Application submitted', 'application': application.to_dict()}), 201
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/jobs/<int:job_id>/applications', methods=['GET'])
    def list_job_applications(job_id):
        """List applications for a job. Requires employer_id query param to verify access."""
        if not db_available or session_local is None or job_model is None or job_application_model is None:
            return jsonify({'error': 'database not available'}), 503

        employer_id = request.args.get('employer_id')
        if not employer_id:
            return jsonify({'error': 'employer_id required'}), 400

        session = session_local()
        try:
            job = session.query(job_model).filter_by(id=job_id).first()
            if not job:
                return jsonify({'error': 'Job not found'}), 404

            if int(employer_id) != job.employer_id:
                return jsonify({'error': 'Access denied'}), 403

            applications = session.query(job_application_model).filter_by(job_id=job_id).all()
            return jsonify([a.to_dict() for a in applications])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/jobs/<int:job_id>/my-application', methods=['GET'])
    def get_my_application(job_id):
        """Get the calling user's application for the job. Pass user_id query param."""
        if not db_available or session_local is None or job_application_model is None:
            return jsonify({'error': 'database not available'}), 503

        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400

        session = session_local()
        try:
            appn = session.query(job_application_model).filter_by(job_id=job_id, applicant_id=user_id).first()
            if not appn:
                return jsonify({'application': None}), 200
            return jsonify({'application': appn.to_dict()}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/job-applications/<int:application_id>/accept', methods=['POST'])
    def accept_application(application_id):
        """Accept an application. Requires employer_id in JSON body."""
        if not db_available or session_local is None or job_application_model is None or job_model is None:
            return jsonify({'error': 'database not available'}), 503

        data = request.get_json() or {}
        employer_id = data.get('employer_id')
        if not employer_id:
            return jsonify({'error': 'employer_id required'}), 400

        session = session_local()
        try:
            appn = session.query(job_application_model).filter_by(id=application_id).first()
            if not appn:
                return jsonify({'error': 'Application not found'}), 404

            job = session.query(job_model).filter_by(id=appn.job_id).first()
            if not job or job.employer_id != int(employer_id):
                return jsonify({'error': 'Access denied'}), 403

            appn.status = 'accepted'
            session.commit()
            return jsonify({'message': 'Application accepted', 'application': appn.to_dict()}), 200
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/job-applications/<int:application_id>/decline', methods=['POST'])
    def decline_application(application_id):
        """Decline an application. Requires employer_id in JSON body."""
        if not db_available or session_local is None or job_application_model is None or job_model is None:
            return jsonify({'error': 'database not available'}), 503

        data = request.get_json() or {}
        employer_id = data.get('employer_id')
        if not employer_id:
            return jsonify({'error': 'employer_id required'}), 400

        session = session_local()
        try:
            appn = session.query(job_application_model).filter_by(id=application_id).first()
            if not appn:
                return jsonify({'error': 'Application not found'}), 404

            job = session.query(job_model).filter_by(id=appn.job_id).first()
            if not job or job.employer_id != int(employer_id):
                return jsonify({'error': 'Access denied'}), 403

            appn.status = 'rejected'
            session.commit()
            return jsonify({'message': 'Application declined', 'application': appn.to_dict()}), 200
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/job-applications/<int:application_id>/message', methods=['POST'])
    def message_applicant(application_id):
        """Send a message from the job poster to the applicant (or vice-versa).
           JSON body: sender_id, content
        """
        if not db_available or session_local is None or job_application_model is None or message_model is None or user_model is None:
            return jsonify({'error': 'database not available'}), 503

        data = request.get_json() or {}
        sender_id = data.get('sender_id')
        content = data.get('content')
        if not sender_id or not content:
            return jsonify({'error': 'sender_id and content required'}), 400

        session = session_local()
        try:
            appn = session.query(job_application_model).filter_by(id=application_id).first()
            if not appn:
                return jsonify({'error': 'Application not found'}), 404

            # Determine recipient: if sender is applicant -> recipient is employer, else recipient is applicant
            if int(sender_id) == int(appn.applicant_id):
                recipient_id = session.query(job_model).filter_by(id=appn.job_id).first().employer_id
            else:
                recipient_id = appn.applicant_id

            # Create message
            message = message_model(sender_id=sender_id, recipient_id=recipient_id, content=content)
            session.add(message)
            session.commit()
            session.refresh(message)
            return jsonify({'message': 'Message sent', 'data': message.to_dict()}), 201
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    def validate_password(password):
        """Validate password complexity"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r"[0-9]", password):
            return False, "Password must contain at least one number"
        return True, ""

    def send_mock_email(to_email, subject, body):
        """Mock email sender that prints to terminal"""
        print("\n" + "="*50)
        print(f"MOCK EMAIL TO: {to_email}")
        print(f"SUBJECT: {subject}")
        print(f"BODY:\n{body}")
        print("="*50 + "\n")
        return True
    
    # ========== Routes ==========

    # Old index route removed in favor of frontend template
    # @app.route('/')
    # def index(): ...

    @app.route('/health')
    def health():
        # Extended health check: DB connectivity & query latency, storage usage, optional psutil metrics
        start = time.time()
        result = {'status': 'ok', 'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()}

        # Database check
        db_info = {'status': 'unavailable', 'query_time_ms': None, 'user_count': None}
        if db_available and session_local is not None and user_model is not None:
            session = None
            try:
                t0 = time.time()
                session = session_local()
                # simple query to test DB responsiveness
                user_count = session.query(user_model).count()
                t1 = time.time()
                db_info['status'] = 'online'
                db_info['query_time_ms'] = int((t1 - t0) * 1000)
                db_info['user_count'] = int(user_count)
            except Exception as e:
                db_info['status'] = 'error'
                db_info['error'] = str(e)
            finally:
                try:
                    if session:
                        session.close()
                except Exception:
                    pass
        result['db'] = db_info

        # Storage usage
        try:
            du = shutil.disk_usage(config.BASE_DIR)
            total = du.total
            used = du.used
            free = du.free
            percent = int((used / total) * 100) if total else 0
            result['storage'] = {
                'total_bytes': total,
                'used_bytes': used,
                'free_bytes': free,
                'used_percent': percent
            }
        except Exception as e:
            result['storage'] = {'error': str(e)}

        # Optional system metrics via psutil if available
        try:
            try:
                import psutil
            except Exception:
                psutil = None
            if psutil:
                proc = psutil.Process()
                mem = psutil.virtual_memory()
                cpu = psutil.cpu_percent(interval=0.1)
                result['system'] = {
                    'cpu_percent': cpu,
                    'memory_total': mem.total,
                    'memory_used': mem.used,
                    'memory_percent': mem.percent,
                    'process_rss': proc.memory_info().rss
                }
        except Exception:
            # psutil not available or failed, skip
            pass

        # Uptime and response time
        try:
            result['uptime_seconds'] = int(time.time() - getattr(app, 'start_time', time.time()))
        except Exception:
            result['uptime_seconds'] = None

        result['api_response_time_ms'] = int((time.time() - start) * 1000)

        # Load thresholds (if any) and generate alerts
        try:
            DATA_DIR = os.path.join(config.BASE_DIR, 'data')
            os.makedirs(DATA_DIR, exist_ok=True)
            thresholds_path = os.path.join(DATA_DIR, 'health_thresholds.json')
            if os.path.exists(thresholds_path):
                with open(thresholds_path, 'r', encoding='utf-8') as f:
                    thresholds = json.load(f)
            else:
                thresholds = {}
        except Exception:
            thresholds = {}

        alerts = []
        # api response time threshold
        api_thr = thresholds.get('api_response_time_ms')
        if api_thr is not None and result.get('api_response_time_ms') is not None and result['api_response_time_ms'] > api_thr:
            alerts.append({'metric': 'api_response_time_ms', 'value': result['api_response_time_ms'], 'threshold': api_thr, 'level': 'warning'})

        # storage threshold
        storage_thr = thresholds.get('storage_used_percent')
        if storage_thr is not None and result.get('storage') and result['storage'].get('used_percent') is not None and result['storage']['used_percent'] > storage_thr:
            alerts.append({'metric': 'storage_used_percent', 'value': result['storage']['used_percent'], 'threshold': storage_thr, 'level': 'critical'})

        # db query time
        db_thr = thresholds.get('db_query_time_ms')
        if db_thr is not None and result.get('db') and result['db'].get('query_time_ms') is not None and result['db']['query_time_ms'] > db_thr:
            alerts.append({'metric': 'db_query_time_ms', 'value': result['db']['query_time_ms'], 'threshold': db_thr, 'level': 'warning'})

        # cpu threshold (if available)
        cpu_thr = thresholds.get('cpu_percent')
        if cpu_thr is not None and result.get('system') and result['system'].get('cpu_percent') is not None and result['system']['cpu_percent'] > cpu_thr:
            alerts.append({'metric': 'cpu_percent', 'value': result['system']['cpu_percent'], 'threshold': cpu_thr, 'level': 'warning'})

        result['alerts'] = alerts

        # Append to history file (keep last 200 entries)
        try:
            history_path = os.path.join(DATA_DIR, 'health_history.json')
            history = []
            if os.path.exists(history_path):
                try:
                    with open(history_path, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                except Exception:
                    history = []
            entry = {
                'timestamp': result.get('timestamp'),
                'api_response_time_ms': result.get('api_response_time_ms'),
                'storage_used_percent': result.get('storage', {}).get('used_percent'),
                'db_query_time_ms': result.get('db', {}).get('query_time_ms') if result.get('db') else None,
                'cpu_percent': result.get('system', {}).get('cpu_percent') if result.get('system') else None
            }
            history.append(entry)
            # keep tail (increase retention so restart doesn't lose recent history)
            history = history[-2000:]
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, default=str)
            result['history_count'] = len(history)
        except Exception:
            pass

        return jsonify(result), 200

    # ----- Health thresholds and history endpoints -----
    @app.route('/api/health/thresholds', methods=['GET'])
    def get_health_thresholds():
        DATA_DIR = os.path.join(config.BASE_DIR, 'data')
        os.makedirs(DATA_DIR, exist_ok=True)
        thresholds_path = os.path.join(DATA_DIR, 'health_thresholds.json')
        if os.path.exists(thresholds_path):
            try:
                with open(thresholds_path, 'r', encoding='utf-8') as f:
                    return jsonify(json.load(f)), 200
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        # default thresholds
        defaults = {
            'api_response_time_ms': 200,
            'storage_used_percent': 80,
            'db_query_time_ms': 200,
            'cpu_percent': 85
        }
        return jsonify(defaults), 200

    @app.route('/api/health/thresholds', methods=['POST'])
    @require_admin
    def set_health_thresholds():
        DATA_DIR = os.path.join(config.BASE_DIR, 'data')
        os.makedirs(DATA_DIR, exist_ok=True)
        thresholds_path = os.path.join(DATA_DIR, 'health_thresholds.json')
        data = request.get_json() or {}
        try:
            with open(thresholds_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            return jsonify({'message': 'thresholds saved'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/health/history', methods=['GET'])
    @require_admin
    def get_health_history():
        DATA_DIR = os.path.join(config.BASE_DIR, 'data')
        history_path = os.path.join(DATA_DIR, 'health_history.json')
        limit = int(request.args.get('limit', 100))
        # optional server-side filtering: minutes (relative window), since (ISO), until (ISO)
        minutes = request.args.get('minutes')
        since_q = request.args.get('since')
        until_q = request.args.get('until')
        if not os.path.exists(history_path):
            return jsonify([]), 200
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)

            # if minutes provided, compute cutoff and filter
            filtered = history
            try:
                # convert stored timestamps to datetimes for comparison
                if minutes is not None:
                    try:
                        m = int(minutes)
                        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=m)
                        newf = []
                        for h in filtered:
                            ts = h.get('timestamp') or h.get('time') or h.get('checked_at') or h.get('t')
                            if not ts:
                                continue
                            try:
                                t = datetime.datetime.fromisoformat(ts)
                                # ensure tz-aware
                                if t.tzinfo is None:
                                    t = t.replace(tzinfo=datetime.timezone.utc)
                                if t >= cutoff:
                                    newf.append(h)
                            except Exception:
                                continue
                        filtered = newf
                    except Exception:
                        pass
                # since/until override
                if since_q:
                    try:
                        since_dt = datetime.datetime.fromisoformat(since_q)
                        if since_dt.tzinfo is None:
                            since_dt = since_dt.replace(tzinfo=datetime.timezone.utc)
                        newf = []
                        for h in filtered:
                            ts = h.get('timestamp') or h.get('time') or h.get('checked_at') or h.get('t')
                            if not ts:
                                continue
                            try:
                                t = datetime.datetime.fromisoformat(ts)
                                if t.tzinfo is None:
                                    t = t.replace(tzinfo=datetime.timezone.utc)
                                if t >= since_dt:
                                    newf.append(h)
                            except Exception:
                                continue
                        filtered = newf
                    except Exception:
                        pass
                if until_q:
                    try:
                        until_dt = datetime.datetime.fromisoformat(until_q)
                        if until_dt.tzinfo is None:
                            until_dt = until_dt.replace(tzinfo=datetime.timezone.utc)
                        newf = []
                        for h in filtered:
                            ts = h.get('timestamp') or h.get('time') or h.get('checked_at') or h.get('t')
                            if not ts:
                                continue
                            try:
                                t = datetime.datetime.fromisoformat(ts)
                                if t.tzinfo is None:
                                    t = t.replace(tzinfo=datetime.timezone.utc)
                                if t <= until_dt:
                                    newf.append(h)
                            except Exception:
                                continue
                        filtered = newf
                    except Exception:
                        pass
            except Exception:
                # if any filtering step fails, fall back to full history
                filtered = history

            # support CSV export
            fmt = request.args.get('format')
            tail = filtered[-limit:]
            if fmt and fmt.lower() == 'csv':
                try:
                    output = io.StringIO()
                    writer = csv.writer(output)
                    # header
                    writer.writerow(['timestamp','api_response_time_ms','storage_used_percent','db_query_time_ms','cpu_percent'])
                    for h in tail:
                        writer.writerow([
                            h.get('timestamp') or h.get('time') or h.get('checked_at') or '',
                            h.get('api_response_time_ms',''),
                            h.get('storage_used_percent',''),
                            h.get('db_query_time_ms',''),
                            h.get('cpu_percent','')
                        ])
                    csv_data = output.getvalue()
                    output.close()
                    headers = {
                        'Content-Disposition': 'attachment; filename="health_history.csv"'
                    }
                    return Response(csv_data, mimetype='text/csv', headers=headers)
                except Exception as e:
                    return jsonify({'error': 'failed to generate csv', 'detail': str(e)}), 500

            # return the tail up to limit (json)
            return jsonify(tail), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/health/alert-test', methods=['POST'])
    @require_admin
    def health_alert_test():
        data = request.get_json() or {}
        to_email = data.get('email')
        if not to_email:
            return jsonify({'error': 'email required'}), 400
        # synthesize a sample alert
        subject = 'Test: System Health Alert'
        body = 'This is a test alert from FLB Extended system health.\n\n'
        try:
            # include current health snapshot
            res = requests.get(request.url_root.rstrip('/') + '/health')
            body += 'Current health snapshot:\n' + (res.text if res.ok else 'unable to fetch')
        except Exception as e:
            body += 'error fetching health: ' + str(e)

        send_mock_email(to_email, subject, body)
        return jsonify({'message': 'test alert sent (mock)'}), 200

    @app.route('/users')
    def list_users():
        # If DB is available, return real users; otherwise return an empty list.
        if db_available and session_local is not None and user_model is not None:
            session = session_local()
            users = session.query(user_model).all()
            session.close()
            return jsonify([u.to_dict() for u in users])
        return jsonify([])

    @app.route('/register', methods=['POST'])
    def register():
        if not db_available or session_local is None or user_model is None:
            return jsonify({'error': 'database not available'}), 503

        data = None
        try:
            data = request.get_json()
        except Exception:
            data = None

        if not data:
            return jsonify({'error': 'invalid json'}), 400

        required = ('full_name', 'email', 'password', 'account_type')
        if not all(k in data for k in required):
            return jsonify({'error': 'missing fields'}), 400

        # Validate account_type
        # Note: moderator, admin, super_admin can only be created by super_admin via special endpoints
        VALID_ROLES = {'farmer', 'realtor', 'worker'}
        if data['account_type'] not in VALID_ROLES:
            return jsonify({
                'error': f'Invalid account_type. Must be one of: {sorted(VALID_ROLES)}'
            }), 400

        # Validate password
        is_valid, msg = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': msg}), 400

        session = session_local()
        existing = session.query(user_model).filter_by(email=data['email']).first()
        if existing:
            session.close()
            return jsonify({'error': 'email already registered'}), 409

        user = user_model(full_name=data['full_name'], email=data['email'], account_type=data['account_type'])
        user.set_password(data['password'])
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # If account_type is worker, create WorkerProfile
        if data['account_type'] == 'worker' and worker_profile_model is not None:
            worker_profile = worker_profile_model(
                user_id=user.id,
                specialization='general',  # Default, can be updated later
                bio='',
                available=True,
                location_state='',
                location_area=''
            )
            session.add(worker_profile)
            session.commit()
            session.refresh(user)  # Refresh user after adding worker profile
        
        # Get user dict before closing session
        user_dict = user.to_dict()
        session.close()
        return jsonify(user_dict), 201

    @app.route('/login', methods=['POST'])
    @limiter.limit("5 per minute")
    def login():
        if not db_available or session_local is None or user_model is None:
            return jsonify({'error': 'database not available'}), 503

        try:
            data = request.get_json()
        except Exception:
            data = None

        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'invalid credentials'}), 400

        session = session_local()
        user = session.query(user_model).filter_by(email=data['email']).first()
        session.close()
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'invalid email or password'}), 401

        if user.is_banned:
            reason = user.ban_reason if user.ban_reason else "No reason provided"
            return jsonify({'error': f'account is banned\nReason: {reason}'}), 403

        return jsonify(user.to_dict()), 200

    @app.route('/logout')
    def logout():
        """Clear server-side session (if any) and redirect to login page"""
        try:
            from flask import session as flask_session
            flask_session.pop('user_id', None)
        except Exception:
            pass
        return redirect(url_for('login_page'))

    @app.route('/documents/upload', methods=['POST'])
    def upload_document():
        """Upload verification document (NIN, passport, or driver's license)"""
        if not db_available or session_local is None or user_model is None or verification_doc_model is None:
            return jsonify({'error': 'database not available'}), 503

        data = None
        
        # Handle Multipart/Form-Data (File Upload)
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            
            if 'document' in request.files:
                file = request.files['document']
                if file and file.filename:
                    from werkzeug.utils import secure_filename
                    filename = secure_filename(f"{int(time.time())}_{file.filename}")
                    
                    # Ensure directory exists
                    upload_dir = os.path.join('static', 'uploads', 'verifications')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    file_path = os.path.join(upload_dir, filename)
                    file.save(file_path)
                    
                    # Store relative path for DB
                    data['document_path'] = f'/static/uploads/verifications/{filename}'
        
        # Handle JSON
        elif request.is_json:
            try:
                data = request.get_json()
            except Exception:
                data = None

        if not data:
            return jsonify({'error': 'invalid request data'}), 400

        required = ('user_id', 'document_type', 'document_number')
        if not all(k in data for k in required):
            return jsonify({'error': 'missing required fields: user_id, document_type, document_number'}), 400

        # Validate document_type
        VALID_DOC_TYPES = {'NIN', 'passport', 'drivers_license', 'voters_card'}
        if data['document_type'] not in VALID_DOC_TYPES:
            return jsonify({
                'error': f'Invalid document_type. Must be one of: {sorted(VALID_DOC_TYPES)}'
            }), 400

        session = session_local()
        
        # Verify user exists
        user = session.query(user_model).filter_by(id=data['user_id']).first()
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404

        if user.is_banned:
            reason = user.ban_reason if user.ban_reason else "No reason provided"
            session.close()
            return jsonify({'error': f'account is banned\nReason: {reason}'}), 403

        # Create verification document
        doc = verification_doc_model(
            user_id=data['user_id'],
            document_type=data['document_type'],
            document_number=data['document_number'],
            document_path=data.get('document_path')  # Optional file path
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        session.close()

        return jsonify(doc.to_dict()), 201

    @app.route('/documents/<int:user_id>', methods=['GET'])
    def get_user_documents(user_id):
        """Get all verification documents for a user"""
        if not db_available or session_local is None or verification_doc_model is None:
            return jsonify({'error': 'database not available'}), 503

        session = session_local()
        
        # Check for admin viewer to log access
        admin_id = request.args.get('admin_id')
        if admin_id:
            admin = session.query(user_model).filter_by(id=admin_id).first()
            if admin and admin.account_type in ['admin', 'super_admin']:
                # Log access
                log_admin_action(
                    admin_id=admin_id,
                    action='view_verification_docs',
                    target_type='user',
                    target_id=user_id,
                    details=f'Viewed verification documents for user {user_id}'
                )

        docs = session.query(verification_doc_model).filter_by(user_id=user_id).all()
        session.close()

        return jsonify([doc.to_dict() for doc in docs]), 200

    @app.route('/documents/verify/<int:doc_id>', methods=['POST'])
    def verify_document(doc_id):
        """Admin endpoint to approve/reject a verification document"""
        if not db_available or session_local is None or verification_doc_model is None or user_model is None:
            return jsonify({'error': 'database not available'}), 503

        try:
            data = request.get_json()
        except Exception:
            data = None

        if not data or 'status' not in data or 'admin_id' not in data:
            return jsonify({'error': 'missing required fields: status, admin_id'}), 400

        # Validate status
        VALID_STATUSES = {'approved', 'rejected'}
        if data['status'] not in VALID_STATUSES:
            return jsonify({
                'error': f'Invalid status. Must be one of: {sorted(VALID_STATUSES)}'
            }), 400

        session = session_local()

        # Verify admin exists and has admin or super_admin role
        admin = session.query(user_model).filter_by(id=data['admin_id']).first()
        if not admin or admin.account_type not in ['admin', 'super_admin']:
            session.close()
            return jsonify({'error': 'unauthorized: admin access required'}), 403

        # Get document with a fresh read and check status to prevent approving non-pending docs
        try:
            # Optional: use with_for_update() for DBs that support row-level locking
            try:
                doc = session.query(verification_doc_model).filter_by(id=doc_id).with_for_update().first()
            except Exception:
                doc = session.query(verification_doc_model).filter_by(id=doc_id).first()

            if not doc:
                session.close()
                return jsonify({'error': 'document not found'}), 404

            # Prevent changing a document that is no longer pending
            current_status = getattr(doc, 'status', None)
            if current_status != 'pending':
                session.close()
                return jsonify({'error': 'document already processed', 'status': current_status}), 409

            # Update document status
            doc.status = data['status']
            doc.admin_notes = data.get('admin_notes')
            doc.reviewed_at = datetime.datetime.now(datetime.timezone.utc)
            doc.reviewed_by = data['admin_id']

            # Log admin action
            try:
                log_admin_action(
                    admin_id=data['admin_id'],
                    action=f'verify_document_{data["status"]}',
                    target_type='verification_document',
                    target_id=doc.id,
                    reason=data.get('admin_notes'),
                    details=f'Document {data["status"]}'
                )
            except Exception:
                pass

            # If approved, mark user as verified
            if data['status'] == 'approved':
                user = session.query(user_model).filter_by(id=doc.user_id).first()
                if user:
                    user.verified = True

            session.commit()
            session.refresh(doc)
            result = doc.to_dict()
            session.close()
            return jsonify(result), 200
        except Exception as e:
            session.rollback()
            session.close()
            return jsonify({'error': str(e)}), 500

    @app.route('/admin/verify-user/<int:user_id>', methods=['POST'])
    @require_admin
    def admin_verify_user(user_id):
        """Admin convenience endpoint: find a pending verification document for the user and approve it."""
        if not db_available or session_local is None or verification_doc_model is None or user_model is None:
            return jsonify({'error': 'database not available'}), 503

        data = request.get_json() or {}
        admin_id = data.get('admin_id') or request.args.get('admin_id')
        if not admin_id:
            return jsonify({'error': 'admin_id required'}), 401

        session = session_local()
        try:
            doc = session.query(verification_doc_model).filter_by(user_id=user_id, status='pending').first()
            if not doc:
                session.close()
                return jsonify({'error': 'No pending verification document for this user'}), 404

            # Approve the document
            doc.status = 'approved'
            doc.admin_notes = data.get('admin_notes')
            doc.reviewed_at = datetime.datetime.now(datetime.timezone.utc)
            doc.reviewed_by = int(admin_id)

            # Mark the user as verified
            user = session.query(user_model).filter_by(id=user_id).first()
            if user:
                user.verified = True

            session.commit()

            # Log admin action
            try:
                log_admin_action(
                    admin_id=admin_id,
                    action='verify_user_admin_approved',
                    target_type='user',
                    target_id=user_id,
                    reason=data.get('admin_notes')
                )
            except Exception:
                pass

            session.refresh(doc)
            result = doc.to_dict()
            session.close()
            return jsonify(result), 200
        except Exception as e:
            session.rollback()
            session.close()
            return jsonify({'error': str(e)}), 500

    # ========== MESSAGING ENDPOINTS ==========
    
    @app.route('/messages/send', methods=['POST'])
    def send_message():
        """Send a message to another user"""
        if not db_available or session_local is None or user_model is None or message_model is None:
            return jsonify({'error': 'database not available'}), 503

        try:
            data = request.get_json()
        except Exception:
            data = None

        if not data:
            return jsonify({'error': 'invalid json'}), 400

        required = ('sender_id', 'recipient_id', 'content')
        if not all(k in data for k in required):
            return jsonify({'error': 'missing required fields: sender_id, recipient_id, content'}), 400

        session = session_local()

        # Verify both users exist
        sender = session.query(user_model).filter_by(id=data['sender_id']).first()
        recipient = session.query(user_model).filter_by(id=data['recipient_id']).first()
        
        if not sender or not recipient:
            session.close()
            return jsonify({'error': 'sender or recipient not found'}), 404

        if sender.is_banned:
            reason = sender.ban_reason if sender.ban_reason else "No reason provided"
            session.close()
            return jsonify({'error': f'account is banned\nReason: {reason}'}), 403

        # Create message
        message = message_model(
            sender_id=data['sender_id'],
            recipient_id=data['recipient_id'],
            subject=data.get('subject'),
            content=data['content']
        )
        session.add(message)
        session.commit()
        session.refresh(message)
        session.close()

        return jsonify(message.to_dict()), 201

    @app.route('/messages/<int:user_id>', methods=['GET'])
    def get_user_messages(user_id):
        """Get all messages for a user (sent and received)"""
        if not db_available or session_local is None or message_model is None:
            return jsonify({'error': 'database not available'}), 503

        session = session_local()
        
        # Get messages where user is sender or recipient
        sent = session.query(message_model).filter_by(sender_id=user_id).all()
        received = session.query(message_model).filter_by(recipient_id=user_id).all()
        session.close()

        return jsonify({
            'sent': [msg.to_dict() for msg in sent],
            'received': [msg.to_dict() for msg in received]
        }), 200

    @app.route('/messages/<int:message_id>/read', methods=['PUT'])
    def mark_message_read(message_id):
        """Mark a message as read"""
        if not db_available or session_local is None or message_model is None:
            return jsonify({'error': 'database not available'}), 503

        session = session_local()
        message = session.query(message_model).filter_by(id=message_id).first()
        
        if not message:
            session.close()
            return jsonify({'error': 'message not found'}), 404

        message.read = True
        message.read_at = datetime.datetime.now(datetime.timezone.utc)
        session.commit()
        session.refresh(message)
        session.close()

        return jsonify(message.to_dict()), 200

    # ========== CONTRACT ENDPOINTS ==========
    
    @app.route('/contracts/create', methods=['POST'])
    def create_contract():
        """Create a new contract between two parties"""
        if not db_available or session_local is None or user_model is None or contract_model is None:
            return jsonify({'error': 'database not available'}), 503

        try:
            data = request.get_json()
        except Exception:
            data = None

        if not data:
            return jsonify({'error': 'invalid json'}), 400

        required = ('title', 'party_a_id', 'party_b_id', 'terms')
        if not all(k in data for k in required):
            return jsonify({'error': 'missing required fields: title, party_a_id, party_b_id, terms'}), 400

        session = session_local()

        # Verify both parties exist
        party_a = session.query(user_model).filter_by(id=data['party_a_id']).first()
        party_b = session.query(user_model).filter_by(id=data['party_b_id']).first()
        
        if not party_a or not party_b:
            session.close()
            return jsonify({'error': 'one or both parties not found'}), 404

        if party_a.is_banned:
            reason = party_a.ban_reason if party_a.ban_reason else "No reason provided"
            session.close()
            return jsonify({'error': f'party_a is banned: {reason}'}), 403

        if party_b.is_banned:
            reason = party_b.ban_reason if party_b.ban_reason else "No reason provided"
            session.close()
            return jsonify({'error': f'party_b is banned: {reason}'}), 403

        # Create contract
        contract = contract_model(
            title=data['title'],
            description=data.get('description'),
            party_a_id=data['party_a_id'],
            party_b_id=data['party_b_id'],
            terms=data['terms'],
            amount=data.get('amount'),
            expires_at=data.get('expires_at')
        )
        session.add(contract)
        session.commit()
        session.refresh(contract)
        session.close()

        return jsonify(contract.to_dict()), 201

    @app.route('/contracts/<int:contract_id>/sign', methods=['POST'])
    def sign_contract(contract_id):
        """Sign a contract (party must be one of the contract parties)"""
        if not db_available or session_local is None or contract_model is None:
            return jsonify({'error': 'database not available'}), 503

        try:
            data = request.get_json()
        except Exception:
            data = None

        if not data or 'user_id' not in data:
            return jsonify({'error': 'missing required field: user_id'}), 400

        session = session_local()
        contract = session.query(contract_model).filter_by(id=contract_id).first()
        
        if not contract:
            session.close()
            return jsonify({'error': 'contract not found'}), 404

        user_id = data['user_id']
        
        # Check if user is banned
        user = session.query(user_model).filter_by(id=user_id).first()
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404
            
        if user.is_banned:
            reason = user.ban_reason if user.ban_reason else "No reason provided"
            session.close()
            return jsonify({'error': f'account is banned\nReason: {reason}'}), 403
        
        # Check if user is one of the parties
        signature = data.get('signature')
        if not signature:
             session.close()
             return jsonify({'error': 'signature required'}), 400

        if user_id == contract.party_a_id:
            contract.party_a_signed = True
            contract.party_a_signed_at = datetime.datetime.now(datetime.timezone.utc)
            contract.party_a_signature = signature
        elif user_id == contract.party_b_id:
            contract.party_b_signed = True
            contract.party_b_signed_at = datetime.datetime.now(datetime.timezone.utc)
            contract.party_b_signature = signature
        else:
            session.close()
            return jsonify({'error': 'user is not a party to this contract'}), 403

        # If both parties signed, update status
        if contract.party_a_signed and contract.party_b_signed:
            contract.status = 'signed'

        session.commit()
        session.refresh(contract)
        session.close()

        return jsonify(contract.to_dict()), 200

    @app.route('/contracts/<int:user_id>', methods=['GET'])
    def get_user_contracts(user_id):
        """Get all contracts for a user (as party_a or party_b)"""
        if not db_available or session_local is None or contract_model is None:
            return jsonify({'error': 'database not available'}), 503

        session = session_local()
        
        # Get contracts where user is party_a or party_b
        from sqlalchemy import or_
        contracts = session.query(contract_model).filter(
            or_(contract_model.party_a_id == user_id, contract_model.party_b_id == user_id)
        ).all()
        session.close()

        return jsonify([contract.to_dict() for contract in contracts]), 200

    # ========== MARKETPLACE/LISTING ENDPOINTS ==========
    
    @app.route('/listings/create', methods=['POST'])
    def create_listing():
        """Create a new marketplace listing"""
        if not db_available or session_local is None or user_model is None or listing_model is None:
            return jsonify({'error': 'database not available'}), 503

        # Check if it's a multipart/form-data request (file upload) or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
        else:
            try:
                data = request.get_json()
            except Exception:
                data = None

        if not data:
            return jsonify({'error': 'invalid data'}), 400

        required = ('owner_id', 'listing_type', 'title', 'price', 'category')
        if not all(k in data for k in required):
            return jsonify({'error': 'missing required fields: owner_id, listing_type, title, price, category'}), 400

        # Validate listing_type
        VALID_LISTING_TYPES = {'land_sale', 'land_rent', 'produce', 'equipment', 'services'}
        if data['listing_type'] not in VALID_LISTING_TYPES and data['category'] not in VALID_LISTING_TYPES:
             pass

        session = session_local()

        # Verify owner exists
        owner = session.query(user_model).filter_by(id=data['owner_id']).first()
        if not owner:
            session.close()
            return jsonify({'error': 'owner not found'}), 404
            
        if owner.is_banned:
            reason = owner.ban_reason if owner.ban_reason else "No reason provided"
            session.close()
            return jsonify({'error': f'user is banned: {reason}'}), 403

        # Handle file uploads
        import json
        import csv
        import io
        import os
        from werkzeug.utils import secure_filename
        
        images_list = []
        videos_list = []
        
        # Base upload directory
        UPLOAD_FOLDER = os.path.join('static', 'uploads', 'listings')
        IMAGES_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
        VIDEOS_FOLDER = os.path.join(UPLOAD_FOLDER, 'videos')
        
        os.makedirs(IMAGES_FOLDER, exist_ok=True)
        os.makedirs(VIDEOS_FOLDER, exist_ok=True)

        # Handle images
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    file_path = os.path.join(IMAGES_FOLDER, unique_filename)
                    file.save(file_path)
                    # Store relative path for URL access
                    images_list.append(f"/static/uploads/listings/images/{unique_filename}")
        elif 'images' in data and isinstance(data['images'], list):
             # Handle JSON payload images (if any legacy support needed)
             images_list = data['images']

        # Handle videos
        if 'videos' in request.files:
            files = request.files.getlist('videos')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    file_path = os.path.join(VIDEOS_FOLDER, unique_filename)
                    file.save(file_path)
                    # Store relative path for URL access
                    videos_list.append(f"/static/uploads/listings/videos/{unique_filename}")

        listing = listing_model(
            owner_id=data['owner_id'],
            listing_type=data.get('listing_type', data.get('category')), # Fallback
            title=data['title'],
            description=data.get('description', ''),
            location_state=data.get('location_state'),
            location_area=data.get('location_area'),
            location_address=data.get('location_address'),
            size_value=data.get('size_value'),
            size_unit=data.get('size_unit'),
            price=data['price'],
            price_type=data.get('price_type', 'fixed'),
            images=json.dumps(images_list),
            videos=json.dumps(videos_list),
            status='active'
        )

        session.add(listing)
        session.commit()
        session.refresh(listing)
        session.close()

        return jsonify(listing.to_dict()), 201

    @app.route('/listings/<int:listing_id>/update', methods=['POST', 'PUT'])
    def update_listing(listing_id):
        """Update an existing marketplace listing"""
        if not db_available or session_local is None or user_model is None or listing_model is None:
            return jsonify({'error': 'database not available'}), 503

        # Check if it's a multipart/form-data request (file upload) or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
        else:
            try:
                data = request.get_json()
            except Exception:
                data = None

        if not data:
            return jsonify({'error': 'invalid data'}), 400

        session = session_local()

        # Get the listing
        listing = session.query(listing_model).filter_by(id=listing_id).first()
        if not listing:
            session.close()
            return jsonify({'error': 'listing not found'}), 404

        # Verify ownership (optional - add user_id check if needed)
        owner_id = data.get('owner_id')
        if owner_id and int(owner_id) != listing.owner_id:
            session.close()
            return jsonify({'error': 'not authorized to update this listing'}), 403

        # Update basic fields
        if 'title' in data:
            listing.title = data['title']
        if 'price' in data:
            listing.price = data['price']
        if 'description' in data:
            listing.description = data['description']
        if 'location_state' in data:
            listing.location_state = data['location_state']
        if 'location_area' in data:
            listing.location_area = data['location_area']
        if 'listing_type' in data:
            listing.listing_type = data['listing_type']

        # Handle file uploads for images and videos
        import json
        import os
        from werkzeug.utils import secure_filename

        # Base upload directory
        UPLOAD_FOLDER = os.path.join('static', 'uploads', 'listings')
        IMAGES_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
        VIDEOS_FOLDER = os.path.join(UPLOAD_FOLDER, 'videos')

        os.makedirs(IMAGES_FOLDER, exist_ok=True)
        os.makedirs(VIDEOS_FOLDER, exist_ok=True)

        # Handle image removal (if specified)
        if 'remove_images' in data:
            # Parse existing images
            existing_images = []
            if listing.images:
                try:
                    existing_images = json.loads(listing.images)
                except:
                    existing_images = []
            
            # Remove specified images
            remove_list = data['remove_images'].split(',') if isinstance(data['remove_images'], str) else data['remove_images']
            existing_images = [img for img in existing_images if img not in remove_list]
            listing.images = json.dumps(existing_images)

        # Handle new images (if provided)
        if 'images' in request.files:
            # Parse existing images
            existing_images = []
            if listing.images:
                try:
                    existing_images = json.loads(listing.images)
                except:
                    existing_images = []

            # Add new images
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    file_path = os.path.join(IMAGES_FOLDER, unique_filename)
                    file.save(file_path)
                    existing_images.append(f"/static/uploads/listings/images/{unique_filename}")

            listing.images = json.dumps(existing_images)

        # Handle video removal (if specified)
        if 'remove_videos' in data:
            # Parse existing videos
            existing_videos = []
            if listing.videos:
                try:
                    existing_videos = json.loads(listing.videos)
                except:
                    existing_videos = []
            
            # Remove specified videos
            remove_list = data['remove_videos'].split(',') if isinstance(data['remove_videos'], str) else data['remove_videos']
            existing_videos = [vid for vid in existing_videos if vid not in remove_list]
            listing.videos = json.dumps(existing_videos)

        # Handle new videos (if provided)
        if 'videos' in request.files:
            # Parse existing videos
            existing_videos = []
            if listing.videos:
                try:
                    existing_videos = json.loads(listing.videos)
                except:
                    existing_videos = []

            # Add new videos
            files = request.files.getlist('videos')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    file_path = os.path.join(VIDEOS_FOLDER, unique_filename)
                    file.save(file_path)
                    existing_videos.append(f"/static/uploads/listings/videos/{unique_filename}")

            listing.videos = json.dumps(existing_videos)

        session.commit()
        session.refresh(listing)
        session.close()

        return jsonify(listing.to_dict()), 200


    @app.route('/listings', methods=['GET'])
    def get_listings():
        """Get all marketplace listings with filtering"""
        if not db_available or session_local is None or listing_model is None:
            return jsonify({'error': 'database not available'}), 503

        session = session_local()
        query = session.query(listing_model)

        # Apply filters from query parameters
        listing_type = request.args.get('listing_type')
        if listing_type:
            query = query.filter_by(listing_type=listing_type)

        status = request.args.get('status')
        if status:
            query = query.filter_by(status=status)
        else:
            # Default to active listings only
            query = query.filter_by(status='active')

        location_state = request.args.get('location_state')
        if location_state:
            query = query.filter_by(location_state=location_state)

        # Price range filters
        min_price = request.args.get('min_price')
        if min_price:
            try:
                query = query.filter(listing_model.price >= int(min_price))
            except ValueError:
                pass

        max_price = request.args.get('max_price')
        if max_price:
            try:
                query = query.filter(listing_model.price <= int(max_price))
            except ValueError:
                pass

        # Featured listings first
        featured = request.args.get('featured')
        if featured and featured.lower() == 'true':
            query = query.filter_by(featured=True)
            
        # Search
        search_query = request.args.get('q')
        if search_query:
            from sqlalchemy import or_
            search_term = f"%{search_query}%"
            query = query.filter(or_(
                listing_model.title.ilike(search_term),
                listing_model.description.ilike(search_term),
                listing_model.location_state.ilike(search_term),
                listing_model.location_area.ilike(search_term)
            ))

        # Sorting
        sort_by = request.args.get('sort_by', 'recent')
        if sort_by == 'price_low':
            query = query.order_by(listing_model.price.asc())
        elif sort_by == 'price_high':
            query = query.order_by(listing_model.price.desc())
        elif sort_by == 'oldest':
            query = query.order_by(listing_model.created_at.asc())
        else: # recent
            query = query.order_by(listing_model.created_at.desc())

        listings = query.all()
        session.close()

        return jsonify([listing.to_dict() for listing in listings]), 200

    @app.route('/listings/<int:listing_id>', methods=['GET'])
    def get_listing(listing_id):
        """Get a specific listing by ID"""
        if not db_available or session_local is None or listing_model is None:
            return jsonify({'error': 'database not available'}), 503

        session = session_local()
        listing = session.query(listing_model).filter_by(id=listing_id).first()

        if not listing:
            session.close()
            return jsonify({'error': 'listing not found'}), 404

        # Increment view count
        listing.views += 1
        session.commit()
        session.refresh(listing)
        session.close()

        return jsonify(listing.to_dict()), 200


    @app.route('/listings/<int:listing_id>', methods=['DELETE'])
    def delete_listing(listing_id):
        """Delete a listing (owner only)"""
        if not db_available or session_local is None or listing_model is None:
            return jsonify({'error': 'database not available'}), 503

        try:
            data = request.get_json()
        except Exception:
            data = None

        if not data or 'user_id' not in data:
            return jsonify({'error': 'missing required field: user_id'}), 400

        session = session_local()
        listing = session.query(listing_model).filter_by(id=listing_id).first()

        if not listing:
            session.close()
            return jsonify({'error': 'listing not found'}), 404

        # Verify ownership
        if listing.owner_id != data['user_id']:
            session.close()
            return jsonify({'error': 'unauthorized: only owner can delete listing'}), 403
            
        # Check if user is banned
        user = session.query(user_model).filter_by(id=data['user_id']).first()
        if user and user.is_banned:
            reason = user.ban_reason if user.ban_reason else "No reason provided"
            session.close()
            return jsonify({'error': f'account is banned\nReason: {reason}'}), 403

        session.delete(listing)
        session.commit()
        session.close()

        return jsonify({'message': 'listing deleted successfully'}), 200

    @app.route('/listings/user/<int:user_id>', methods=['GET'])
    def get_user_listings(user_id):
        """Get all listings for a specific user"""
        if not db_available or session_local is None or listing_model is None:
            return jsonify({'error': 'database not available'}), 503

        session = session_local()
        listings = session.query(listing_model).filter_by(owner_id=user_id).order_by(listing_model.created_at.desc()).all()
        session.close()

        return jsonify([listing.to_dict() for listing in listings]), 200

    # ========== WORKER MARKETPLACE ENDPOINTS ==========
    
    @app.route('/workers/create-profile', methods=['POST'])
    def create_worker_profile():
        """Create a worker profile"""
        if not db_available or session_local is None or user_model is None or worker_profile_model is None:
            return jsonify({'error': 'database not available'}), 503

        try:
            data = request.get_json()
        except Exception:
            data = None

        if not data:
            return jsonify({'error': 'invalid json'}), 400

        required = ('user_id', 'specialization')
        if not all(k in data for k in required):
            return jsonify({'error': 'missing required fields: user_id, specialization'}), 400

        # Validate specialization
        VALID_SPECIALIZATIONS = {'fumigation', 'fertilizer', 'labor', 'specialist', 'planting', 'irrigation', 'harvesting'}
        if data['specialization'] not in VALID_SPECIALIZATIONS:
            return jsonify({
                'error': f'Invalid specialization. Must be one of: {sorted(VALID_SPECIALIZATIONS)}'
            }), 400

        session = session_local()

        # Verify user exists
        user = session.query(user_model).filter_by(id=data['user_id']).first()
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404
            
        # Check if user is banned
        if user.is_banned:
            reason = user.ban_reason if user.ban_reason else "No reason provided"
            session.close()
            return jsonify({'error': f'account is banned\nReason: {reason}'}), 403

        # Check if profile already exists
        existing = session.query(worker_profile_model).filter_by(user_id=data['user_id']).first()
        if existing:
            session.close()
            return jsonify({'error': 'worker profile already exists for this user'}), 409

        # Handle JSON fields
        import json
        skills_json = None
        if 'skills' in data and isinstance(data['skills'], list):
            skills_json = json.dumps(data['skills'])

        certifications_json = None
        if 'certifications' in data and isinstance(data['certifications'], list):
            certifications_json = json.dumps(data['certifications'])

        portfolio_json = None
        if 'portfolio_images' in data and isinstance(data['portfolio_images'], list):
            portfolio_json = json.dumps(data['portfolio_images'])

        # Create worker profile
        profile = worker_profile_model(
            user_id=data['user_id'],
            specialization=data['specialization'],
            bio=data.get('bio'),
            experience_years=data.get('experience_years'),
            skills=skills_json,
            available=data.get('available', True),
            hourly_rate=data.get('hourly_rate'),
            daily_rate=data.get('daily_rate'),
            location_state=data.get('location_state'),
            location_area=data.get('location_area'),
            willing_to_travel=data.get('willing_to_travel', False),
            certifications=certifications_json,
            portfolio_images=portfolio_json
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)
        # Eager load user for to_dict
        _ = profile.user
        session.close()

        return jsonify(profile.to_dict()), 201

    @app.route('/workers', methods=['GET'])
    def get_workers():
        """Get all worker profiles with optional filters"""
        if not db_available or session_local is None or worker_profile_model is None:
            return jsonify({'error': 'database not available'}), 503

        session = session_local()
        query = session.query(worker_profile_model).options(joinedload(worker_profile_model.user))

        # Apply filters from query parameters
        specialization = request.args.get('specialization')
        if specialization:
            query = query.filter_by(specialization=specialization)

        available = request.args.get('available')
        if available and available.lower() == 'true':
            query = query.filter_by(available=True)

        location_state = request.args.get('location_state')
        if location_state:
            query = query.filter_by(location_state=location_state)

        # Rate range filters
        min_rate = request.args.get('min_hourly_rate')
        if min_rate:
            try:
                query = query.filter(worker_profile_model.hourly_rate >= int(min_rate))
            except ValueError:
                pass

        max_rate = request.args.get('max_hourly_rate')
        if max_rate:
            try:
                query = query.filter(worker_profile_model.hourly_rate <= int(max_rate))
            except ValueError:
                pass

        # Minimum experience filter
        min_experience = request.args.get('min_experience')
        if min_experience:
            try:
                query = query.filter(worker_profile_model.experience_years >= int(min_experience))
            except ValueError:
                pass
                
        # Search
        search_query = request.args.get('q')
        if search_query:
            from sqlalchemy import or_
            search_term = f"%{search_query}%"
            # Join with user model to search by name
            query = query.join(worker_profile_model.user).filter(or_(
                worker_profile_model.specialization.ilike(search_term),
                worker_profile_model.bio.ilike(search_term),
                worker_profile_model.location_state.ilike(search_term),
                worker_profile_model.location_area.ilike(search_term),
                user_model.full_name.ilike(search_term)
            ))

        # Sorting
        sort_by = request.args.get('sort_by', 'recommended')
        
        # Always prioritize boosted profiles
        if sort_by == 'rating':
            query = query.order_by(worker_profile_model.is_boosted.desc(), worker_profile_model.rating.desc())
        elif sort_by == 'experience':
            query = query.order_by(worker_profile_model.is_boosted.desc(), worker_profile_model.experience_years.desc())
        elif sort_by == 'rate_low':
            query = query.order_by(worker_profile_model.is_boosted.desc(), worker_profile_model.hourly_rate.asc())
        elif sort_by == 'rate_high':
            query = query.order_by(worker_profile_model.is_boosted.desc(), worker_profile_model.hourly_rate.desc())
        else: # recommended / default
            query = query.order_by(worker_profile_model.is_boosted.desc(), worker_profile_model.rating.desc(), worker_profile_model.total_jobs.desc())

        workers = query.all()
        session.close()

        return jsonify([worker.to_dict() for worker in workers]), 200

    @app.route('/workers/<int:worker_id>', methods=['GET'])
    def get_worker(worker_id):
        """Get a specific worker profile by ID"""
        if not db_available or session_local is None or worker_profile_model is None:
            return jsonify({'error': 'database not available'}), 503

        session = session_local()
        worker = session.query(worker_profile_model).options(joinedload(worker_profile_model.user)).filter_by(id=worker_id).first()

        if not worker:
            session.close()
            return jsonify({'error': 'worker profile not found'}), 404

        # Serialize before closing session to avoid DetachedInstanceError
        data = worker.to_dict()
        session.close()
        return jsonify(data), 200

    @app.route('/workers/<int:worker_id>', methods=['PUT'])
    def update_worker_profile(worker_id):
        """Update a worker profile (owner only)"""
        if not db_available or session_local is None or worker_profile_model is None:
            return jsonify({'error': 'database not available'}), 503

        try:
            data = request.get_json()
        except Exception:
            data = None

        if not data:
            return jsonify({'error': 'invalid json'}), 400

        session = session_local()
        worker = session.query(worker_profile_model).filter_by(id=worker_id).first()

        if not worker:
            session.close()
            return jsonify({'error': 'worker profile not found'}), 404

        # Verify ownership if user_id provided
        if 'user_id' in data:
            if worker.user_id != data['user_id']:
                session.close()
                return jsonify({'error': 'unauthorized: only profile owner can update'}), 403
            
            # Check if user is banned
            user = session.query(user_model).filter_by(id=data['user_id']).first()
            if user and user.is_banned:
                reason = user.ban_reason if user.ban_reason else "No reason provided"
                session.close()
                return jsonify({'error': f'account is banned\nReason: {reason}'}), 403

        # Update fields
        import json
        updatable_fields = {
            'specialization', 'bio', 'experience_years', 'available',
            'hourly_rate', 'daily_rate', 'location_state', 'location_area',
            'willing_to_travel'
        }

        for field in updatable_fields:
            if field in data:
                setattr(worker, field, data[field])

        # Handle JSON fields
        if 'skills' in data and isinstance(data['skills'], list):
            worker.skills = json.dumps(data['skills'])

        if 'certifications' in data and isinstance(data['certifications'], list):
            worker.certifications = json.dumps(data['certifications'])

        if 'portfolio_images' in data and isinstance(data['portfolio_images'], list):
            worker.portfolio_images = json.dumps(data['portfolio_images'])

        worker.updated_at = datetime.datetime.now(datetime.timezone.utc)
        session.commit()
        session.refresh(worker)
        # Eager load user for to_dict
        _ = worker.user
        session.close()

        return jsonify(worker.to_dict()), 200

    @app.route('/workers/user/<int:user_id>', methods=['GET'])
    def get_worker_by_user(user_id):
        """Get worker profile for a specific user"""
        if not db_available or session_local is None or worker_profile_model is None:
            return jsonify({'error': 'database not available'}), 503

        session = session_local()
        try:
            worker = session.query(worker_profile_model).options(joinedload(worker_profile_model.user)).filter_by(user_id=user_id).first()

            if not worker:
                return jsonify({'error': 'worker profile not found for this user'}), 404
            
            # Access relationship while session is open
            _ = worker.user
            result = worker.to_dict()
            return jsonify(result), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()
        return jsonify(worker.to_dict()), 200

    # ================== PRODUCE ASSISTANT ENDPOINTS ==================

    @app.route('/produce-assistant/calculate-cost', methods=['POST'])
    def calculate_produce_cost():
        """Calculate cost and profit for farm produce"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        data = request.get_json()
        if not data:
            return jsonify({'error': 'no input data provided'}), 400

        # Validate required fields
        required_fields = [
            'user_id', 'crop_type', 'season', 'land_size_hectares',
            'expected_yield_kg', 'num_workers'
        ]
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400

        # Validate user exists
        session = session_local()
        user = session.query(user_model).filter_by(id=data['user_id']).first()
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404

        # Validate numeric fields
        try:
            land_size = float(data['land_size_hectares'])
            expected_yield = int(data['expected_yield_kg'])
            num_workers = int(data['num_workers'])
            
            if land_size <= 0:
                raise ValueError("Land size must be greater than zero")
            if expected_yield <= 0:
                raise ValueError("Expected yield must be greater than zero")
            if num_workers < 0:
                raise ValueError("Number of workers cannot be negative")
                
        except (ValueError, TypeError) as e:
            session.close()
            return jsonify({'error': f'invalid numeric value: {str(e)}'}), 400

        # Get cost fields (all optional, default to 0)
        cost_fields = [
            'labor_cost', 'seed_cost', 'fertilizer_cost', 'pesticide_cost',
            'water_cost', 'electricity_cost', 'transport_cost', 'other_expenses'
        ]
        
        costs = {}
        for field in cost_fields:
            try:
                costs[field] = int(data.get(field, 0))
                if costs[field] < 0:
                    raise ValueError(f"{field} cannot be negative")
            except (ValueError, TypeError):
                session.close()
                return jsonify({'error': f'{field} must be a valid integer'}), 400

        # Get profit margin (optional, default to 0)
        try:
            profit_margin = float(data.get('profit_margin_percent', 0))
            if profit_margin < 0:
                raise ValueError("Profit margin cannot be negative")
        except (ValueError, TypeError):
            session.close()
            return jsonify({'error': 'profit_margin_percent must be a valid number'}), 400

        # Import calculator functions
        try:
            from calculator import calculate_produce_cost as calc_cost, get_cost_breakdown, get_profitability_analysis
        except ImportError:
            session.close()
            return jsonify({'error': 'calculator module not available'}), 500

        # Prepare calculation data
        calc_data = {
            'expected_yield_kg': expected_yield,
            'profit_margin_percent': profit_margin,
            **costs
        }

        # Perform calculations
        try:
            calculations = calc_cost(calc_data)
            breakdown = get_cost_breakdown(calc_data)
            analysis = get_profitability_analysis(
                calculations['total_cost'],
                calculations['total_profit'],
                calculations['total_revenue']
            )
        except Exception as e:
            session.close()
            return jsonify({'error': f'calculation failed: {str(e)}'}), 400

        # Create ProduceCalculation record
        calculation_record = produce_calculation_model(
            user_id=data['user_id'],
            crop_type=data['crop_type'],
            season=data['season'],
            land_size_hectares=land_size,
            expected_yield_kg=expected_yield,
            num_workers=num_workers,
            profit_margin_percent=profit_margin,
            **costs,
            **calculations
        )

        session.add(calculation_record)
        session.commit()
        
        result = calculation_record.to_dict()
        result['cost_breakdown'] = breakdown
        result['profitability_analysis'] = analysis
        
        session.close()
        return jsonify(result), 201

    @app.route('/produce-assistant/calculations/<int:user_id>', methods=['GET'])
    def get_user_calculations(user_id):
        """Get all cost calculations for a user"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        session = session_local()
        
        # Verify user exists
        user = session.query(user_model).filter_by(id=user_id).first()
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404

        # Get all calculations
        calculations = session.query(produce_calculation_model).filter_by(
            user_id=user_id
        ).order_by(produce_calculation_model.created_at.desc()).all()

        result = [calc.to_dict() for calc in calculations]
        session.close()
        return jsonify(result), 200

    @app.route('/produce-assistant/calculation/<int:calc_id>', methods=['GET'])
    def get_calculation_detail(calc_id):
        """Get detailed information for a specific calculation"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        session = session_local()
        
        calculation = session.query(produce_calculation_model).filter_by(id=calc_id).first()
        if not calculation:
            session.close()
            return jsonify({'error': 'calculation not found'}), 404

        # Import calculator functions for breakdown and analysis
        try:
            from calculator import get_cost_breakdown, get_profitability_analysis
            
            calc_dict = calculation.to_dict()
            
            # Generate breakdown and analysis
            cost_data = {
                'labor_cost': calculation.labor_cost,
                'seed_cost': calculation.seed_cost,
                'fertilizer_cost': calculation.fertilizer_cost,
                'pesticide_cost': calculation.pesticide_cost,
                'water_cost': calculation.water_cost,
                'electricity_cost': calculation.electricity_cost,
                'transport_cost': calculation.transport_cost,
                'other_expenses': calculation.other_expenses
            }
            
            breakdown = get_cost_breakdown(cost_data)
            analysis = get_profitability_analysis(
                calculation.total_cost,
                calculation.total_profit,
                calculation.total_revenue
            )
            
            calc_dict['cost_breakdown'] = breakdown
            calc_dict['profitability_analysis'] = analysis
            
        except ImportError:
            calc_dict = calculation.to_dict()

        session.close()
        return jsonify(calc_dict), 200

    # ================== SHELF

    @app.route('/produce-assistant/predict-shelf-life', methods=['POST'])
    def predict_shelf_life():
        """Predict shelf life for produce based on storage conditions"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        data = request.get_json()
        if not data:
            return jsonify({'error': 'no input data provided'}), 400

        # Validate required fields
        required_fields = [
            'user_id', 'produce_type', 'quantity_kg', 'harvest_date', 'storage_method'
        ]
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400

        # Validate user exists
        session = session_local()
        user = session.query(user_model).filter_by(id=data['user_id']).first()
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404

        # Validate numeric fields
        try:
            quantity = float(data['quantity_kg'])
            if quantity <= 0:
                raise ValueError("Quantity must be greater than zero")
                
        except (ValueError, TypeError) as e:
            session.close()
            return jsonify({'error': f'invalid quantity: {str(e)}'}), 400

        # Get optional storage conditions
        storage_temp = data.get('storage_temperature_celsius')
        storage_humidity = data.get('storage_humidity_percent')
        
        if storage_temp is not None:
            try:
                storage_temp = float(storage_temp)
            except (ValueError, TypeError) as e:
                session.close()
                return jsonify({'error': 'storage_temperature_celsius must be a number'}), 400
        
        if storage_humidity is not None:
            try:
                storage_humidity = float(storage_humidity)
                if storage_humidity < 0 or storage_humidity > 100:
                    raise ValueError("Humidity must be between 0 and 100")
            except (ValueError, TypeError) as e:
                session.close()
                return jsonify({'error': f'invalid humidity: {str(e)}'}), 400

        # Parse harvest date
        import datetime
        try:
            harvest_date = data['harvest_date']
            if isinstance(harvest_date, str):
                harvest_date = datetime.datetime.fromisoformat(harvest_date.replace('Z', '+00:00'))
        except (ValueError, TypeError) as e:
            session.close()
            return jsonify({'error': f'invalid harvest_date format: {str(e)}. Use ISO format'}), 400

        # Import calculator functions
        try:
            from calculator import calculate_shelf_life, get_storage_recommendations, get_quality_timeline
        except ImportError:
            session.close()
            return jsonify({'error': 'calculator module not available'}), 500

        # Prepare calculation data
        calc_data = {
            'produce_type': data['produce_type'],
            'storage_method': data['storage_method'],
            'storage_temperature_celsius': storage_temp,
            'storage_humidity_percent': storage_humidity,
            'packaging_type': data.get('packaging_type', 'open'),
            'harvest_date': harvest_date
        }

        # Perform calculations
        try:
            predictions = calculate_shelf_life(calc_data)
            recommendations = get_storage_recommendations(
                data['produce_type'],
                calc_data
            )
            timeline = get_quality_timeline(
                harvest_date,
                predictions['predicted_shelf_life_days']
            )
        except ValueError as e:
            session.close()
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            session.close()
            return jsonify({'error': f'calculation failed: {str(e)}'}), 400

        # Calculate storage costs if provided
        storage_cost_per_day = data.get('storage_cost_per_day', 0)
        try:
            storage_cost_per_day = int(storage_cost_per_day)
            if storage_cost_per_day < 0:
                raise ValueError("Storage cost cannot be negative")
        except (ValueError, TypeError) as e:
            session.close()
            return jsonify({'error': f'invalid storage_cost_per_day: {str(e)}'}), 400

        # Calculate total storage cost
        total_storage_cost = storage_cost_per_day * predictions['predicted_shelf_life_days']

        # Create ShelfLifePrediction record
        prediction_record = shelf_life_prediction_model(
            user_id=data['user_id'],
            produce_type=data['produce_type'],
            quantity_kg=quantity,
            harvest_date=harvest_date,
            storage_method=data['storage_method'],
            storage_temperature_celsius=storage_temp,
            storage_humidity_percent=storage_humidity,
            packaging_type=data.get('packaging_type'),
            predicted_shelf_life_days=predictions['predicted_shelf_life_days'],
            quality_degradation_rate=predictions['quality_degradation_rate'],
            optimal_sell_by_date=predictions['optimal_sell_by_date'],
            spoilage_date=predictions['spoilage_date'],
            excellent_quality_until=predictions['excellent_quality_until'],
            good_quality_until=predictions['good_quality_until'],
            fair_quality_until=predictions['fair_quality_until'],
            storage_cost_per_day=storage_cost_per_day,
            estimated_total_storage_cost=total_storage_cost
        )

        session.add(prediction_record)
        session.commit()
        
        result = prediction_record.to_dict()
        result['storage_recommendations'] = recommendations
        result['quality_timeline'] = timeline
        result['modifiers_applied'] = predictions.get('modifiers_applied', {})
        
        session.close()
        return jsonify(result), 201

    @app.route('/produce-assistant/predictions/<int:user_id>', methods=['GET'])
    def get_user_predictions(user_id):
        """Get all shelf life predictions for a user"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        session = session_local()
        
        # Verify user exists
        user = session.query(user_model).filter_by(id=user_id).first()
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404

        # Get all predictions
        predictions = session.query(shelf_life_prediction_model).filter_by(
            user_id=user_id
        ).order_by(shelf_life_prediction_model.created_at.desc()).all()

        result = [pred.to_dict() for pred in predictions]
        session.close()
        return jsonify(result), 200

    @app.route('/produce-assistant/prediction/<int:pred_id>', methods=['GET'])
    def get_prediction_detail(pred_id):
        """Get detailed information for a specific shelf life prediction"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        session = session_local()
        
        prediction = session.query(shelf_life_prediction_model).filter_by(id=pred_id).first()
        if not prediction:
            session.close()
            return jsonify({'error': 'prediction not found'}), 404

        # Import calculator functions for recommendations and timeline
        try:
            from calculator import get_storage_recommendations, get_quality_timeline
            
            pred_dict = prediction.to_dict()
            
            # Generate recommendations and timeline
            storage_data = {
                'storage_method': prediction.storage_method,
                'storage_temperature_celsius': prediction.storage_temperature_celsius,
                'storage_humidity_percent': prediction.storage_humidity_percent,
                'packaging_type': prediction.packaging_type
            }
            
            recommendations = get_storage_recommendations(
                prediction.produce_type,
                storage_data
            )
            
            timeline = get_quality_timeline(
                prediction.harvest_date,
                prediction.predicted_shelf_life_days
            )
            
            pred_dict['storage_recommendations'] = recommendations
            pred_dict['quality_timeline'] = timeline
            
        except ImportError:
            pred_dict = prediction.to_dict()

        session.close()
        return jsonify(pred_dict), 200

    # ================== CROP RECOMMENDATION ENDPOINTS ==================

    @app.route('/produce-assistant/recommend-crops', methods=['POST'])
    def recommend_crops():
        """Get AI-powered crop recommendations based on land and climate conditions"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        data = request.get_json()
        if not data:
            return jsonify({'error': 'no input data provided'}), 400

        # Validate required fields
        required_fields = [
            'user_id', 'location', 'soil_type', 'land_size_hectares',
            'climate_zone', 'season'
        ]
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400

        # Validate user exists
        session = session_local()
        user = session.query(user_model).filter_by(id=data['user_id']).first()
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404

        # Validate numeric fields
        try:
            land_size = float(data['land_size_hectares'])
            if land_size <= 0:
                raise ValueError("Land size must be greater than zero")
        except (ValueError, TypeError) as e:
            session.close()
            return jsonify({'error': f'invalid land_size_hectares: {str(e)}'}), 400

        # Get optional fields
        soil_ph = data.get('soil_ph')
        if soil_ph is not None:
            try:
                soil_ph = float(soil_ph)
                if soil_ph < 0 or soil_ph > 14:
                    raise ValueError("pH must be between 0 and 14")
            except (ValueError, TypeError) as e:
                session.close()
                return jsonify({'error': f'invalid soil_ph: {str(e)}'}), 400

        avg_rainfall = data.get('average_rainfall_mm')
        if avg_rainfall is not None:
            try:
                avg_rainfall = float(avg_rainfall)
                if avg_rainfall < 0:
                    raise ValueError("Rainfall cannot be negative")
            except (ValueError, TypeError) as e:
                session.close()
                return jsonify({'error': f'invalid average_rainfall_mm: {str(e)}'}), 400

        avg_temp = data.get('average_temperature_celsius')
        if avg_temp is not None:
            try:
                avg_temp = float(avg_temp)
            except (ValueError, TypeError) as e:
                session.close()
                return jsonify({'error': f'invalid average_temperature_celsius: {str(e)}'}), 400

        irrigation_available = data.get('irrigation_available', False)
        if not isinstance(irrigation_available, bool):
            try:
                irrigation_available = str(irrigation_available).lower() in ['true', '1', 'yes']
            except:
                irrigation_available = False

        # Import recommendation functions
        try:
            from calculator import get_crop_recommendations, analyze_risk_factors, analyze_success_factors
        except ImportError:
            session.close()
            return jsonify({'error': 'calculator module not available'}), 500

        # Prepare user conditions
        user_conditions = {
            'location': data['location'],
            'soil_type': data['soil_type'],
            'soil_ph': soil_ph,
            'land_size_hectares': land_size,
            'climate_zone': data['climate_zone'],
            'average_rainfall_mm': avg_rainfall,
            'average_temperature_celsius': avg_temp,
            'season': data['season'],
            'irrigation_available': irrigation_available,
            'budget_category': data.get('budget_category'),
            'experience_level': data.get('experience_level')
        }

        # Get recommendations
        try:
            recommendations = get_crop_recommendations(user_conditions)
            
            # Analyze risks and success factors
            risks = analyze_risk_factors(user_conditions, recommendations['recommended_crops'])
            success_factors = analyze_success_factors(user_conditions, recommendations['recommended_crops'])
            
        except Exception as e:
            session.close()
            return jsonify({'error': f'recommendation failed: {str(e)}'}), 400

        # Prepare data for storage
        import json
        
        # Determine estimated yield range from top crop
        if recommendations['recommended_crops']:
            top_crop = recommendations['recommended_crops'][0]
            estimated_yield = top_crop.get('estimated_yield_kg_per_hectare', 'N/A')
        else:
            estimated_yield = 'N/A'

        # Create CropRecommendation record
        recommendation_record = crop_recommendation_model(
            user_id=data['user_id'],
            location=data['location'],
            soil_type=data['soil_type'],
            soil_ph=soil_ph,
            land_size_hectares=land_size,
            climate_zone=data['climate_zone'],
            average_rainfall_mm=avg_rainfall,
            average_temperature_celsius=avg_temp,
            season=data['season'],
            irrigation_available=irrigation_available,
            budget_category=data.get('budget_category'),
            experience_level=data.get('experience_level'),
            recommended_crops=json.dumps(recommendations['recommended_crops']),
            confidence_score=recommendations['confidence_score'],
            market_potential=recommendations['market_potential'],
            estimated_yield_range=estimated_yield,
            risk_factors=json.dumps(risks),
            success_factors=json.dumps(success_factors),
            alternative_crops=json.dumps(recommendations['alternative_crops'])
        )

        session.add(recommendation_record)
        session.commit()
        
        result = recommendation_record.to_dict()
        
        session.close()
        return jsonify(result), 201

    @app.route('/produce-assistant/recommendations/<int:user_id>', methods=['GET'])
    def get_user_recommendations(user_id):
        """Get all crop recommendations for a user"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        session = session_local()
        
        # Verify user exists
        user = session.query(user_model).filter_by(id=user_id).first()
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404

        # Get all recommendations
        recommendations = session.query(crop_recommendation_model).filter_by(
            user_id=user_id
        ).order_by(crop_recommendation_model.created_at.desc()).all()

        result = [rec.to_dict() for rec in recommendations]
        session.close()
        return jsonify(result), 200

    @app.route('/produce-assistant/recommendation/<int:rec_id>', methods=['GET'])
    def get_recommendation_detail(rec_id):
        """Get detailed information for a specific crop recommendation"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        session = session_local()
        
        recommendation = session.query(crop_recommendation_model).filter_by(id=rec_id).first()
        if not recommendation:
            session.close()
            return jsonify({'error': 'recommendation not found'}), 404

        result = recommendation.to_dict()
        session.close()
        return jsonify(result), 200

    # ========== FORUM ENDPOINTS ==========

    @app.route('/forum/posts', methods=['POST'])
    def create_forum_post():
        """Create a new forum post"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        data = request.get_json()
        if not data:
            return jsonify({'error': 'invalid json'}), 400

        required = ['author_id', 'title', 'content', 'category']
        if not all(k in data for k in required):
            return jsonify({'error': 'missing required fields'}), 400

        session = session_local()
        
        # Check if user is banned
        user = session.query(user_model).filter_by(id=data['author_id']).first()
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404
            
        if user.is_banned:
            reason = user.ban_reason if user.ban_reason else "No reason provided"
            session.close()
            return jsonify({'error': f'account is banned\nReason: {reason}'}), 403

        post = forum_post_model(
            author_id=data['author_id'],
            title=data['title'],
            content=data['content'],
            category=data['category'],
            location_state=data.get('location_state'),
            crop_type=data.get('crop_type')
        )
        
        session.add(post)
        session.commit()
        session.refresh(post)
        result = post.to_dict()
        session.close()
        
        return jsonify(result), 201

    @app.route('/forum/posts', methods=['GET'])
    def get_forum_posts():
        """Get all forum posts with optional filtering"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        category = request.args.get('category')
        location = request.args.get('location')
        crop = request.args.get('crop')
        
        session = session_local()
        query = session.query(forum_post_model)
        
        if category and category != 'all':
            query = query.filter_by(category=category)
        if location:
            query = query.filter_by(location_state=location)
        if crop:
            query = query.filter_by(crop_type=crop)
            
        # Sorting
        sort_by = request.args.get('sort_by', 'recent')
        if sort_by == 'popular':
            query = query.order_by(forum_post_model.upvotes.desc())
        elif sort_by == 'unpopular':
            query = query.order_by(forum_post_model.upvotes.asc())
        elif sort_by == 'oldest':
            query = query.order_by(forum_post_model.created_at.asc())
        else: # recent
            query = query.order_by(forum_post_model.created_at.desc())

        posts = query.all()
        result = [p.to_dict() for p in posts]
        session.close()
        
        return jsonify(result), 200

    @app.route('/forum/posts/<int:post_id>', methods=['GET'])
    def get_forum_post(post_id):
        """Get a specific forum post with comments"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        session = session_local()
        post = session.query(forum_post_model).filter_by(id=post_id).first()
        
        if not post:
            session.close()
            return jsonify({'error': 'post not found'}), 404
            
        # Increment view count
        post.view_count += 1
        session.commit()
        
        result = post.to_dict()
        
        # Get comments (only top-level)
        comments = session.query(forum_comment_model).filter_by(post_id=post_id, parent_id=None).order_by(forum_comment_model.created_at).all()
        result['comments'] = [c.to_dict() for c in comments]
        
        session.close()
        return jsonify(result), 200

    @app.route('/forum/posts/<int:post_id>/comments', methods=['POST'])
    def add_forum_comment(post_id):
        """Add a comment to a forum post"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        data = request.get_json()
        if not data:
            return jsonify({'error': 'invalid json'}), 400

        required = ['author_id', 'content']
        if not all(k in data for k in required):
            return jsonify({'error': 'missing required fields'}),  400

        session = session_local()
        
        # Check if post exists
        post = session.query(forum_post_model).filter_by(id=post_id).first()
        if not post:
            session.close()
            return jsonify({'error': 'post not found'}), 404
            
        if post.is_locked:
            session.close()
            return jsonify({'error': 'post is locked'}), 403
            
        # Check if user is banned
        user = session.query(user_model).filter_by(id=data['author_id']).first()
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404
            
        if user.is_banned:
            reason = user.ban_reason if user.ban_reason else "No reason provided"
            session.close()
            return jsonify({'error': f'account is banned\nReason: {reason}'}), 403

        comment = forum_comment_model(
            post_id=post_id,
            author_id=data['author_id'],
            content=data['content'],
            parent_id=data.get('parent_id')
        )
        
        session.add(comment)
        session.commit()
        session.refresh(comment)
        result = comment.to_dict()
        session.close()
        
        return jsonify(result), 201

    @app.route('/forum/posts/<int:post_id>/vote', methods=['POST'])
    def vote_forum_post(post_id):
        """Vote on a forum post"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        data = request.get_json()
        if not data:
            return jsonify({'error': 'invalid json'}), 400

        required = ['user_id', 'vote_type'] # vote_type: upvote, downvote
        if not all(k in data for k in required):
            return jsonify({'error': 'missing required fields'}), 400

        session = session_local()
        
        # Check if user is banned
        user = session.query(user_model).filter_by(id=data['user_id']).first()
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404
            
        if user.is_banned:
            reason = user.ban_reason if user.ban_reason else "No reason provided"
            session.close()
            return jsonify({'error': f'account is banned\nReason: {reason}'}), 403
        
        post = session.query(forum_post_model).filter_by(id=post_id).first()
        if not post:
            session.close()
            return jsonify({'error': 'post not found'}), 404

        # Check if user already voted
        existing_vote = session.query(forum_vote_model).filter_by(
            user_id=data['user_id'],
            post_id=post_id
        ).first()
        
        if existing_vote:
            # If changing vote type
            if existing_vote.vote_type != data['vote_type']:
                existing_vote.vote_type = data['vote_type']
                if data['vote_type'] == 'upvote':
                    post.upvotes += 2 # -1 for removing downvote, +1 for upvote
                else:
                    post.upvotes -= 2
            else:
                # Same vote type - toggle off (remove vote)
                session.delete(existing_vote)
                if data['vote_type'] == 'upvote':
                    post.upvotes -= 1
                else:
                    post.upvotes += 1
        else:
            # New vote
            vote = forum_vote_model(
                user_id=data['user_id'],
                post_id=post_id,
                vote_type=data['vote_type']
            )
            session.add(vote)
            if data['vote_type'] == 'upvote':
                post.upvotes += 1
            else:
                post.upvotes -= 1
        
        session.commit()
        result = {'upvotes': post.upvotes}
        session.close()
        
        return jsonify(result), 200

    @app.route('/forum/posts/<int:post_id>/pin', methods=['POST'])
    def pin_forum_post(post_id):
        """Pin or unpin a forum post (Admin/Moderator only)"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({'error': 'user_id required'}), 400

        session = session_local()
        
        # Verify user is admin or moderator
        user = session.query(user_model).filter_by(id=data['user_id']).first()
        if not user or user.account_type not in ['admin', 'super_admin', 'moderator']:
            session.close()
            return jsonify({'error': 'unauthorized'}), 403

        post = session.query(forum_post_model).filter_by(id=post_id).first()
        if not post:
            session.close()
            return jsonify({'error': 'post not found'}), 404

        # Toggle pin status
        post.is_pinned = not post.is_pinned
        session.commit()
        
        result = {'is_pinned': post.is_pinned}
        session.close()
        
        return jsonify(result), 200

    # ========== Report System Endpoints ==========
    
    @app.route('/reports/create', methods=['POST'])
    def create_report():
        """Allow users to report violations"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'invalid json'}), 400
        
        # Required fields
        required = ['reporter_id', 'report_type', 'description']
        if not all(k in data for k in required):
            return jsonify({'error': 'missing required fields: reporter_id, report_type, description'}), 400
        
        # At least one target must be specified
        if not any(k in data for k in ['reported_user_id', 'reported_listing_id', 'reported_worker_id']):
            return jsonify({'error': 'must specify at least one target: reported_user_id, reported_listing_id, or reported_worker_id'}), 400
        
        # Validate report type
        valid_types = ['fraud', 'spam', 'harassment', 'inappropriate', 'scam', 'fake_listing']
        if data['report_type'] not in valid_types:
            return jsonify({'error': f'invalid report_type. Must be one of: {valid_types}'}), 400
        
        session = session_local()
        
        # Verify reporter exists
        reporter = session.query(user_model).filter_by(id=data['reporter_id']).first()
        if not reporter:
            session.close()
            return jsonify({'error': 'reporter not found'}), 404
            
        if reporter.is_banned:
            reason = reporter.ban_reason if reporter.ban_reason else "No reason provided"
            session.close()
            return jsonify({'error': f'account is banned\nReason: {reason}'}), 403
        
        # Create report
        report = report_model(
            reporter_id=data['reporter_id'],
            reported_user_id=data.get('reported_user_id'),
            reported_listing_id=data.get('reported_listing_id'),
            reported_worker_id=data.get('reported_worker_id'),
            report_type=data['report_type'],
            description=data['description']
        )
        
        
        session.add(report)
        session.commit()
        session.refresh(report)
        result = report.to_dict()
        session.close()
        
        return jsonify(result), 201
    
    @app.route('/reports/my-reports/<int:user_id>', methods=['GET'])
    def get_my_reports(user_id):
        """Get all reports created by a user"""
        if not db_available:

            return jsonify({'error': 'database not available'}), 500
        
        session = session_local()
        
        # Verify user exists
        user = session.query(user_model).filter_by(id=user_id).first()
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404
        
        reports = session.query(report_model).filter_by(reporter_id=user_id).all()
        result = [r.to_dict() for r in reports]
        session.close()
        
        return jsonify(result), 200

    
    # ========== Moderator Endpoints ==========
    
    @app.route('/admin/reports', methods=['POST'])
    @require_moderator
    def get_all_reports():
        """Moderator: Get all reports (with optional filters)"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500
        
        data = request.get_json() or {}
        session = session_local()
        
        query = session.query(report_model)
        
        # Filter by status
        if 'status' in data:
            query = query.filter_by(status=data['status'])
        
        # Filter by report type
        if 'report_type' in data:
            query = query.filter_by(report_type=data['report_type'])
        
        reports = query.all()
        result = [r.to_dict() for r in reports]
        session.close()
        
        return jsonify(result), 200
    
    @app.route('/admin/reports/<int:report_id>/resolve', methods=['POST'])
    @limiter.limit("20 per minute")
    @require_moderator
    def resolve_report(report_id):
        """Moderator: Resolve a report"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'invalid json'}), 400

        admin_id = data.get('admin_id')
        if not admin_id:
            return jsonify({'error': 'admin_id required'}), 400
        
        session = session_local()
        
        report = session.query(report_model).filter_by(id=report_id).first()
        if not report:
            session.close()
            return jsonify({'error': 'report not found'}), 404
        
        # Update report
        report.status = data.get('status', 'resolved')  # resolved or dismissed
        report.resolved_at = datetime.datetime.now(datetime.timezone.utc)
        report.resolved_by = admin_id
        report.resolution_notes = data.get('resolution_notes')
        
        session.commit()
        session.close()
        
        return jsonify({'message': 'report updated'}), 200

    @app.route('/admin/users', methods=['POST'])
    @require_admin
    def get_all_users():
        """Admin: Get list of all users"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500
        
        session = session_local()
        users = session.query(user_model).all()
        result = [u.to_dict() for u in users]
        session.close()
        
        return jsonify(result), 200

    @app.route('/admin/listings/<int:listing_id>/hide', methods=['POST'])
    @limiter.limit("20 per minute")
    @require_moderator
    def hide_listing(listing_id):
        """Moderator: Hide a listing pending review"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'invalid json'}), 400
        
        admin_id = data.get('admin_id')
        reason = data.get('reason', '')
        
        session = session_local()
        
        listing = session.query(listing_model).filter_by(id=listing_id).first()
        if not listing:
            session.close()
            return jsonify({'error': 'listing not found'}), 404
        
        # Add a hidden/status field (you may need to add this to Listing model)
        # For now, we'll just log the action
        
        log_admin_action(
            admin_id=admin_id,
            action='hide_listing',
            target_type='listing',
            target_id=listing_id,
            reason=reason,
            details=f"Listing title: {listing.title}"
        )
        
        session.close()
        
        return jsonify({'message': 'listing hidden successfully', 'listing_id': listing_id}), 200
    
    @app.route('/admin/listings/<int:listing_id>', methods=['DELETE'])
    @limiter.limit("10 per minute")
    @require_moderator
    def delete_listing_admin(listing_id):
        """Moderator: Delete a fraudulent listing"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500
        
        try:
            data = request.get_json()
        except Exception:
            data = None

        if not data or 'admin_id' not in data:
            return jsonify({'error': 'missing required field: admin_id'}), 400

        admin_id = data['admin_id']
        
        session = session_local()
        
        listing = session.query(listing_model).filter_by(id=listing_id).first()

        if not listing:
            session.close()
            return jsonify({'error': 'listing not found'}), 404
        
        listing_title = listing.title
        
        session.delete(listing)
        session.commit()
        
        log_admin_action(
            admin_id=admin_id,
            action='delete_listing',
            target_type='listing',
            target_id=listing_id,
            reason=data.get('reason', ''),
            details=f"Deleted listing: {listing_title}"
        )
        
        session.close()
        
        return jsonify({'message': 'listing deleted successfully'}), 200
    
    # ========== Admin Endpoints ==========
    
    @app.route('/admin/users/<int:user_id>/ban', methods=['POST'])
    @limiter.limit("10 per minute")
    @require_admin
    def ban_user(user_id):
        """Admin: Ban a user"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'invalid json'}), 400
        
        try:
            validated_data = BanUserSchema().load(data)
        except ValidationError as err:
            return jsonify({'error': err.messages}), 400
        
        admin_id = data.get('admin_id')
        reason = validated_data.get('reason')
        
        session = session_local()
        
        user = session.query(user_model).filter_by(id=user_id).first()
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404
        
        if user.is_banned:
            session.close()
            return jsonify({'error': 'user is already banned'}), 400
        
        # Ban the user
        user.is_banned = True
        user.banned_at = datetime.datetime.now(datetime.timezone.utc)
        user.banned_by = admin_id
        user.ban_reason = reason
        
        session.commit()
        
        log_admin_action(
            admin_id=admin_id,
            action='ban_user',
            target_type='user',
            target_id=user_id,
            reason=reason,
            details=f"Banned user: {user.email}"
        )
        
        result = user.to_dict()
        session.close()
        
        return jsonify(result), 200
    
    @app.route('/admin/users/<int:user_id>/unban', methods=['POST'])
    @limiter.limit("10 per minute")
    @require_admin
    def unban_user(user_id):
        """Admin: Unban a user"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'invalid json'}), 400
        
        admin_id = data.get('admin_id')
        
        session = session_local()
        
        user = session.query(user_model).filter_by(id=user_id).first()
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404
        
        if not user.is_banned:
            session.close()
            return jsonify({'error': 'user is not banned'}), 400
        
        # Unban the user
        user.is_banned = False
        user.banned_at = None
        user.banned_by = None
        user.ban_reason = None
        
        session.commit()
        
        log_admin_action(
            admin_id=admin_id,
            action='unban_user',
            target_type='user',
            target_id=user_id,
            reason='User unbanned',
            details=f"Unbanned user: {user.email}"
        )
        
        result = user.to_dict()
        session.close()
        
        return jsonify(result), 200
    
    @app.route('/admin/users/banned', methods=['POST'])
    @require_admin
    def get_banned_users():
        """Admin: Get list of all banned users"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500
        
        session = session_local()
        
        banned_users = session.query(user_model).filter_by(is_banned=True).all()
        result = [u.to_dict() for u in banned_users]
        session.close()
        
        return jsonify(result), 200
    
    @app.route('/admin/create-moderator', methods=['POST'])
    @require_super_admin
    def create_moderator():
        """Super Admin: Create a moderator account"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'invalid json'}), 400
        
        try:
            validated_data = CreateModeratorSchema().load(data)
        except ValidationError as err:
            return jsonify({'error': err.messages}), 400
        
        admin_id = data.get('admin_id')
        
        session = session_local()
        
        # Check if email already exists
        existing = session.query(user_model).filter_by(email=validated_data['email']).first()
        if existing:
            session.close()
            return jsonify({'error': 'email already registered'}), 409
        
        # Create moderator account
        moderator = user_model(
            full_name=validated_data['full_name'],
            email=validated_data['email'],
            account_type='moderator'
        )
        moderator.set_password(validated_data['password'])
        
        session.add(moderator)
        session.commit()
        session.refresh(moderator)
        
        log_admin_action(
            admin_id=admin_id,
            action='create_moderator',
            target_type='user',
            target_id=moderator.id,
            reason='Created new moderator account',
            details=f"Moderator email: {moderator.email}"
        )
        
        result = moderator.to_dict()
        session.close()
        
        return jsonify(result), 201
    
    @app.route('/admin/create-admin', methods=['POST'])
    @require_super_admin
    def create_admin():
        """Super Admin: Create an admin account"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'invalid json'}), 400
        
        try:
            validated_data = CreateAdminSchema().load(data)
        except ValidationError as err:
            return jsonify({'error': err.messages}), 400
        
        admin_id = data.get('admin_id')
        
        session = session_local()
        
        # Check if email already exists
        existing = session.query(user_model).filter_by(email=validated_data['email']).first()
        if existing:
            session.close()
            return jsonify({'error': 'email already registered'}), 409
        
        # Create admin account
        new_admin = user_model(
            full_name=validated_data['full_name'],
            email=validated_data['email'],
            account_type='admin'
        )
        new_admin.set_password(validated_data['password'])
        
        session.add(new_admin)
        session.commit()
        session.refresh(new_admin)
        
        log_admin_action(
            admin_id=admin_id,
            action='create_admin',
            target_type='user',
            target_id=new_admin.id,
            reason='Created new admin account',
            details=f"Admin email: {new_admin.email}"
        )
        
        result = new_admin.to_dict()
        session.close()
        
        return jsonify(result), 201
    
    @app.route('/admin/audit-logs', methods=['POST'])
    @require_admin
    def get_audit_logs():
        """Super Admin: Get all audit logs (with optional filters)"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500
        
        data = request.get_json() or {}
        session = session_local()
        
        query = session.query(admin_audit_log_model)
        
        # Filter by admin_id
        if 'filter_admin_id' in data:
            query = query.filter_by(admin_id=data['filter_admin_id'])
        
        # Filter by action
        if 'action' in data:
            query = query.filter_by(action=data['action'])
        
        # Filter by target_type
        if 'target_type' in data:
            query = query.filter_by(target_type=data['target_type'])
        
        # Limit results
        limit = data.get('limit', 100)
        logs = query.order_by(admin_audit_log_model.created_at.desc()).limit(limit).all()
        
        result = [log.to_dict() for log in logs]
        session.close()
        
        return jsonify(result), 200


    @app.route('/admin/audit-logs/mark-read', methods=['POST'])
    @require_admin
    def mark_audit_logs_read():
        """Mark one or more audit log entries as read. JSON: { ids: [1,2,3] } or { mark_all: true }"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        data = request.get_json() or {}
        session = session_local()
        try:
            if data.get('mark_all'):
                session.query(admin_audit_log_model).update({ admin_audit_log_model.read: True })
                session.commit()
                session.close()
                return jsonify({'message': 'All logs marked read'}), 200

            ids = data.get('ids') or []
            if not ids:
                session.close()
                return jsonify({'error': 'ids required'}), 400

            session.query(admin_audit_log_model).filter(admin_audit_log_model.id.in_(ids)).update({ admin_audit_log_model.read: True }, synchronize_session=False)
            session.commit()
            session.close()
            return jsonify({'message': 'Marked specified logs as read'}), 200
        except Exception as e:
            session.rollback()
            session.close()
            return jsonify({'error': str(e)}), 500


    @app.route('/api/admin/fee-transactions', methods=['GET'])
    @require_admin
    def api_fee_transactions():
        """Return recent transactions that are marked as fees for debugging/inspection"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        limit = int(request.args.get('limit', 20))
        session = session_local()
        try:
            q = session.query(transaction_model).filter_by(transaction_type='fee').order_by(transaction_model.created_at.desc()).limit(limit).all()
            results = [t.to_dict() for t in q]
            try:
                record_admin_action('api_view_fee_transactions', 'transactions')
            except Exception:
                pass
            return jsonify(results), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Payment & Wallet Routes (Milestone 8)
    # -------------------------------------------------------------------------

    def verify_interswitch_transaction(reference, amount_in_naira):
        url = config.INTERSWITCH_VERIFY_URL
        # Interswitch API expects amount in Kobo (minor unit)
        # We convert Naira to Kobo here for the API call only
        amount_in_kobo = int(amount_in_naira * 100)
        
        params = {
            "merchantcode": config.INTERSWITCH_MERCHANT_CODE,
            "transactionreference": reference,
            "amount": amount_in_kobo
        }
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.get(url, params=params, headers=headers)
            return response.json()
        except Exception as e:
            logging.error(f"Interswitch verification error: {e}")
            return None

    @app.route('/api/wallet/fund', methods=['POST'])
    def fund_wallet():
        """Initialize a transaction to fund the wallet"""
        if not db_available or session_local is None:
            return jsonify({'error': 'database not available'}), 503

        data = request.get_json()
        user_id = data.get('user_id')
        amount = data.get('amount')
        email = data.get('email')
        name = data.get('name', 'Customer') # Optional name

        if not all([user_id, amount, email]):
            return jsonify({'error': 'user_id, amount, and email are required'}), 400

        try:
            amount = float(amount)
            if amount <= 0:
                return jsonify({'error': 'Amount must be positive'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid amount'}), 400

        # Create a pending transaction record
        session = session_local()
        
        # Ensure wallet exists
        wallet = session.query(wallet_model).filter_by(user_id=user_id).first()
        if not wallet:
            wallet = wallet_model(user_id=user_id)
            session.add(wallet)
            session.commit() # Commit to get wallet ID

        # Generate Reference
        reference = uuid.uuid4().hex[:12].upper()
        
        # Calculate total amount to charge (Amount + Deposit Fee)
        # Option A: Pass fee to user
        deposit_fee = amount * config.DEPOSIT_FEE_PERCENTAGE
        total_charge = amount + deposit_fee
        
        # Interswitch expects amount in Kobo for the form
        amount_kobo = int(total_charge * 100)
        
        # Callback URL
        callback_url = request.host_url.rstrip('/') + '/api/payment/callback'
        
        transaction = transaction_model(
            wallet_id=wallet.id,
            amount=amount, # We credit the requested amount in Naira, the extra is the fee
            transaction_type='credit',
            status='pending',
            reference=reference,
            description=f"Wallet funding: {amount} (Fee: {deposit_fee:.2f})"
        )
        session.add(transaction)
        session.commit()
        session.close()

        # Return parameters for the frontend to construct the form
        return jsonify({
            'payment_url': config.INTERSWITCH_PAYMENT_URL,
            'merchant_code': config.INTERSWITCH_MERCHANT_CODE,
            'pay_item_id': config.INTERSWITCH_PAY_ITEM_ID,
            'txn_ref': reference,
            'amount': amount_kobo, # Charge the total including fee (in Kobo for Interswitch)
            'currency': 566, # NGN
            'cust_name': name,
            'cust_email': email,
            'site_redirect_url': callback_url,
            'message': f'Submit a POST request to payment_url. Total charge: {total_charge:.2f} (includes {deposit_fee:.2f} fee)'
        }), 200

    @app.route('/api/payment/callback', methods=['GET', 'POST'])
    def payment_callback():
        """Verify payment from Interswitch callback"""
        # Interswitch can send data via POST or GET
        reference = request.values.get('txn_ref') or request.values.get('txnref')
        
        if not reference:
            return jsonify({'error': 'No reference provided'}), 400

        if not db_available or session_local is None:
            return jsonify({'error': 'database not available'}), 503

        session = session_local()
        transaction = session.query(transaction_model).filter_by(reference=reference).first()
        
        if not transaction:
            session.close()
            return jsonify({'error': 'Transaction not found'}), 404

        if transaction.status == 'success':
            session.close()
            return jsonify({'message': 'Transaction already verified', 'status': 'success'}), 200

        # Verify with Interswitch
        # We need to verify the TOTAL amount charged (amount + fee)
        deposit_fee = transaction.amount * config.DEPOSIT_FEE_PERCENTAGE
        total_charge = transaction.amount + deposit_fee
        
        # Verify using Naira amount (function handles conversion to Kobo for API)
        verification = verify_interswitch_transaction(reference, total_charge)
        
        # Check Response Code "00" means Successful
        if verification and verification.get('ResponseCode') == '00':
            # Double check amount (Interswitch returns amount in Kobo)
            verified_amount_kobo = int(verification.get('Amount', 0))
            expected_amount_kobo = int(total_charge * 100)
            
            # Allow small floating point difference tolerance if needed, but kobo is integer
            if abs(verified_amount_kobo - expected_amount_kobo) <= 10: # Tolerance of 10 kobo
                # Update transaction
                transaction.status = 'success'

                # Update wallet balance
                wallet = session.query(wallet_model).filter_by(id=transaction.wallet_id).first()
                if wallet:
                    wallet.balance += transaction.amount

                # Create a notification/message for the user (simple hook)
                try:
                    # Determine user id from wallet
                    user_id = wallet.user_id if wallet else None
                    if user_id and message_model is not None:
                        msg_subject = 'Wallet credited'
                        msg_body = f"Your wallet has been credited with ₦{transaction.amount:.2f}. New balance: ₦{wallet.balance:.2f}"
                        msg = message_model(sender_id=user_id, recipient_id=user_id, subject=msg_subject, content=msg_body)
                        session.add(msg)
                except Exception as e:
                    logging.exception('Failed to create deposit notification: %s', e)

                # Capture values before closing session
                amount = transaction.amount
                new_balance = wallet.balance if wallet else 0

                session.commit()
                session.close()
                # If this was a browser redirect (user returning from the payment page), send them to the wallet UI.
                # Detect browser returns by checking Accept and User-Agent headers so POSTs from the provider
                # that are intended to be browser redirects will also be redirected to the wallet UI.
                ua = (request.headers.get('User-Agent') or '').lower()
                accept = (request.headers.get('Accept') or '').lower()
                is_browser_return = (
                    ('text/html' in accept) or
                    ('mozilla' in ua) or
                    bool(request.headers.get('Referer'))
                ) and (request.values.get('txn_ref') or request.values.get('txnref'))
                if is_browser_return:
                    # Include minimal info as query params so the frontend can show a message.
                    redirect_url = request.host_url.rstrip('/') + url_for('wallet_page') + f"?payment=success&txn_ref={reference}&amount={amount}"
                    return redirect(redirect_url)
                return jsonify({'status': 'success', 'message': 'Payment successful', 'amount': amount, 'new_balance': new_balance}), 200
            else:
                transaction.status = 'failed' # Amount mismatch
                session.commit()
                session.close()
                # Redirect browser back to wallet with failure info if appropriate
                ua = (request.headers.get('User-Agent') or '').lower()
                accept = (request.headers.get('Accept') or '').lower()
                is_browser_return = (
                    ('text/html' in accept) or
                    ('mozilla' in ua) or
                    bool(request.headers.get('Referer'))
                ) and (request.values.get('txn_ref') or request.values.get('txnref'))
                if is_browser_return:
                    redirect_url = request.host_url.rstrip('/') + url_for('wallet_page') + f"?payment=failed&reason=amount_mismatch&txn_ref={reference}"
                    return redirect(redirect_url)
                return jsonify({'error': f'Payment verification failed: Amount mismatch. Expected {expected_amount_kobo}, got {verified_amount_kobo}'}), 400
        else:
            transaction.status = 'failed'
            session.commit()
            session.close()
            reason = verification.get('ResponseDescription') if verification else 'Unknown error'
            ua = (request.headers.get('User-Agent') or '').lower()
            accept = (request.headers.get('Accept') or '').lower()
            is_browser_return = (
                ('text/html' in accept) or
                ('mozilla' in ua) or
                bool(request.headers.get('Referer'))
            ) and (request.values.get('txn_ref') or request.values.get('txnref'))
            if is_browser_return:
                redirect_url = request.host_url.rstrip('/') + url_for('wallet_page') + f"?payment=failed&reason={reason}&txn_ref={reference}"
                return redirect(redirect_url)
            return jsonify({'error': f'Payment verification failed: {reason}'}), 400

    @app.route('/api/wallet/balance/<int:user_id>', methods=['GET'])
    def get_wallet_balance(user_id):
        """Get user wallet balance"""
        if not db_available or session_local is None:
            return jsonify({'error': 'database not available'}), 503

        session = session_local()
        wallet = session.query(wallet_model).filter_by(user_id=user_id).first()
        
        if not wallet:
            # Create wallet if it doesn't exist
            wallet = wallet_model(user_id=user_id)
            session.add(wallet)
            session.commit()
        
        balance = wallet.balance
        currency = wallet.currency
        session.close()
        
        return jsonify({'user_id': user_id, 'balance': balance, 'currency': currency}), 200

    @app.route('/api/wallet/transactions/<int:user_id>', methods=['GET'])
    def get_wallet_transactions(user_id):
        """Get user transaction history"""
        if not db_available or session_local is None:
            return jsonify({'error': 'database not available'}), 503

        session = session_local()
        wallet = session.query(wallet_model).filter_by(user_id=user_id).first()
        
        if not wallet:
            session.close()
            return jsonify([]), 200
            
        transactions = session.query(transaction_model).filter_by(wallet_id=wallet.id).order_by(transaction_model.created_at.desc()).all()
        result = [t.to_dict() for t in transactions]
        session.close()
        
        return jsonify(result), 200

    @app.route('/api/bank-accounts', methods=['POST'])
    def add_bank_account():
        """Add a new bank account for withdrawals"""
        if not db_available or session_local is None:
            return jsonify({'error': 'database not available'}), 503

        data = request.get_json()
        user_id = data.get('user_id')
        bank_name = data.get('bank_name')
        account_number = data.get('account_number')
        account_name = data.get('account_name')
        bank_code = data.get('bank_code') # Optional

        if not all([user_id, bank_name, account_number, account_name]):
            return jsonify({'error': 'Missing required fields'}), 400

        session = session_local()
        
        # Check if user exists
        user = session.query(user_model).filter_by(id=user_id).first()
        if not user:
            session.close()
            return jsonify({'error': 'User not found'}), 404

        # Check if account already exists
        existing = session.query(bank_account_model).filter_by(
            user_id=user_id, 
            account_number=account_number
        ).first()
        
        if existing:
            session.close()
            return jsonify({'error': 'Bank account already added'}), 409

        # Check if this is the first account, make it default
        count = session.query(bank_account_model).filter_by(user_id=user_id).count()
        is_default = (count == 0)

        account = bank_account_model(
            user_id=user_id,
            bank_name=bank_name,
            account_number=account_number,
            account_name=account_name,
            bank_code=bank_code,
            is_default=is_default
        )
        session.add(account)
        session.commit()
        session.refresh(account)
        
        result = account.to_dict()
        session.close()
        return jsonify(result), 201

    @app.route('/api/bank-accounts/<int:user_id>', methods=['GET'])
    def get_bank_accounts(user_id):
        """Get all bank accounts for a user"""
        if not db_available or session_local is None:
            return jsonify({'error': 'database not available'}), 503

        session = session_local()
        accounts = session.query(bank_account_model).filter_by(user_id=user_id).all()
        result = [acc.to_dict() for acc in accounts]
        session.close()
        return jsonify(result), 200

    @app.route('/api/wallet/withdraw', methods=['POST'])
    def withdraw_funds():
        """Request a withdrawal to a bank account"""
        if not db_available or session_local is None:
            return jsonify({'error': 'database not available'}), 503

        data = request.get_json()
        user_id = data.get('user_id')
        amount = data.get('amount')
        bank_account_id = data.get('bank_account_id')

        if not all([user_id, amount, bank_account_id]):
            return jsonify({'error': 'Missing required fields'}), 400

        try:
            amount = float(amount)
            if amount <= 0:
                return jsonify({'error': 'Amount must be positive'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid amount'}), 400

        session = session_local()
        
        # Get user to check account type for fee exemption
        user = session.query(user_model).get(user_id)
        if not user:
            session.close()
            return jsonify({'error': 'User not found'}), 404

        # Determine fee
        fee = config.WITHDRAWAL_FEE
        # Exempt super_admin (Business Account) from fees
        if user.account_type == 'super_admin':
            fee = 0.0

        # Check wallet balance
        wallet = session.query(wallet_model).filter_by(user_id=user_id).first()
        
        total_deduction = amount + fee
        
        if not wallet or wallet.balance < total_deduction:
            session.close()
            return jsonify({'error': f'Insufficient funds. Balance must cover amount + fee ({fee})'}), 400

        # Check bank account ownership
        bank_account = session.query(bank_account_model).filter_by(id=bank_account_id, user_id=user_id).first()
        if not bank_account:
            session.close()
            return jsonify({'error': 'Invalid bank account'}), 400

        # Deduct funds immediately
        wallet.balance -= total_deduction
        
        # Create transaction record for withdrawal
        reference = f"WTH-{uuid.uuid4().hex[:12].upper()}"
        transaction = transaction_model(
            wallet_id=wallet.id,
            amount=amount,
            transaction_type='withdrawal',
            status='pending', # Pending admin approval or processing
            reference=reference,
            description=f"Withdrawal to {bank_account.bank_name} - {bank_account.account_number}"
        )
        session.add(transaction)
        
        # Handle Fee
        fee_tx_id = None
        if fee > 0:
            # 1. Create transaction record for fee deduction (User side)
            fee_reference = f"FEE-{uuid.uuid4().hex[:12].upper()}"
            fee_transaction = transaction_model(
                wallet_id=wallet.id,
                amount=fee,
                transaction_type='fee',
                status='success', # Fee is taken immediately
                reference=fee_reference,
                description=f"Fee for withdrawal {reference}"
            )
            session.add(fee_transaction)
            
            # 2. Credit Fee to Business Account (Super Admin)
            # Find the super admin user
            system_user = session.query(user_model).filter_by(account_type='super_admin').first()
            if system_user:
                system_wallet = session.query(wallet_model).filter_by(user_id=system_user.id).first()
                if system_wallet:
                    system_wallet.balance += fee
                    system_fee_credit = transaction_model(
                        wallet_id=system_wallet.id,
                        amount=fee,
                        transaction_type='deposit', # Treat as deposit/income
                        status='success',
                        reference=f"INC-{fee_reference}",
                        description=f"Fee income from withdrawal {reference}"
                    )
                    session.add(system_fee_credit)
        
        session.commit()
        
        # In a real app, we would trigger an async job here to process the payout via Interswitch
        # For this implementation, we leave it as 'pending' for admin review or manual processing
        
        result = transaction.to_dict()
        if fee > 0:
            # We need to refresh to get the ID if we want to return it, 
            # but since we committed, we might need to query it or just rely on the object if session is still valid.
            # However, session.commit() expires objects.
            pass

        new_balance = wallet.balance
        session.close()
        
        return jsonify({
            'message': 'Withdrawal request submitted successfully',
            'transaction': result,
            'fee_amount': fee,
            'new_balance': new_balance
        }), 201

    # ========== RATING ENDPOINTS ==========

    @app.route('/ratings', methods=['POST'])
    def submit_rating():
        """Submit a rating for a user"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        data = request.get_json()
        if not data:
            return jsonify({'error': 'invalid json'}), 400

        required = ['rater_id', 'rated_user_id', 'rating_value']
        if not all(k in data for k in required):
            return jsonify({'error': 'missing required fields'}), 400

        # Validate rating value
        try:
            rating_value = int(data['rating_value'])
            if rating_value < 1 or rating_value > 5:
                return jsonify({'error': 'rating must be between 1 and 5'}), 400
        except ValueError:
            return jsonify({'error': 'rating must be an integer'}), 400

        if data['rater_id'] == data['rated_user_id']:
            return jsonify({'error': 'cannot rate yourself'}), 400

        session = session_local()
        
        # Check if users exist
        rater = session.query(user_model).filter_by(id=data['rater_id']).first()
        rated_user = session.query(user_model).filter_by(id=data['rated_user_id']).first()
        
        if not rater or not rated_user:
            session.close()
            return jsonify({'error': 'user not found'}), 404

        if rater.is_banned:
            reason = rater.ban_reason if rater.ban_reason else "No reason provided"
            session.close()
            return jsonify({'error': f'account is banned\nReason: {reason}'}), 403

        # Check if already rated
        existing_rating = session.query(rating_model).filter_by(
            rater_id=data['rater_id'],
            rated_user_id=data['rated_user_id']
        ).first()
        
        if existing_rating:
            # Update existing rating
            old_rating = existing_rating.rating_value
            existing_rating.rating_value = rating_value
            existing_rating.comment = data.get('comment')
            existing_rating.created_at = datetime.datetime.now(datetime.timezone.utc)
            
            # Update user average
            # New average = ((Old Avg * Count) - Old Rating + New Rating) / Count
            current_total = rated_user.average_rating * rated_user.rating_count
            new_total = current_total - old_rating + rating_value
            rated_user.average_rating = new_total / rated_user.rating_count
            
        else:
            # Create new rating
            rating = rating_model(
                rater_id=data['rater_id'],
                rated_user_id=data['rated_user_id'],
                rating_value=rating_value,
                comment=data.get('comment')
            )
            session.add(rating)
            
            # Update user average
            # New average = ((Old Avg * Count) + New Rating) / (Count + 1)
            current_total = rated_user.average_rating * rated_user.rating_count
            rated_user.rating_count += 1
            rated_user.average_rating = (current_total + rating_value) / rated_user.rating_count

        # If user is a worker, update worker profile rating too
        if rated_user.account_type == 'worker':
            worker_profile = session.query(worker_profile_model).filter_by(user_id=rated_user.id).first()
            if worker_profile:
                # Worker profile rating is integer 0-5 (or maybe 0-50 as per comment in models.py)
                # Comment says: "Average rating (0-5 scale, store as 0-50 for decimals)"
                # Let's store as integer scaled by 10 to keep one decimal place precision
                worker_profile.rating = int(rated_user.average_rating * 10)

        session.commit()
        result = {
            'message': 'rating submitted successfully',
            'new_average': rated_user.average_rating,
            'rating_count': rated_user.rating_count
        }
        session.close()
        
        return jsonify(result), 201

    @app.route('/ratings/user/<int:user_id>', methods=['GET'])
    def get_user_ratings(user_id):
        """Get ratings for a specific user"""
        if not db_available:
            return jsonify({'error': 'database not available'}), 500

        session = session_local()
        
        user = session.query(user_model).filter_by(id=user_id).first()
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404
            
        ratings = session.query(rating_model).filter_by(rated_user_id=user_id).order_by(rating_model.created_at.desc()).all()
        
        result = {
            'user_id': user_id,
            'average_rating': user.average_rating,
            'rating_count': user.rating_count,
            'ratings': [r.to_dict() for r in ratings]
        }
        
        session.close()
        return jsonify(result), 200

    # ========== Legal Endpoints ==========

    @app.route('/legal/tos', methods=['GET'])
    def get_terms_of_service():
        """Get Terms of Service content"""
        try:
            with open(os.path.join('txts', 'legal/TERMS_OF_SERVICE.md'), 'r') as f:
                content = f.read()
            return jsonify({'content': content}), 200
        except FileNotFoundError:
            return jsonify({'error': 'Terms of Service not found'}), 404

    @app.route('/legal/privacy', methods=['GET'])
    def get_privacy_policy():
        """Get Privacy Policy content"""
        try:
            with open(os.path.join('txts', 'legal/PRIVACY_POLICY.md'), 'r') as f:
                content = f.read()
            return jsonify({'content': content}), 200
        except FileNotFoundError:
            return jsonify({'error': 'Privacy Policy not found'}), 404

    @app.route('/listings/<int:listing_id>/boost', methods=['POST'])
    def boost_listing(listing_id):
        """Boost a listing for increased visibility"""
        if not db_available or session_local is None:
            return jsonify({'error': 'database not available'}), 503

        try:
            data = request.get_json()
        except Exception:
            data = None
            
        if not data or 'user_id' not in data:
            return jsonify({'error': 'missing required field: user_id'}), 400
            
        user_id = data['user_id']

        session = session_local()
        listing = session.query(listing_model).filter_by(id=listing_id).first()

        if not listing:
            session.close()
            return jsonify({'error': 'Listing not found'}), 404

        if listing.owner_id != user_id:
            session.close()
            return jsonify({'error': 'Unauthorized'}), 403

        # Check wallet balance
        wallet = session.query(wallet_model).filter_by(user_id=user_id).first()
        if not wallet:
            session.close()
            return jsonify({'error': 'Wallet not found. Please fund your wallet.'}), 400

        BOOST_COST = 5000.0 # Example cost
        BOOST_DURATION_DAYS = 7

        if wallet.balance < BOOST_COST:
            session.close()
            return jsonify({'error': 'Insufficient funds'}), 400

        # Deduct funds
        wallet.balance -= BOOST_COST
        
        # Create transaction record
        transaction = transaction_model(
            wallet_id=wallet.id,
            amount=BOOST_COST,
            transaction_type='payment',
            status='success',
            reference=f'BOOST-LIST-{uuid.uuid4().hex[:12].upper()}',
            description=f'Boost listing: {listing.title}'
        )
        session.add(transaction)

        # Apply boost
        listing.featured = True
        listing.boost_expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=BOOST_DURATION_DAYS)

        session.commit()
        
        expiry_iso = listing.boost_expiry.isoformat()
        new_balance = wallet.balance
        
        session.close()

        return jsonify({
            'message': 'Listing boosted successfully', 
            'boost_expiry': expiry_iso,
            'new_balance': new_balance
        }), 200

    @app.route('/workers/<int:worker_id>/boost', methods=['POST'])
    def boost_worker_profile(worker_id):
        """Boost a worker profile for increased visibility"""
        if not db_available or session_local is None:
            return jsonify({'error': 'database not available'}), 503

        try:
            data = request.get_json()
        except Exception:
            data = None
            
        if not data or 'user_id' not in data:
            return jsonify({'error': 'missing required field: user_id'}), 400
            
        user_id = data['user_id']

        session = session_local()
        worker = session.query(worker_profile_model).filter_by(id=worker_id).first()

        if not worker:
            session.close()
            return jsonify({'error': 'Worker profile not found'}), 404

        if worker.user_id != user_id:
            session.close()
            return jsonify({'error': 'Unauthorized'}), 403

        # Check wallet balance
        wallet = session.query(wallet_model).filter_by(user_id=user_id).first()
        if not wallet:
            session.close()
            return jsonify({'error': 'Wallet not found. Please fund your wallet.'}), 400

        BOOST_COST = 5000.0 # Example cost
        BOOST_DURATION_DAYS = 7

        if wallet.balance < BOOST_COST:
            session.close()
            return jsonify({'error': 'Insufficient funds'}), 400

        # Deduct funds
        wallet.balance -= BOOST_COST
        
        # Create transaction record
        transaction = transaction_model(
            wallet_id=wallet.id,
            amount=BOOST_COST,
            transaction_type='payment',
            status='success',
            reference=f'BOOST-WORKER-{uuid.uuid4().hex[:12].upper()}',
            description=f'Boost worker profile: {worker.specialization}'
        )
        session.add(transaction)

        # Apply boost
        worker.is_boosted = True
        worker.boost_expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=BOOST_DURATION_DAYS)

        session.commit()
        
        expiry_iso = worker.boost_expiry.isoformat()
        new_balance = wallet.balance
        
        session.close()

        return jsonify({
            'message': 'Worker profile boosted successfully', 
            'boost_expiry': expiry_iso,
            'new_balance': new_balance
        }), 200

    @app.route('/auth/request-otp', methods=['POST'])
    @limiter.limit("3 per minute")
    def request_otp():
        """Request an OTP for email verification"""
        if not db_available or session_local is None or user_model is None:
            return jsonify({'error': 'database not available'}), 503

        try:
            data = request.get_json()
        except Exception:
            data = None

        if not data or 'email' not in data:
            return jsonify({'error': 'email is required'}), 400

        session = session_local()
        user = session.query(user_model).filter_by(email=data['email']).first()
        
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404

        if user.email_verified:
            session.close()
            return jsonify({'message': 'Email already verified'}), 200

        # Generate OTP
        # import random
        # otp = f"{random.randint(100000, 999999)}"
        otp = "123456" # Fixed Mock OTP
        expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)

        user.otp_code = otp
        user.otp_expiry = expiry
        session.commit()

        # Send Mock Email
        send_mock_email(
            user.email, 
            "FLB Verification Code", 
            f"Your verification code is: {otp}\nIt expires in 10 minutes."
        )

        session.close()
        return jsonify({'message': 'OTP sent to email'}), 200

    @app.route('/auth/verify-otp', methods=['POST'])
    @limiter.limit("5 per minute")
    def verify_otp():
        """Verify the OTP code"""
        if not db_available or session_local is None or user_model is None:
            return jsonify({'error': 'database not available'}), 503

        try:
            data = request.get_json()
        except Exception:
            data = None

        if not data or 'email' not in data or 'otp' not in data:
            return jsonify({'error': 'email and otp are required'}), 400

        session = session_local()
        user = session.query(user_model).filter_by(email=data['email']).first()
        
        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404

        if user.email_verified:
            session.close()
            return jsonify({'message': 'Email already verified'}), 200

        if not user.otp_code or not user.otp_expiry:
            session.close()
            return jsonify({'error': 'No OTP requested'}), 400

        # Check expiry
        # Ensure timezone awareness
        now = datetime.datetime.now(datetime.timezone.utc)
        if user.otp_expiry.tzinfo is None:
             # If DB returns naive datetime, assume UTC (sqlite often does this)
             user.otp_expiry = user.otp_expiry.replace(tzinfo=datetime.timezone.utc)

        if now > user.otp_expiry:
            session.close()
            return jsonify({'error': 'OTP expired'}), 400

        if user.otp_code != data['otp']:
            session.close()
            return jsonify({'error': 'invalid OTP'}), 400

        # Success
        user.email_verified = True
        user.otp_code = None
        user.otp_expiry = None
        session.commit()
        session.close()

        return jsonify({'message': 'Email verified successfully'}), 200

    @app.route('/jobs')
    def jobs_page():
        return render_template('jobs.html')

    @app.route('/jobs/<int:id>')
    def job_detail_page(id):
        return render_template('job_detail.html')

    @app.route('/jobs/create')
    def job_create_page():
        return render_template('job_create.html')

    @app.route('/jobs/<int:id>/edit')
    def job_edit_page(id):
        return render_template('job_edit.html')

    @app.route('/api/jobs', methods=['POST'])
    def create_job():
        if not db_available or session_local is None or job_model is None:
            return jsonify({'error': 'database not available'}), 503
        
        data = request.get_json()
        if not data or 'user_id' not in data or 'title' not in data or 'description' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
            
        session = session_local()
        try:
            # Check if user exists and is not banned
            user = session.query(user_model).filter_by(id=data['user_id']).first()
            if not user:
                return jsonify({'error': 'user not found'}), 404
            
            if user.is_banned:
                reason = user.ban_reason if user.ban_reason else "No reason provided"
                return jsonify({'error': f'account is banned\nReason: {reason}'}), 403

            new_job = job_model(
                employer_id=data['user_id'],
                title=data['title'],
                description=data['description'],
                requirements=data.get('requirements'),
                location=data.get('location'),
                salary_range=data.get('salary_range')
            )
            session.add(new_job)
            session.commit()
            return jsonify({'message': 'Job posted successfully', 'id': new_job.id}), 201
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/jobs/list', methods=['GET'])
    def get_all_jobs():
        """Get all jobs with optional filtering"""
        if not db_available or session_local is None or job_model is None:
            return jsonify({'error': 'database not available'}), 503
            
        session = session_local()
        try:
            query = session.query(job_model)
            
            # Search query
            search_q = request.args.get('q')
            if search_q:
                search_term = f"%{search_q}%"
                query = query.filter(
                    (job_model.title.ilike(search_term)) | 
                    (job_model.description.ilike(search_term)) |
                    (job_model.location.ilike(search_term))
                )
            
            # Sorting
            sort_by = request.args.get('sort_by', 'recent')
            if sort_by == 'salary_high':
                # This is tricky if salary is a string range. 
                # For now, just sort by ID or created_at as proxy or ignore
                pass 
            elif sort_by == 'recent':
                query = query.order_by(job_model.created_at.desc())
                
            jobs = query.all()
            return jsonify([job.to_dict() for job in jobs])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/jobs/<int:id>', methods=['GET'])
    def get_job_detail(id):
        if not db_available or session_local is None or job_model is None:
            return jsonify({'error': 'database not available'}), 503
            
        session = session_local()
        try:
            job = session.query(job_model).filter_by(id=id).first()
            if not job:
                return jsonify({'error': 'Job not found'}), 404
            return jsonify(job.to_dict())
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/my-jobs', methods=['GET'])
    def get_my_jobs():
        if not db_available or session_local is None or job_model is None:
            return jsonify({'error': 'database not available'}), 503
        
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
            
        session = session_local()
        try:
            jobs = session.query(job_model).filter_by(employer_id=user_id).all()
            return jsonify([job.to_dict() for job in jobs])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/my-contracts', methods=['GET'])
    def get_my_contracts():
        if not db_available or session_local is None or contract_model is None:
            return jsonify({'error': 'database not available'}), 503
        
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
            
        session = session_local()
        try:
            # Get contracts where user is party_a or party_b
            from sqlalchemy import or_
            contracts = session.query(contract_model).filter(
                or_(contract_model.party_a_id == user_id, contract_model.party_b_id == user_id)
            ).all()
            return jsonify([c.to_dict() for c in contracts])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/my-job-history', methods=['GET'])
    def get_my_job_history():
        if not db_available or session_local is None or job_model is None or job_application_model is None:
            return jsonify({'error': 'database not available'}), 503
        
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
            
        session = session_local()
        try:
            # Find applications by this user that are accepted
            applications = session.query(job_application_model).filter_by(
                applicant_id=user_id, 
                status='accepted'
            ).all()
            
            job_ids = [app.job_id for app in applications]
            
            if not job_ids:
                return jsonify([])
                
            jobs = session.query(job_model).filter(job_model.id.in_(job_ids)).all()
            return jsonify([job.to_dict() for job in jobs])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/my-reviews', methods=['GET'])
    def get_my_reviews():
        if not db_available or session_local is None or rating_model is None:
            return jsonify({'error': 'database not available'}), 503
        
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
            
        session = session_local()
        try:
            ratings = session.query(rating_model).filter_by(rated_user_id=user_id).all()
            
            # Enhance with rater name
            results = []
            for r in ratings:
                d = r.to_dict()
                if r.rater:
                    d['rater_name'] = r.rater.full_name
                results.append(d)
                
            return jsonify(results)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        """Update user profile information"""
        if not db_available or session_local is None or user_model is None:
            return jsonify({'error': 'database not available'}), 503

        try:
            data = request.get_json()
        except Exception:
            data = None

        if not data:
            return jsonify({'error': 'invalid json'}), 400

        session = session_local()
        user = session.query(user_model).filter_by(id=user_id).first()

        if not user:
            session.close()
            return jsonify({'error': 'user not found'}), 404

        # Update fields
        updatable_fields = {
            'full_name', 'phone_number', 'bio', 'location', 'profile_picture'
        }

        for field in updatable_fields:
            if field in data:
                setattr(user, field, data[field])

        session.commit()
        session.refresh(user)
        session.close()

        return jsonify(user.to_dict()), 200

    @app.route('/api/workers/list', methods=['GET'])
    def get_all_workers():
        """Get all workers with optional filtering"""
        if not db_available or session_local is None or worker_profile_model is None:
            return jsonify({'error': 'database not available'}), 503
            
        session = session_local()
        try:
            query = session.query(worker_profile_model).join(user_model)
            
            # Search query
            search_q = request.args.get('q')
            if search_q:
                search_term = f"%{search_q}%"
                query = query.filter(
                    (user_model.full_name.ilike(search_term)) | 
                    (worker_profile_model.specialization.ilike(search_term)) |
                    (worker_profile_model.location_state.ilike(search_term)) |
                    (worker_profile_model.location_area.ilike(search_term))
                )
            
            # Sorting
            sort_by = request.args.get('sort_by', 'rating')
            if sort_by == 'rating':
                query = query.order_by(worker_profile_model.rating.desc())
            elif sort_by == 'experience':
                query = query.order_by(worker_profile_model.experience_years.desc())
            elif sort_by == 'rate_low':
                query = query.order_by(worker_profile_model.daily_rate.asc())
            elif sort_by == 'rate_high':
                query = query.order_by(worker_profile_model.daily_rate.desc())
            elif sort_by == 'recommended':
                # Boosted first, then rating
                query = query.order_by(worker_profile_model.is_boosted.desc(), worker_profile_model.rating.desc())
                
            workers = query.all()
            return jsonify([worker.to_dict() for worker in workers])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/worker-dashboard-stats', methods=['GET'])
    def get_worker_dashboard_stats():
        if not db_available or session_local is None:
            return jsonify({'error': 'database not available'}), 503
        
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
            
        session = session_local()
        try:
            # 1. Worker Profile Stats
            worker_profile = session.query(worker_profile_model).filter_by(user_id=user_id).first()
            jobs_completed = worker_profile.total_jobs if worker_profile else 0
            rating = worker_profile.rating if worker_profile else 0.0
            
            # 2. Wallet Balance
            wallet = session.query(wallet_model).filter_by(user_id=user_id).first()
            total_earnings = wallet.balance if wallet else 0.0
            
            # 3. Recent Job Applications
            recent_applications = session.query(job_application_model)\
                .filter_by(applicant_id=user_id)\
                .order_by(job_application_model.created_at.desc())\
                .limit(5)\
                .all()
            
            applications_data = []
            for app in recent_applications:
                job = session.query(job_model).get(app.job_id)
                applications_data.append({
                    'id': app.id,
                    'job_title': job.title if job else 'Unknown Job',
                    'status': app.status,
                    'date': app.created_at.isoformat() if app.created_at else None,
                    'location': job.location if job else ''
                })

            return jsonify({
                'jobsCompleted': jobs_completed,
                'totalEarnings': total_earnings,
                'rating': rating,
                'recentApplications': applications_data
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    # ========== TASK ENDPOINTS ==========

    @app.route('/api/tasks', methods=['GET'])
    def get_tasks():
        if not db_available or session_local is None or task_model is None:
            return jsonify({'error': 'database not available'}), 503
        
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
            
        session = session_local()
        try:
            tasks = session.query(task_model).filter_by(user_id=user_id).order_by(task_model.due_date).all()
            return jsonify([t.to_dict() for t in tasks])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/tasks', methods=['POST'])
    def create_task():
        if not db_available or session_local is None or task_model is None:
            return jsonify({'error': 'database not available'}), 503
        
        data = request.get_json()
        if not data or 'user_id' not in data or 'title' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
            
        session = session_local()
        try:
            due_date = None
            if data.get('due_date'):
                due_date = datetime.datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))

            new_task = task_model(
                user_id=data['user_id'],
                title=data['title'],
                description=data.get('description'),
                due_date=due_date,
                status='pending'
            )
            session.add(new_task)
            session.commit()
            return jsonify(new_task.to_dict()), 201
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/tasks/<int:task_id>', methods=['PUT'])
    def update_task(task_id):
        if not db_available or session_local is None or task_model is None:
            return jsonify({'error': 'database not available'}), 503
        
        data = request.get_json()
        session = session_local()
        try:
            task = session.query(task_model).get(task_id)
            if not task:
                return jsonify({'error': 'Task not found'}), 404
            
            if 'status' in data:
                task.status = data['status']
            if 'title' in data:
                task.title = data['title']
            if 'description' in data:
                task.description = data['description']
            
            session.commit()
            return jsonify(task.to_dict())
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
    def delete_task(task_id):
        if not db_available or session_local is None or task_model is None:
            return jsonify({'error': 'database not available'}), 503
            
        session = session_local()
        try:
            task = session.query(task_model).get(task_id)
            if not task:
                return jsonify({'error': 'Task not found'}), 404
            
            session.delete(task)
            session.commit()
            return jsonify({'message': 'Task deleted'})
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

