from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager
from flask_migrate import Migrate
from models import db, User, Category, Product
from config import Config
import os
from datetime import datetime
import pytz


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create upload folders
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'categories'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'products'), exist_ok=True)
    
    # ========== TEMPLATE FILTERS FOR IST TIMEZONE ==========
    
    @app.template_filter('to_ist')
    def to_ist_filter(utc_time):
        """
        Convert UTC datetime to IST (Indian Standard Time)
        Usage in templates: {{ order.created_at | to_ist }}
        """
        if utc_time is None:
            return None
        
        # Define timezones
        utc = pytz.UTC
        ist = pytz.timezone('Asia/Kolkata')
        
        # If the datetime is naive (no timezone info), assume it's UTC
        if utc_time.tzinfo is None:
            utc_time = utc.localize(utc_time)
        
        # Convert to IST
        ist_time = utc_time.astimezone(ist)
        
        return ist_time
    
    @app.template_filter('format_datetime')
    def format_datetime_filter(dt, format='%B %d, %Y at %I:%M %p'):
        """
        Format datetime with IST conversion
        Usage: {{ order.created_at | format_datetime }}
        Custom format: {{ order.created_at | format_datetime('%b %d, %Y') }}
        """
        if dt is None:
            return ''
        
        # Convert to IST first
        ist_dt = to_ist_filter(dt)
        
        # Format the datetime
        return ist_dt.strftime(format)
    
    @app.template_filter('format_date')
    def format_date_filter(dt):
        """
        Format date only (no time)
        Usage: {{ order.created_at | format_date }}
        """
        return format_datetime_filter(dt, '%B %d, %Y')
    
    @app.template_filter('format_time')
    def format_time_filter(dt):
        """
        Format time only (no date)
        Usage: {{ order.created_at | format_time }}
        """
        return format_datetime_filter(dt, '%I:%M %p')
    
    # ========== REGISTER BLUEPRINTS ==========
    
    from routes.auth import auth_bp
    from routes.customer import customer_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # ========== ROUTES ==========
    
    @app.route('/')
    def index():
        try:
            # Only show active categories and products
            categories = Category.query.filter_by(is_active=True).all()
        except Exception as e:
            print(f'Error querying Category with is_active filter: {type(e).__name__}: {e}')
            # Fallback to all categories if error
            categories = Category.query.all()
        
        try:
            featured_products = Product.query.filter_by(is_active=True).limit(8).all()
        except Exception as e:
            print(f'Error querying Product with is_active filter: {type(e).__name__}: {e}')
            # Fallback to all products if error
            featured_products = Product.query.limit(8).all()
        
        return render_template('index.html', categories=categories, featured_products=featured_products)
    
    @app.route('/shop')
    def shop():
        return redirect(url_for('customer.shop'))
    
    return app


# Create a global app instance for Gunicorn
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)