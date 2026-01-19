import psycopg2
import time

# Your RDS connection details
VIRGINIA_CONFIG = {
    'host': 'database-1.cyd2y8oae1eo.us-east-1.rds.amazonaws.com',
    'database': 'flashsale',
    'user': 'flashadmin',
    'password': '19114messi',
    'port': 5432
}

IRELAND_CONFIG = {
    'host': 'database-ireland-replica.c3ys4uiwyug7.eu-west-1.rds.amazonaws.com',
    'database': 'flashsale',
    'user': 'flashadmin',
    'password': '19114messi',
    'port': 5432
}

def initialize_database():
    print("🚀 Initializing Flash Sale Database...")
    
    try:
        # Connect to Virginia primary
        print("🔗 Connecting to Virginia RDS...")
        conn_virginia = psycopg2.connect(**VIRGINIA_CONFIG)
        conn_virginia.autocommit = True
        cur_virginia = conn_virginia.cursor()
        
        # Create products table
        print("📦 Creating products table...")
        cur_virginia.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            original_price DECIMAL(10,2) NOT NULL,
            discount INTEGER DEFAULT 0,
            category VARCHAR(50),
            image_url VARCHAR(500),
            flash_sale BOOLEAN DEFAULT FALSE,
            stock INTEGER DEFAULT 100,
            region VARCHAR(20) DEFAULT 'us-east-1',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create orders table
        print("📋 Creating orders table...")
        cur_virginia.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            order_id VARCHAR(50) UNIQUE,
            user_id VARCHAR(100),
            product_id INTEGER,
            quantity INTEGER DEFAULT 1,
            total_price DECIMAL(10,2),
            status VARCHAR(20) DEFAULT 'pending',
            region VARCHAR(20) DEFAULT 'us-east-1',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        )
        ''')
        
        # Check if tables have data
        print("🔍 Checking existing data...")
        cur_virginia.execute("SELECT COUNT(*) FROM products")
        existing_products = cur_virginia.fetchone()[0]
        
        cur_virginia.execute("SELECT COUNT(*) FROM orders")
        existing_orders = cur_virginia.fetchone()[0]
        
        print(f"   Found: {existing_products} products, {existing_orders} orders")
        
        # Clear existing data (in correct order!)
        if existing_orders > 0:
            print("🗑️  Clearing existing orders...")
            cur_virginia.execute("DELETE FROM orders")
        
        if existing_products > 0:
            print("🗑️  Clearing existing products...")
            cur_virginia.execute("DELETE FROM products")
        
        # Reset sequence (optional, but good practice)
        cur_virginia.execute("ALTER SEQUENCE products_id_seq RESTART WITH 1")
        cur_virginia.execute("ALTER SEQUENCE orders_id_seq RESTART WITH 1")
        
        # Insert sample flash sale products
        print("🎁 Inserting sample products...")
        sample_products = [
            ('⚡ Flash Sale: Men\'s Premium Shirt', 29.99, 59.99, 50, 'men', 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400', True, 50),
            ('⚡ Flash Sale: Women\'s Summer Dress', 34.99, 69.99, 50, 'women', 'https://images.unsplash.com/photo-1567095761054-7a02e69e5c43?w=400', True, 30),
            ('⚡ Flash Sale: Kids Party Wear', 19.99, 39.99, 50, 'kids', 'https://images.unsplash.com/photo-1534321452387-cc6d5e2e8b03?w=400', True, 40),
            ('⚡ Flash Sale: Wireless Headphones', 49.99, 99.99, 50, 'electronics', 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400', True, 25),
            ('⚡ Flash Sale: Smart Watch', 199.99, 399.99, 50, 'electronics', 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400', True, 15),
            ('Running Shoes', 59.99, 119.99, 50, 'sports', 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400', True, 35),
            ('Backpack', 39.99, 79.99, 50, 'accessories', 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400', False, 60),
            ('Formal Blazer', 79.99, 159.99, 50, 'men', 'https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?w=400', False, 20)
        ]
        
        # Insert new products
        for product in sample_products:
            cur_virginia.execute('''
            INSERT INTO products (name, price, original_price, discount, category, image_url, flash_sale, stock)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', product)
        
        # Get product IDs for orders
        cur_virginia.execute("SELECT id FROM products ORDER BY id")
        product_ids = [row[0] for row in cur_virginia.fetchall()]
        
        # Create test orders
        print("📝 Creating sample orders...")
        test_orders = [
            ('FLASH-001', 'user123', product_ids[0], 2, 59.98, 'us-east-1'),
            ('FLASH-002', 'user456', product_ids[2], 1, 19.99, 'us-east-1'),
            ('FLASH-003', 'user789', product_ids[4], 1, 199.99, 'eu-west-1')
        ]
        
        for order in test_orders:
            cur_virginia.execute('''
            INSERT INTO orders (order_id, user_id, product_id, quantity, total_price, region)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (order_id) DO NOTHING
            ''', order)
        
        # Count records
        cur_virginia.execute("SELECT COUNT(*) FROM products")
        product_count = cur_virginia.fetchone()[0]
        
        cur_virginia.execute("SELECT COUNT(*) FROM orders")
        order_count = cur_virginia.fetchone()[0]
        
        print(f"\n✅ Virginia Database Initialized!")
        print(f"📊 Products: {product_count} items")
        print(f"📊 Orders: {order_count} records")
        
        # Show sample data
        print("\n📋 Sample Products:")
        cur_virginia.execute("SELECT id, name, price, flash_sale FROM products LIMIT 3")
        for row in cur_virginia.fetchall():
            print(f"   - #{row[0]}: {row[1]} - ${row[2]} (Flash: {row[3]})")
        
        cur_virginia.close()
        conn_virginia.close()
        
        # Wait for replication
        print("\n⏳ Waiting 30 seconds for data to replicate to Ireland...")
        time.sleep(30)
        
        # Test Ireland replica
        test_replication()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_replication():
    """Test if data replicated to Ireland"""
    try:
        print("\n🌍 Testing Cross-Region Replication...")
        
        # Connect to Ireland replica
        print("🔗 Connecting to Ireland RDS replica...")
        conn_ireland = psycopg2.connect(**IRELAND_CONFIG)
        cur_ireland = conn_ireland.cursor()
        
        # Check products count
        cur_ireland.execute("SELECT COUNT(*) FROM products")
        ireland_products = cur_ireland.fetchone()[0]
        
        # Check orders count  
        cur_ireland.execute("SELECT COUNT(*) FROM orders")
        ireland_orders = cur_ireland.fetchone()[0]
        
        print(f"✅ Ireland Replica Check:")
        print(f"   Products: {ireland_products} (should match Virginia)")
        print(f"   Orders: {ireland_orders} (should match Virginia)")
        
        # Show sample data
        cur_ireland.execute("SELECT id, name, price, flash_sale FROM products LIMIT 3")
        print("\n📋 Sample Products in Ireland:")
        for row in cur_ireland.fetchall():
            print(f"   - #{row[0]}: {row[1]} - ${row[2]} (Flash: {row[3]})")
        
        cur_ireland.close()
        conn_ireland.close()
        
        print("\n🎉 CROSS-REGION REPLICATION SUCCESSFUL!")
        print("💾 Data is automatically syncing between Virginia (US) and Ireland (EU)")
        
    except Exception as e:
        print(f"⚠️ Could not connect to Ireland replica: {e}")
        print("   This might be because:")
        print("   1. Replica is still being created (wait 20-30 minutes)")
        print("   2. Endpoint not found (check AWS Console for Ireland endpoint)")
        print("   3. Security Group needs PostgreSQL rule (port 5432 from 0.0.0.0/0)")

if __name__ == "__main__":
    initialize_database()