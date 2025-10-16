# Grocery Store Web Application

A full-featured grocery store web application built with Python Flask, Bootstrap 5, Font Awesome, and SQLite.

## Features

### Customer Features
- 🛒 Browse products by category
- 🔍 Search products
- 🛍️ Add products to shopping cart
- 📱 Responsive design for mobile and desktop
- 👤 User registration and authentication
- 📦 Order management and history
- 💳 Secure checkout process

### Admin Features
- 📊 Admin dashboard with statistics
- 📂 Category management (CRUD operations)
- 📦 Product management (CRUD operations)
- 🛒 Order management and status updates
- 👥 User management
- 📸 Image upload for categories and products

## Technology Stack

- **Backend**: Python Flask 3.0.0
- **Database**: SQLite with Flask-SQLAlchemy 3.1.1
- **Authentication**: Flask-Login 0.6.3
- **Forms**: Flask-WTF 1.2.1 with WTForms validation
- **Frontend**: Bootstrap 5.3.0, Font Awesome 6.4.0
- **File Uploads**: Pillow 10.1.0 for image processing

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation Steps

1. **Clone or extract the project**
   ```bash
   cd grocery-app
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python init_db.py
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   Open your browser and go to: `http://localhost:5000`

## Demo Credentials

### Admin Account
- **Username**: admin
- **Password**: admin123

### Customer Account
- **Username**: testuser
- **Password**: user123

## Project Structure

```
grocery-app/
├── app.py                 # Main application file
├── config.py             # Configuration settings
├── models.py             # Database models
├── forms.py              # WTForms form classes
├── init_db.py            # Database initialization script
├── requirements.txt      # Python dependencies
├── routes/               # Route blueprints
│   ├── __init__.py
│   ├── auth.py          # Authentication routes
│   ├── customer.py      # Customer routes
│   └── admin.py         # Admin routes
├── templates/            # Jinja2 templates
│   ├── base.html        # Base template
│   ├── index.html       # Home page
│   ├── auth/            # Authentication templates
│   ├── customer/        # Customer templates
│   └── admin/           # Admin templates
├── static/              # Static files
│   ├── css/
│   │   └── style.css    # Custom CSS
│   ├── js/
│   │   └── main.js      # Custom JavaScript
│   └── uploads/         # File uploads
│       ├── categories/  # Category images
│       └── products/    # Product images
└── README.md            # This file
```

## Database Schema

### Users
- User authentication and profile information
- Admin flag for role-based access

### Categories
- Product categorization
- Image support for categories

### Products
- Complete product information
- Stock management
- Category association
- Image support

### Orders & Cart
- Shopping cart functionality
- Order management
- Order items tracking

## Features in Detail

### Authentication System
- Secure user registration and login
- Password hashing with Werkzeug
- Session management with Flask-Login
- Role-based access control (Admin/Customer)

### Product Management
- CRUD operations for products and categories
- Image upload and storage
- Stock management
- Category-based organization

### Shopping Cart
- Add/remove products
- Quantity management
- Real-time total calculation
- Persistent cart per user session

### Order Management
- Secure checkout process
- Order status tracking
- Order history for customers
- Admin order management with status updates

### Responsive Design
- Mobile-first approach with Bootstrap 5
- Touch-friendly interface
- Responsive navigation
- Optimized for all screen sizes

## Security Features

- Password hashing
- CSRF protection with Flask-WTF
- File upload validation
- SQL injection prevention with SQLAlchemy ORM
- XSS protection with Jinja2 auto-escaping

## Customization

### Adding New Features
1. Create new routes in appropriate blueprint files
2. Add corresponding templates
3. Update models if database changes are needed
4. Add forms for user input

### Styling Customization
- Modify `static/css/style.css` for custom styles
- Bootstrap variables can be overridden
- Font Awesome icons can be customized

### Database Customization
- Modify `models.py` to add new fields
- Run `init_db.py` to recreate database
- Update forms and templates accordingly

## Troubleshooting

### Common Issues

1. **Database not found error**
   - Run `python init_db.py` to initialize the database

2. **Import errors**
   - Ensure virtual environment is activated
   - Install all requirements: `pip install -r requirements.txt`

3. **File upload errors**
   - Check that upload directories exist
   - Verify file permissions

4. **Template not found**
   - Ensure all template files are in correct directories
   - Check template inheritance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For support and questions:
- Check the troubleshooting section
- Review the code comments
- Create an issue in the project repository

---

**Note**: This is a demo application for educational purposes. For production use, additional security measures and optimizations should be implemented.
