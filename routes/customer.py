from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import Category, Product, Cart, CartItem, Order, OrderItem, User, Subscription, SubscriptionItem, db
from forms import CheckoutForm, ProfileForm, SubscriptionForm, AddSubscriptionItemForm
from datetime import datetime, timedelta


customer_bp = Blueprint('customer', __name__)


# ==================== SHOP & PRODUCTS ====================


@customer_bp.route('/shop')
def shop():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '')
    
    # Only show active products
    query = Product.query.filter_by(is_active=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(Product.name.contains(search))
    
    products = query.paginate(page=page, per_page=12, error_out=False)
    
    # Only show active categories
    categories = Category.query.filter_by(is_active=True).all()
    
    return render_template('customer/shop.html', 
                         products=products, 
                         categories=categories,
                         current_category=category_id,
                         search=search)


@customer_bp.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    if not product.is_active:
        flash('This product is currently unavailable', 'warning')
        return redirect(url_for('customer.shop'))
    
    related_products = Product.query.filter_by(
        category_id=product.category_id, 
        is_active=True
    ).filter(Product.id != id).limit(4).all()
    
    return render_template('customer/product_detail.html', product=product, related_products=related_products)


# ==================== CART MANAGEMENT ====================


@customer_bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    
    if not product.is_active:
        flash('This product is currently unavailable', 'danger')
        return redirect(url_for('customer.shop'))
    
    quantity = int(request.form.get('quantity', 1))
    
    if quantity > product.stock:
        flash('Not enough stock available', 'danger')
        return redirect(url_for('customer.product_detail', id=product_id))
    
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    
    if cart_item:
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock:
            flash('Not enough stock available', 'danger')
            return redirect(url_for('customer.product_detail', id=product_id))
        cart_item.quantity = new_quantity
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    flash('Product added to cart successfully!', 'success')
    return redirect(url_for('customer.cart'))


@customer_bp.route('/cart')
@login_required
def cart():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    cart_items = []
    total = 0
    
    if cart:
        cart_items = db.session.query(CartItem, Product).join(Product).filter(CartItem.cart_id == cart.id).all()
        total = sum(item.quantity * product.price for item, product in cart_items)
    
    return render_template('customer/cart.html', cart_items=cart_items, total=total)


@customer_bp.route('/update_cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    quantity = int(request.form.get('quantity', 1))
    
    if quantity <= 0:
        db.session.delete(cart_item)
    else:
        if quantity > cart_item.product.stock:
            flash('Not enough stock available', 'danger')
            return redirect(url_for('customer.cart'))
        cart_item.quantity = quantity
    
    db.session.commit()
    return redirect(url_for('customer.cart'))


@customer_bp.route('/remove_from_cart/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart', 'info')
    return redirect(url_for('customer.cart'))


# ==================== CHECKOUT & ORDERS ====================


@customer_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart or not cart.items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('customer.shop'))
    
    cart_items = db.session.query(CartItem, Product).join(Product).filter(CartItem.cart_id == cart.id).all()
    total = sum(item.quantity * product.price for item, product in cart_items)
    
    form = CheckoutForm()
    if form.validate_on_submit():
        # Get payment method from form
        payment_method = request.form.get('payment_method', 'cod')
        
        # Create order with payment method
        order = Order(
            user_id=current_user.id,
            total_amount=total,
            delivery_address=form.delivery_address.data,
            phone=form.phone.data,
            payment_method=payment_method  # Save payment method
        )
        db.session.add(order)
        db.session.commit()
        
        # Create order items and update stock
        for cart_item, product in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=cart_item.quantity,
                price=product.price
            )
            product.stock -= cart_item.quantity
            db.session.add(order_item)
        
        # Clear cart
        for cart_item, _ in cart_items:
            db.session.delete(cart_item)
        
        db.session.commit()
        
        # Show success message based on payment method
        if payment_method == 'cod':
            flash('Order placed successfully! Pay cash on delivery.', 'success')
        elif payment_method == 'upi':
            flash('Order placed successfully! Complete UPI payment to confirm.', 'success')
        elif payment_method == 'card':
            flash('Order placed successfully! Card payment processed.', 'success')
        elif payment_method == 'netbanking':
            flash('Order placed successfully! Net banking payment initiated.', 'success')
        else:
            flash('Order placed successfully!', 'success')
        
        return redirect(url_for('customer.orders'))
    
    # Pre-fill form with user data
    if not form.phone.data:
        form.phone.data = current_user.phone
    if not form.delivery_address.data:
        form.delivery_address.data = current_user.address
    
    return render_template('customer/checkout.html', form=form, cart_items=cart_items, total=total)


@customer_bp.route('/orders')
@login_required
def orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('customer/orders.html', orders=orders)


@customer_bp.route('/order/<int:id>')
@login_required
def order_detail(id):
    order = Order.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    order_items = db.session.query(OrderItem, Product).join(Product).filter(OrderItem.order_id == order.id).all()
    return render_template('customer/order_detail.html', order=order, order_items=order_items)


# ==================== PROFILE MANAGEMENT ====================


@customer_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page - view and edit profile information"""
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Check if username or email already exists (for other users)
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).filter(User.id != current_user.id).first()
        
        if existing_user:
            if existing_user.username == form.username.data:
                flash('Username already taken by another user.', 'danger')
            else:
                flash('Email already registered to another user.', 'danger')
            return redirect(url_for('customer.profile'))
        
        # Update basic info
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        
        # Update password if provided
        if form.current_password.data and form.new_password.data:
            if current_user.check_password(form.current_password.data):
                current_user.set_password(form.new_password.data)
                flash('Password updated successfully!', 'success')
            else:
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('customer.profile'))
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('customer.profile'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('customer.profile'))
    
    # Get user statistics
    total_orders = Order.query.filter_by(user_id=current_user.id).count()
    completed_orders = Order.query.filter_by(user_id=current_user.id, status='Delivered').count()
    
    # Calculate total spent (only from delivered orders)
    total_spent = db.session.query(db.func.sum(Order.total_amount)).filter_by(
        user_id=current_user.id, 
        status='Delivered'
    ).scalar() or 0.0
    
    return render_template('customer/profile.html', 
                          form=form,
                          total_orders=total_orders,
                          completed_orders=completed_orders,
                          total_spent=total_spent)


# ==================== SUBSCRIPTION MANAGEMENT ====================


@customer_bp.route('/subscriptions')
@login_required
def subscriptions():
    """View all user subscriptions"""
    subscriptions = Subscription.query.filter_by(user_id=current_user.id).order_by(Subscription.created_at.desc()).all()
    return render_template('customer/subscriptions.html', subscriptions=subscriptions)


@customer_bp.route('/create_subscription', methods=['GET', 'POST'])
@login_required
def create_subscription():
    """Create a new subscription"""
    form = SubscriptionForm()
    
    if form.validate_on_submit():
        subscription = Subscription(
            user_id=current_user.id,
            name=form.name.data,
            frequency=form.frequency.data,
            delivery_time=form.delivery_time.data
        )
        subscription.calculate_next_delivery()
        
        db.session.add(subscription)
        db.session.commit()
        
        flash('Subscription created! Now add products to it.', 'success')
        return redirect(url_for('customer.edit_subscription', id=subscription.id))
    
    return render_template('customer/create_subscription.html', form=form)


@customer_bp.route('/subscription/<int:id>')
@login_required
def subscription_detail(id):
    """View subscription details"""
    subscription = Subscription.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    items = db.session.query(SubscriptionItem, Product).join(Product).filter(
        SubscriptionItem.subscription_id == subscription.id
    ).all()
    return render_template('customer/subscription_detail.html', subscription=subscription, items=items)


@customer_bp.route('/edit_subscription/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_subscription(id):
    """Add/remove products from subscription"""
    subscription = Subscription.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = AddSubscriptionItemForm()
    
    # Get active products for dropdown
    form.product_id.choices = [(p.id, f"{p.name} - ₹{p.price}") for p in Product.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        # Check if product already in subscription
        existing = SubscriptionItem.query.filter_by(
            subscription_id=subscription.id,
            product_id=form.product_id.data
        ).first()
        
        if existing:
            existing.quantity += form.quantity.data
            flash('Product quantity updated in subscription!', 'success')
        else:
            item = SubscriptionItem(
                subscription_id=subscription.id,
                product_id=form.product_id.data,
                quantity=form.quantity.data
            )
            db.session.add(item)
            flash('Product added to subscription!', 'success')
        
        db.session.commit()
        return redirect(url_for('customer.edit_subscription', id=id))
    
    # Get current items
    items = db.session.query(SubscriptionItem, Product).join(Product).filter(
        SubscriptionItem.subscription_id == subscription.id
    ).all()
    
    return render_template('customer/edit_subscription.html', 
                          subscription=subscription, 
                          items=items, 
                          form=form)


@customer_bp.route('/update_subscription_item/<int:id>', methods=['POST'])
@login_required
def update_subscription_item(id):
    """Update subscription item quantity"""
    item = SubscriptionItem.query.get_or_404(id)
    subscription = Subscription.query.filter_by(id=item.subscription_id, user_id=current_user.id).first_or_404()
    
    quantity = int(request.form.get('quantity', 1))
    
    if quantity <= 0:
        db.session.delete(item)
        flash('Product removed from subscription', 'info')
    else:
        item.quantity = quantity
        flash('Quantity updated successfully!', 'success')
    
    db.session.commit()
    return redirect(url_for('customer.edit_subscription', id=subscription.id))


@customer_bp.route('/remove_subscription_item/<int:id>')
@login_required
def remove_subscription_item(id):
    """Remove product from subscription"""
    item = SubscriptionItem.query.get_or_404(id)
    subscription_id = item.subscription_id
    
    # Verify ownership
    subscription = Subscription.query.filter_by(id=subscription_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(item)
    db.session.commit()
    
    flash('Product removed from subscription', 'info')
    return redirect(url_for('customer.edit_subscription', id=subscription_id))


@customer_bp.route('/toggle_subscription/<int:id>')
@login_required
def toggle_subscription(id):
    """Pause/Resume subscription"""
    subscription = Subscription.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    subscription.is_active = not subscription.is_active
    db.session.commit()
    
    status = 'activated' if subscription.is_active else 'paused'
    flash(f'Subscription {status} successfully!', 'success')
    
    return redirect(url_for('customer.subscriptions'))


@customer_bp.route('/delete_subscription/<int:id>')
@login_required
def delete_subscription(id):
    """Delete subscription"""
    subscription = Subscription.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    db.session.delete(subscription)
    db.session.commit()
    
    flash('Subscription deleted successfully!', 'success')
    return redirect(url_for('customer.subscriptions'))
