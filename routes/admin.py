from flask import Blueprint, render_template, redirect, url_for, request, flash, make_response
from flask_login import login_required, current_user
from functools import wraps
from models import User, Category, Product, Order, OrderItem, Subscription, SubscriptionItem, db
from forms import CategoryForm, ProductForm, BulkUploadForm
from werkzeug.utils import secure_filename
import os
import pandas as pd
import io


admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # User stats
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    
    # Category stats
    total_categories = Category.query.count()
    active_categories = Category.query.filter_by(is_active=True).count()
    
    # Product stats
    total_products = Product.query.count()
    active_products = Product.query.filter_by(is_active=True).count()
    
    # Order stats
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='Pending').count()
    
    # Calculate total sales from all delivered orders
    delivered_orders = Order.query.filter_by(status='Delivered').all()
    total_sales = sum(order.total_amount for order in delivered_orders)
    
    # Subscription stats (NEW!)
    subscription_count = Subscription.query.filter_by(is_active=True, status='approved').count()
    pending_subscriptions = Subscription.query.filter_by(status='pending').count()
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Get recent subscriptions (NEW!)
    recent_subscriptions = Subscription.query.order_by(Subscription.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         total_categories=total_categories,
                         active_categories=active_categories,
                         total_products=total_products,
                         active_products=active_products,
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         total_sales=total_sales,
                         subscription_count=subscription_count,
                         pending_subscriptions=pending_subscriptions,
                         recent_orders=recent_orders,
                         recent_subscriptions=recent_subscriptions)


# ==================== CATEGORY MANAGEMENT ====================

@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)


@admin_bp.route('/add_category', methods=['GET', 'POST'])
@login_required
@admin_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        # Priority: URL > Upload
        image_value = None
        
        if form.image_url.data:
            image_value = form.image_url.data
        elif form.image.data and hasattr(form.image.data, 'filename'):
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join('static/uploads/categories', filename))
            image_value = filename
        
        category = Category(
            name=form.name.data,
            description=form.description.data,
            image=image_value,
            is_active=form.is_active.data
        )
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/add_category.html', form=form)


@admin_bp.route('/edit_category/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        category.is_active = form.is_active.data
        
        # Handle image - Priority: URL > Upload > Keep existing
        if form.image_url.data:
            category.image = form.image_url.data
        elif form.image.data and hasattr(form.image.data, 'filename'):
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join('static/uploads/categories', filename))
            category.image = filename
        
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/edit_category.html', form=form, category=category)


@admin_bp.route('/delete_category/<int:id>')
@login_required
@admin_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    if category.products.count() > 0:
        flash('Cannot delete category with products. Please delete products first.', 'danger')
        return redirect(url_for('admin.categories'))
    
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin.categories'))


# ==================== PRODUCT MANAGEMENT ====================

@admin_bp.route('/products')
@login_required
@admin_required
def products():
    page = request.args.get('page', 1, type=int)
    products = Product.query.paginate(page=page, per_page=10, error_out=False)
    return render_template('admin/products.html', products=products)


@admin_bp.route('/add_product', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        # Priority: URL > Upload
        image_value = None
        
        if form.image_url.data:
            image_value = form.image_url.data
        elif form.image.data and hasattr(form.image.data, 'filename'):
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join('static/uploads/products', filename))
            image_value = filename
        
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            stock=form.stock.data,
            category_id=form.category_id.data,
            image=image_value,
            is_active=form.is_active.data
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin.products'))
    
    return render_template('admin/add_product.html', form=form)


@admin_bp.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.stock = form.stock.data
        product.category_id = form.category_id.data
        product.is_active = form.is_active.data
        
        # Handle image - Priority: URL > Upload > Keep existing
        if form.image_url.data:
            product.image = form.image_url.data
        elif form.image.data and hasattr(form.image.data, 'filename'):
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join('static/uploads/products', filename))
            product.image = filename
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin.products'))
    
    return render_template('admin/edit_product.html', form=form, product=product)


@admin_bp.route('/delete_product/<int:id>')
@login_required
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin.products'))


# ==================== BULK UPLOAD FEATURE ====================

@admin_bp.route('/bulk-upload-products', methods=['GET', 'POST'])
@login_required
@admin_required
def bulk_upload_products():
    """Bulk upload products from CSV/Excel file"""
    form = BulkUploadForm()
    
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        
        try:
            # Read CSV or Excel file
            if filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif filename.endswith('.xlsx') or filename.endswith('.xls'):
                df = pd.read_excel(file)
            else:
                flash('Invalid file format. Please upload CSV or Excel file.', 'danger')
                return redirect(url_for('admin.bulk_upload_products'))
            
            # Expected columns
            required_columns = ['name', 'price', 'category_id']
            
            # Check if required columns exist
            if not all(col in df.columns for col in required_columns):
                flash(f'CSV must have these columns: {", ".join(required_columns)}', 'danger')
                return redirect(url_for('admin.bulk_upload_products'))
            
            # Add products
            success_count = 0
            error_count = 0
            error_messages = []
            
            for index, row in df.iterrows():
                try:
                    # Validate category exists
                    category = Category.query.get(int(row['category_id']))
                    if not category:
                        error_messages.append(f"Row {index + 2}: Category ID {row['category_id']} does not exist")
                        error_count += 1
                        continue
                    
                    # Create product
                    product = Product(
                        name=str(row['name']).strip(),
                        description=str(row.get('description', '')).strip() if pd.notna(row.get('description')) else '',
                        price=float(row['price']),
                        stock=int(row.get('stock', 0)) if pd.notna(row.get('stock')) else 0,
                        category_id=int(row['category_id']),
                        image=str(row.get('image', '')).strip() if pd.notna(row.get('image')) else '',
                        is_active=True
                    )
                    
                    db.session.add(product)
                    success_count += 1
                    
                except ValueError as e:
                    error_messages.append(f"Row {index + 2}: Invalid data format - {str(e)}")
                    error_count += 1
                except Exception as e:
                    error_messages.append(f"Row {index + 2}: {str(e)}")
                    error_count += 1
                    continue
            
            # Commit all products
            if success_count > 0:
                db.session.commit()
                flash(f'✅ Successfully uploaded {success_count} products!', 'success')
            
            if error_count > 0:
                flash(f'⚠️ {error_count} products failed to upload.', 'warning')
                for msg in error_messages[:5]:
                    flash(msg, 'danger')
            
            return redirect(url_for('admin.products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing file: {str(e)}', 'danger')
            return redirect(url_for('admin.bulk_upload_products'))
    
    return render_template('admin/bulk_upload.html', form=form)


@admin_bp.route('/download-sample-csv')
@login_required
@admin_required
def download_sample_csv():
    """Download sample CSV template for bulk upload"""
    categories = Category.query.limit(3).all()
    category_examples = [(c.id, c.name) for c in categories] if categories else [(1, 'Example Category')]
    
    csv_data = f"""name,description,price,stock,category_id,image
Fresh Milk,Organic cow milk 1 liter,55,100,{category_examples[0][0]},https://images.unsplash.com/photo-1550583724-b2692b85b150
Whole Wheat Bread,Fresh baked whole wheat bread 400g,45,80,{category_examples[0][0]},https://images.unsplash.com/photo-1509440159596-0249088772ff
Basmati Rice,Premium quality basmati rice 5kg,350,50,{category_examples[0][0]},https://images.unsplash.com/photo-1586201375761-83865001e31c"""
    
    output = io.StringIO()
    output.write(csv_data)
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=sample_products.csv'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    
    return response


# ==================== ORDER MANAGEMENT ====================

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    page = request.args.get('page', 1, type=int)
    orders = Order.query.order_by(Order.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('admin/orders.html', orders=orders)


@admin_bp.route('/order/<int:id>')
@login_required
@admin_required
def order_detail(id):
    order = Order.query.get_or_404(id)
    order_items = db.session.query(OrderItem, Product).join(Product).filter(OrderItem.order_id == order.id).all()
    return render_template('admin/order_detail.html', order=order, order_items=order_items)


@admin_bp.route('/update_order_status/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_order_status(id):
    order = Order.query.get_or_404(id)
    status = request.form.get('status')
    order.status = status
    db.session.commit()
    flash('Order status updated successfully!', 'success')
    return redirect(url_for('admin.order_detail', id=id))


@admin_bp.route('/print_order/<int:id>')
@login_required
@admin_required
def print_order(id):
    order = Order.query.get_or_404(id)
    order_items = db.session.query(OrderItem, Product).join(Product).filter(OrderItem.order_id == order.id).all()
    return render_template('admin/print_order.html', order=order, order_items=order_items)


# ==================== USER MANAGEMENT ====================

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.order_by(User.is_admin.desc(), User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/toggle_user/<int:id>')
@login_required
@admin_required
def toggle_user(id):
    user = User.query.get_or_404(id)
    if user.is_admin:
        flash('Cannot modify admin users.', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {status} successfully!', 'success')
    return redirect(url_for('admin.users'))


# ==================== SUBSCRIPTION MANAGEMENT ====================

@admin_bp.route('/subscriptions')
@login_required
@admin_required
def subscriptions():
    """View all customer subscriptions"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    # Base query
    query = Subscription.query
    
    # Apply status filter
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    # Paginate
    subscriptions = query.order_by(Subscription.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get statistics
    total_subscriptions = Subscription.query.count()
    pending_count = Subscription.query.filter_by(status='pending').count()
    approved_count = Subscription.query.filter_by(status='approved').count()
    rejected_count = Subscription.query.filter_by(status='rejected').count()
    active_count = Subscription.query.filter_by(is_active=True, status='approved').count()
    
    return render_template('admin/subscriptions.html',
                          subscriptions=subscriptions,
                          status_filter=status_filter,
                          total_subscriptions=total_subscriptions,
                          pending_count=pending_count,
                          approved_count=approved_count,
                          rejected_count=rejected_count,
                          active_count=active_count)


@admin_bp.route('/subscription/<int:id>')
@login_required
@admin_required
def subscription_detail(id):
    """View subscription details"""
    subscription = Subscription.query.get_or_404(id)
    items = db.session.query(SubscriptionItem, Product).join(Product).filter(
        SubscriptionItem.subscription_id == subscription.id
    ).all()
    
    return render_template('admin/subscription_detail.html', 
                          subscription=subscription, 
                          items=items)


@admin_bp.route('/subscription/<int:id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_subscription(id):
    """Approve a subscription"""
    subscription = Subscription.query.get_or_404(id)
    admin_notes = request.form.get('admin_notes', '')
    
    subscription.status = 'approved'
    subscription.is_active = True
    subscription.admin_notes = admin_notes
    
    db.session.commit()
    
    flash(f'Subscription "{subscription.name}" has been approved!', 'success')
    return redirect(url_for('admin.subscription_detail', id=id))


@admin_bp.route('/subscription/<int:id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_subscription(id):
    """Reject a subscription"""
    subscription = Subscription.query.get_or_404(id)
    admin_notes = request.form.get('admin_notes', '')
    
    subscription.status = 'rejected'
    subscription.is_active = False
    subscription.admin_notes = admin_notes
    
    db.session.commit()
    
    flash(f'Subscription "{subscription.name}" has been rejected.', 'warning')
    return redirect(url_for('admin.subscription_detail', id=id))


@admin_bp.route('/subscription/<int:id>/toggle')
@login_required
@admin_required
def toggle_subscription_status(id):
    """Toggle subscription active status"""
    subscription = Subscription.query.get_or_404(id)
    
    if subscription.status != 'approved':
        flash('Only approved subscriptions can be toggled.', 'warning')
        return redirect(url_for('admin.subscription_detail', id=id))
    
    subscription.is_active = not subscription.is_active
    db.session.commit()
    
    status = 'activated' if subscription.is_active else 'paused'
    flash(f'Subscription {status} successfully!', 'success')
    
    return redirect(url_for('admin.subscription_detail', id=id))


@admin_bp.route('/subscription/<int:id>/delete')
@login_required
@admin_required
def delete_subscription(id):
    """Delete a subscription"""
    subscription = Subscription.query.get_or_404(id)
    
    db.session.delete(subscription)
    db.session.commit()
    
    flash('Subscription deleted successfully!', 'success')
    return redirect(url_for('admin.subscriptions'))
