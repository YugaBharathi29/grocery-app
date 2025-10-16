"""
Subscription Order Scheduler
-----------------------------
This script automatically processes active subscriptions and creates orders
for customers based on their subscription frequency (daily/weekly).

Usage:
    python scheduler.py

Schedule with Cron (Linux/Mac):
    # Run daily at 6 AM
    0 6 * * * /path/to/python /path/to/project/scheduler.py

    # Run every hour
    0 * * * * /path/to/python /path/to/project/scheduler.py

Schedule with Task Scheduler (Windows):
    Create a scheduled task to run this script daily
"""

import sys
import os
from datetime import datetime
import logging

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Subscription, SubscriptionItem, Order, OrderItem, Product, User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('subscription_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def process_subscriptions():
    """
    Process all active and approved subscriptions that are due for delivery.
    Creates orders automatically and updates inventory.
    """
    with app.app_context():
        now = datetime.utcnow()
        
        # Get all active, approved subscriptions that are due
        due_subscriptions = Subscription.query.filter(
            Subscription.is_active == True,
            Subscription.status == 'approved',
            Subscription.next_delivery <= now
        ).all()
        
        logger.info(f"Found {len(due_subscriptions)} approved subscriptions due for delivery")
        
        # Statistics
        total_processed = 0
        total_failed = 0
        total_skipped = 0
        
        for subscription in due_subscriptions:
            try:
                logger.info(f"Processing subscription #{subscription.id} - {subscription.name}")
                
                # Get subscription items
                items = SubscriptionItem.query.filter_by(subscription_id=subscription.id).all()
                
                if not items:
                    logger.warning(f"Subscription #{subscription.id} has no items, skipping")
                    total_skipped += 1
                    continue
                
                # Get user information
                user = User.query.get(subscription.user_id)
                if not user or not user.is_active:
                    logger.warning(f"User #{subscription.user_id} is not active, skipping subscription #{subscription.id}")
                    total_skipped += 1
                    continue
                
                # Calculate total amount
                total = subscription.get_total_amount()
                
                # Validate stock availability for all items
                stock_issues = []
                for item in items:
                    product = Product.query.get(item.product_id)
                    
                    if not product or not product.is_active:
                        stock_issues.append(f"Product ID {item.product_id} not available")
                        continue
                    
                    if product.stock < item.quantity:
                        stock_issues.append(f"{product.name}: need {item.quantity}, only {product.stock} available")
                
                # If there are stock issues, skip this subscription
                if stock_issues:
                    logger.warning(f"Stock issues for subscription #{subscription.id}: {', '.join(stock_issues)}")
                    total_failed += 1
                    # Optionally: Send notification to admin/customer about stock issues
                    continue
                
                # Create order
                order = Order(
                    user_id=subscription.user_id,
                    total_amount=total,
                    delivery_address=user.address or "Address not provided",
                    phone=user.phone or "Phone not provided",
                    payment_method='cod',  # Default to Cash on Delivery for subscriptions
                    status='Pending'
                )
                
                db.session.add(order)
                db.session.flush()  # Get order ID
                
                logger.info(f"Created order #{order.id} for subscription #{subscription.id}")
                
                # Create order items and update stock
                for item in items:
                    product = Product.query.get(item.product_id)
                    
                    # Create order item
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=item.quantity,
                        price=product.price
                    )
                    db.session.add(order_item)
                    
                    # Update product stock
                    product.stock -= item.quantity
                    logger.info(f"  - Added {item.quantity}x {product.name} to order #{order.id}")
                
                # Update subscription next delivery date
                subscription.calculate_next_delivery()
                logger.info(f"Next delivery for subscription #{subscription.id} scheduled for {subscription.next_delivery}")
                
                # Commit all changes
                db.session.commit()
                total_processed += 1
                
                logger.info(f"Successfully processed subscription #{subscription.id} - Order #{order.id} created")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error processing subscription #{subscription.id}: {str(e)}", exc_info=True)
                total_failed += 1
        
        # Summary
        logger.info("=" * 60)
        logger.info("Subscription Processing Summary")
        logger.info("=" * 60)
        logger.info(f"Total subscriptions found: {len(due_subscriptions)}")
        logger.info(f"Successfully processed: {total_processed}")
        logger.info(f"Failed: {total_failed}")
        logger.info(f"Skipped: {total_skipped}")
        logger.info("=" * 60)
        
        return {
            'total': len(due_subscriptions),
            'processed': total_processed,
            'failed': total_failed,
            'skipped': total_skipped
        }


def check_upcoming_subscriptions():
    """
    Check for subscriptions due in the next 24 hours and log warnings
    for low stock items. This helps admins prepare inventory.
    """
    with app.app_context():
        from datetime import timedelta
        
        tomorrow = datetime.utcnow() + timedelta(days=1)
        
        upcoming = Subscription.query.filter(
            Subscription.is_active == True,
            Subscription.status == 'approved',
            Subscription.next_delivery <= tomorrow
        ).all()
        
        logger.info(f"Found {len(upcoming)} subscriptions due in the next 24 hours")
        
        for subscription in upcoming:
            items = SubscriptionItem.query.filter_by(subscription_id=subscription.id).all()
            
            for item in items:
                product = Product.query.get(item.product_id)
                
                if product and product.stock < item.quantity * 2:  # Warning if stock is less than 2x needed
                    logger.warning(
                        f"Low stock alert: {product.name} has {product.stock} units, "
                        f"subscription #{subscription.id} needs {item.quantity}"
                    )


def get_subscription_statistics():
    """
    Get overall subscription statistics for reporting
    """
    with app.app_context():
        total = Subscription.query.count()
        active = Subscription.query.filter_by(is_active=True, status='approved').count()
        pending = Subscription.query.filter_by(status='pending').count()
        
        logger.info("Subscription Statistics:")
        logger.info(f"  Total: {total}")
        logger.info(f"  Active & Approved: {active}")
        logger.info(f"  Pending Approval: {pending}")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting Subscription Order Processing")
    logger.info("=" * 60)
    
    # Get statistics first
    get_subscription_statistics()
    
    # Check upcoming subscriptions for inventory planning
    check_upcoming_subscriptions()
    
    # Process due subscriptions
    result = process_subscriptions()
    
    logger.info("Subscription processing completed!")
    logger.info("=" * 60)
    
    # Exit with appropriate code
    if result['failed'] > 0:
        sys.exit(1)  # Exit with error code if any failures
    else:
        sys.exit(0)  # Exit successfully
