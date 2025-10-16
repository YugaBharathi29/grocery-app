from app import create_app
from models import db, User, Category, Product
from sqlalchemy import text, inspect


app = create_app()


with app.app_context():
    # Create tables if they don't exist (won't drop existing data)
    print("📝 Ensuring database tables exist...")
    db.create_all()
    
    # ========== FIX SUBSCRIPTION TABLE (Add missing columns) ==========
    print("\n🔧 Checking subscription table schema...")
    try:
        inspector = inspect(db.engine)
        subscription_columns = [col['name'] for col in inspector.get_columns('subscription')]
        
        # Check if 'status' column exists
        if 'status' not in subscription_columns:
            db.session.execute(text("ALTER TABLE subscription ADD COLUMN status VARCHAR(20) DEFAULT 'pending'"))
            print("✅ Added 'status' column to subscription table")
        else:
            print("ℹ️  'status' column already exists")
        
        # Check if 'admin_notes' column exists
        if 'admin_notes' not in subscription_columns:
            db.session.execute(text("ALTER TABLE subscription ADD COLUMN admin_notes TEXT"))
            print("✅ Added 'admin_notes' column to subscription table")
        else:
            print("ℹ️  'admin_notes' column already exists")
        
        # Update existing subscriptions to 'approved' status
        db.session.execute(text("UPDATE subscription SET status = 'approved' WHERE status IS NULL OR status = ''"))
        db.session.commit()
        print("✅ Updated existing subscriptions")
        
    except Exception as e:
        print(f"⚠️  Note: {e}")
        db.session.rollback()
    
    # ========== CREATE USERS (only if they don't exist) ==========
    print("\n👥 Checking users...")
    
    # Check if admin exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@grocery.com',
            is_admin=True,
            is_active=True,
            phone='1234567890',
            address='Admin Office, City'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("✅ Admin user created")
    else:
        print("ℹ️  Admin user already exists")
    
    # Check if test user exists
    user = User.query.filter_by(username='testuser').first()
    if not user:
        user = User(
            username='testuser',
            email='user@grocery.com',
            is_admin=False,
            is_active=True,
            phone='9876543210',
            address='123 Main St, City'
        )
        user.set_password('user123')
        db.session.add(user)
        print("✅ Test user created")
    else:
        print("ℹ️  Test user already exists")
    
    db.session.commit()
    
    # ========== CREATE CATEGORIES WITH IMAGES (only if they don't exist) ==========
    print("\n🏷️  Checking categories...")
    
    categories_data = [
        {
            'name': 'Fruits & Vegetables',
            'description': 'Fresh organic fruits and vegetables delivered daily',
            'image': 'https://images.unsplash.com/photo-1610348725531-843dff563e2c?w=500&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Dairy Products',
            'description': 'Farm fresh milk, cheese, butter and dairy products',
            'image': 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=500&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Bakery',
            'description': 'Fresh bread, cakes, pastries and baked goods',
            'image': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Beverages',
            'description': 'Refreshing drinks, juices, tea and coffee',
            'image': 'https://images.unsplash.com/photo-1544145945-f90425340c7e?w=500&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Snacks',
            'description': 'Delicious chips, cookies, nuts and snacks',
            'image': 'https://images.unsplash.com/photo-1599490659213-e2b9527bd087?w=500&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Frozen Foods',
            'description': 'Frozen vegetables, meals and ice cream',
            'image': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=500&h=400&fit=crop',
            'is_active': True
        }
    ]
    
    categories_added = 0
    for cat_data in categories_data:
        existing_cat = Category.query.filter_by(name=cat_data['name']).first()
        if not existing_cat:
            category = Category(**cat_data)
            db.session.add(category)
            categories_added += 1
    
    db.session.commit()
    
    if categories_added > 0:
        print(f"✅ {categories_added} new categories created")
    else:
        print("ℹ️  All categories already exist")
    
    # ========== CREATE PRODUCTS WITH IMAGES (only if they don't exist) ==========
    print("\n🛒 Checking products...")
    
    products_data = [
        # Fruits & Vegetables (Category ID: 1)
        {
            'name': 'Red Apples',
            'description': 'Crisp and sweet red apples, perfect for snacking',
            'price': 120.0,
            'stock': 100,
            'category_id': 1,
            'image': 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Fresh Bananas',
            'description': 'Ripe yellow bananas rich in potassium',
            'price': 50.0,
            'stock': 150,
            'category_id': 1,
            'image': 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Red Onions',
            'description': 'Fresh red onions for all your cooking needs',
            'price': 30.0,
            'stock': 200,
            'category_id': 1,
            'image': 'https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=400&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Fresh Carrots',
            'description': 'Crunchy orange carrots packed with vitamins',
            'price': 35.0,
            'stock': 120,
            'category_id': 1,
            'image': 'https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=400&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Green Spinach',
            'description': 'Fresh leafy spinach rich in iron',
            'price': 25.0,
            'stock': 90,
            'category_id': 1,
            'image': 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400&h=400&fit=crop',
            'is_active': True
        },
        
        # Dairy Products (Category ID: 2)
        {
            'name': 'Full Cream Milk',
            'description': 'Fresh full cream milk 1L pack',
            'price': 60.0,
            'stock': 200,
            'category_id': 2,
            'image': 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Cheddar Cheese',
            'description': 'Premium cheddar cheese 200g block',
            'price': 180.0,
            'stock': 50,
            'category_id': 2,
            'image': 'https://images.unsplash.com/photo-1552767059-ce182ead6c1b?w=400&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Salted Butter',
            'description': 'Creamy salted butter 100g pack',
            'price': 45.0,
            'stock': 75,
            'category_id': 2,
            'image': 'https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=400&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Greek Yogurt',
            'description': 'Thick and creamy Greek yogurt 500g',
            'price': 120.0,
            'stock': 60,
            'category_id': 2,
            'image': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400&h=400&fit=crop',
            'is_active': True
        },
        
        # Bakery (Category ID: 3)
        {
            'name': 'Whole Wheat Bread',
            'description': 'Fresh baked whole wheat bread loaf',
            'price': 35.0,
            'stock': 120,
            'category_id': 3,
            'image': 'https://images.unsplash.com/photo-1549931319-a545dcf3bc73?w=400&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Chocolate Cake',
            'description': 'Rich chocolate cake perfect for celebrations',
            'price': 400.0,
            'stock': 30,
            'category_id': 3,
            'image': 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Chocolate Cookies',
            'description': 'Crunchy chocolate chip cookies pack',
            'price': 80.0,
            'stock': 60,
            'category_id': 3,
            'image': 'https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=400&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Croissants',
            'description': 'Buttery flaky croissants - pack of 4',
            'price': 150.0,
            'stock': 40,
            'category_id': 3,
            'image': 'https://images.unsplash.com/photo-1555507036-ab794f4d8b97?w=400&h=400&fit=crop',
            'is_active': True
        },
        
        # Beverages (Category ID: 4)
        {
            'name': 'Orange Juice',
            'description': 'Fresh orange juice 1L bottle',
            'price': 100.0,
            'stock': 75,
            'category_id': 4,
            'image': 'https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?w=400&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Cola Drink',
            'description': 'Refreshing cola soft drink 500ml',
            'price': 40.0,
            'stock': 200,
            'category_id': 4,
            'image': 'https://images.unsplash.com/photo-1581006852262-e4307cf6283a?w=400&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Mineral Water',
            'description': 'Pure mineral water 1L bottle',
            'price': 20.0,
            'stock': 300,
            'category_id': 4,
            'image': 'https://images.unsplash.com/photo-1548839140-29a749e1cf4d?w=400&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Green Tea',
            'description': 'Premium green tea bags - pack of 25',
            'price': 80.0,
            'stock': 85,
            'category_id': 4,
            'image': 'https://images.unsplash.com/photo-1564890369478-c89ca6d9cde9?w=400&h=400&fit=crop',
            'is_active': True
        },
        
        # Snacks (Category ID: 5)
        {
            'name': 'Potato Chips',
            'description': 'Crispy potato chips 100g pack',
            'price': 20.0,
            'stock': 150,
            'category_id': 5,
            'image': 'https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=400&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Mixed Nuts',
            'description': 'Premium mixed nuts 250g pack',
            'price': 200.0,
            'stock': 70,
            'category_id': 5,
            'image': 'https://images.unsplash.com/photo-1599599810769-bcde5a160d32?w=400&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Cream Biscuits',
            'description': 'Sweet cream biscuits family pack',
            'price': 25.0,
            'stock': 100,
            'category_id': 5,
            'image': 'https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=400&h=400&fit=crop',
            'is_active': True
        },
        
        # Frozen Foods (Category ID: 6)
        {
            'name': 'Frozen Peas',
            'description': 'Frozen green peas 500g pack',
            'price': 60.0,
            'stock': 80,
            'category_id': 6,
            'image': 'https://images.unsplash.com/photo-1587735243615-c03f25aaff15?w=400&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Vanilla Ice Cream',
            'description': 'Creamy vanilla ice cream 1L tub',
            'price': 120.0,
            'stock': 45,
            'category_id': 6,
            'image': 'https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=400&h=400&fit=crop',
            'is_active': True
        },
        {
            'name': 'Frozen Pizza',
            'description': 'Delicious frozen margherita pizza',
            'price': 250.0,
            'stock': 35,
            'category_id': 6,
            'image': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&h=400&fit=crop',
            'is_active': True
        }
    ]
    
    products_added = 0
    for prod_data in products_data:
        existing_prod = Product.query.filter_by(name=prod_data['name']).first()
        if not existing_prod:
            product = Product(**prod_data)
            db.session.add(product)
            products_added += 1
    
    db.session.commit()
    
    if products_added > 0:
        print(f"✅ {products_added} new products created")
    else:
        print("ℹ️  All sample products already exist")
    
    print("\n🎉 Database initialization completed!")
    print("=" * 60)
    print("📊 CURRENT DATABASE STATUS:")
    print(f"   👥 Total Users: {User.query.count()}")
    print(f"   🏷️  Total Categories: {Category.query.count()}")
    print(f"   🛒 Total Products: {Product.query.count()}")
    print("\n🔐 DEMO CREDENTIALS:")
    print("   👨‍💼 Admin - Username: admin, Password: admin123")
    print("   👤 User - Username: testuser, Password: user123")
    print("=" * 60)
