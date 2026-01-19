from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import os
from datetime import datetime
import time
import random

app = Flask(__name__)
CORS(app)  # Allow frontend to connect

# Database configuration - using YOUR RDS endpoints
DB_CONFIG = {
    'host': 'database-1.cyd2y8oae1eo.us-east-1.rds.amazonaws.com',
    'database': 'flashsale',
    'user': 'flashadmin',
    'password': '19114messi',
    'port': 5432
}

def get_db_connection():
    """Create and return database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise

# ==================== HELPER FUNCTIONS ====================

def calculate_flash_sale_status():
    """Calculate flash sale status and time remaining"""
    # Flash sale runs for next 24 hours from server start
    end_time = app.config.get('flash_sale_end')
    if not end_time:
        # Set flash sale to end 24 hours from now
        end_time = time.time() + (24 * 60 * 60)
        app.config['flash_sale_end'] = end_time
    
    time_remaining = end_time - time.time()
    hours = int(time_remaining // 3600)
    minutes = int((time_remaining % 3600) // 60)
    seconds = int(time_remaining % 60)
    
    return {
        'active': time_remaining > 0,
        'hours': max(0, hours),
        'minutes': max(0, minutes),
        'seconds': max(0, seconds),
        'total_seconds': max(0, int(time_remaining))
    }

# ==================== API ENDPOINTS ====================

@app.route('/')
def home():
    """Home endpoint - API information"""
    flash_sale = calculate_flash_sale_status()
    
    return jsonify({
        'service': '⚡ Flash Sale Cloud Backend',
        'version': '1.0',
        'status': 'online',
        'database': {
            'type': 'AWS RDS PostgreSQL',
            'primary': 'us-east-1 (Virginia)',
            'replica': 'eu-west-1 (Ireland)',
            'status': 'replicating'
        },
        'flash_sale': flash_sale,
        'cloud_architecture': {
            'compute': 'AWS EC2 (IaaS)',
            'database': 'AWS RDS (PaaS)',
            'storage': 'AWS S3 (PaaS)',
            'load_balancing': 'AWS ALB',
            'auto_scaling': 'Enabled'
        },
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'GET /products': 'Get all flash sale products',
            'GET /products/<id>': 'Get product details',
            'POST /order': 'Place an order',
            'GET /orders': 'Get recent orders',
            'GET /health': 'Health check',
            'POST /simulate-load': 'Simulate flash sale traffic',
            'GET /aws-status': 'AWS service status'
        }
    })

@app.route('/products')
def get_products():
    """Get all flash sale products"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get all products
        cur.execute('''
            SELECT id, name, price, original_price, discount, 
                   category, image_url, flash_sale, stock,
                   region, created_at
            FROM products 
            ORDER BY flash_sale DESC, id
        ''')
        
        products = []
        for row in cur.fetchall():
            # Calculate savings
            savings = float(row[3]) - float(row[2])
            savings_percent = int((savings / float(row[3])) * 100) if float(row[3]) > 0 else 0
            
            products.append({
                'id': row[0],
                'name': row[1],
                'price': float(row[2]),
                'original_price': float(row[3]),
                'discount': row[4],
                'category': row[5],
                'image_url': row[6],
                'flash_sale': row[7],
                'stock': row[8],
                'region': row[9],
                'created_at': row[10].isoformat() if row[10] else None,
                'savings': round(savings, 2),
                'savings_percent': savings_percent,
                'status': 'In Stock' if row[8] > 10 else ('Low Stock' if row[8] > 0 else 'Out of Stock')
            })
        
        cur.close()
        conn.close()
        
        flash_sale = calculate_flash_sale_status()
        
        return jsonify({
            'status': 'success',
            'count': len(products),
            'products': products,
            'flash_sale': flash_sale,
            'region': 'us-east-1',
            'timestamp': datetime.now().isoformat(),
            'cloud_info': {
                'database_region': 'Virginia (us-east-1)',
                'replica_region': 'Ireland (eu-west-1)',
                'auto_scaling': 'ready'
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for load balancer"""
    try:
        # Test database connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        
        flash_sale = calculate_flash_sale_status()
        
        return jsonify({
            'status': 'healthy',
            'service': 'flash-sale-backend',
            'database': 'connected',
            'flash_sale_active': flash_sale['active'],
            'timestamp': datetime.now().isoformat(),
            'region': 'us-east-1'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'flash-sale-backend',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/simulate-load', methods=['POST'])
def simulate_load():
    """Simulate high load for auto-scaling demo"""
    try:
        # Simulate CPU-intensive task
        start_time = time.time()
        
        # Perform some computation
        result = 0
        for i in range(1000000):
            result += random.random()
        
        processing_time = time.time() - start_time
        
        # Simulate database operations
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM products')
        product_count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        return jsonify({
            'status': 'load_test_complete',
            'processing_time': round(processing_time, 4),
            'product_count': product_count,
            'simulated_users': random.randint(100, 1000),
            'region': 'us-east-1',
            'instance': 'backend-server-' + str(random.randint(1, 100)),
            'cpu_load': random.randint(30, 90),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

# ==================== MAIN ====================

if __name__ == '__main__':
    print("="*60)
    print("🚀 STARTING FLASH SALE CLOUD BACKEND")
    print("="*60)
    print("📦 Database: AWS RDS PostgreSQL Multi-Region")
    print("   • Primary: Virginia (us-east-1)")
    print("   • Replica: Ireland (eu-west-1)")
    print("⚡ Flash Sale: Active for 24 hours")
    print("🌐 API: http://localhost:5000")
    print("🔧 Endpoints:")
    print("   • GET  /              - API info")
    print("   • GET  /products      - Get all products")
    print("   • POST /order         - Place order")
    print("   • GET  /health        - Health check")
    print("   • POST /simulate-load - Load test")
    print("="*60)
    
    # Set flash sale end time
    app.config['flash_sale_end'] = time.time() + (24 * 60 * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)