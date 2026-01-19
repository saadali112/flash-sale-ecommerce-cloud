

// ==================== DOM ELEMENTS ====================
let cart_count = document.getElementById("cart-count");
let toggle_btn = document.getElementById("toggle-btn");
let link_1 = document.getElementById("link-1");
let link_2 = document.getElementById("link-2");
let link_3 = document.getElementById("link-3");
let link_4 = document.getElementById("link-4");

// ==================== GLOBAL VARIABLES ====================
let mode = "light";
let body = document.body;
let all_products = JSON.parse(localStorage.getItem("all-products")) || [];
let product_id = JSON.parse(localStorage.getItem("product-id")) || "";
let cart = JSON.parse(localStorage.getItem("cart")) || [];

// AWS Configuration
const AWS_BACKEND_URL = "http://3.91.160.131"; // Your EC2 IP
let awsLoad = 30;
let awsInstances = 2;
let dbSyncStatus = "syncing";

// ==================== PAGE LOAD ====================
window.addEventListener("load", () => {
    // Update cart count
    cart_count.textContent = cart.length ? cart.length : "0";

    // Initialize AWS connection
    initializeAWSConnection();
    
    // Start AWS status updates
    setInterval(updateAWSStatus, 5000);
    
    // Load products from AWS or fallback
    loadProducts();
});

// ==================== AWS CONNECTION FUNCTIONS ====================

async function initializeAWSConnection() {
    console.log("🔗 Initializing AWS connection...");
    
    // Check AWS health
    const isHealthy = await checkAWSHealth();
    
    if (isHealthy) {
        console.log("✅ AWS backend is healthy");
        
        // Load products from AWS
        const products = await loadProductsFromAWS();
        
        if (products && products.length > 0) {
            // Display products from AWS
            displayProducts(products);
            all_products = products;
            localStorage.setItem("all-products", JSON.stringify(all_products));
        } else {
            // Fallback to local products
            loadLocalProducts();
        }
        
        // Start periodic health checks
        setInterval(checkAWSHealth, 30000);
        
    } else {
        console.log("⚠️ AWS not reachable - using fallback mode");
        loadLocalProducts();
    }
}

async function checkAWSHealth() {
    try {
        const response = await fetch(`${AWS_BACKEND_URL}/health`);
        const data = await response.json();
        
        const healthElement = document.getElementById('aws-health');
        if (healthElement) {
            healthElement.innerHTML = `
                <span style="color: #2ecc71;">●</span> 
                ${data.status.toUpperCase()} | 
                DB: ${data.database} | 
                EC2: ${data.server}
            `;
        }
        
        return data.status === 'healthy';
    } catch (error) {
        console.error("❌ AWS health check failed:", error);
        
        const healthElement = document.getElementById('aws-health');
        if (healthElement) {
            healthElement.innerHTML = `<span style="color: #e74c3c;">●</span> OFFLINE`;
        }
        
        return false;
    }
}

async function loadProductsFromAWS() {
    try {
        console.log("🌐 Fetching products from AWS backend...");
        
        const response = await fetch(`${AWS_BACKEND_URL}/products`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
            console.log(`✅ Loaded ${data.count} products from AWS`);
            
            // Update cloud status display
            updateCloudStatusDisplay(data);
            
            return data.products;
        } else {
            throw new Error(data.error || 'Unknown error');
        }
        
    } catch (error) {
        console.error("❌ Failed to load from AWS:", error);
        return null;
    }
}

async function placeOrderToAWS(productId, quantity = 1) {
    try {
        console.log(`📦 Placing order for product ${productId}...`);
        
        const response = await fetch(`${AWS_BACKEND_URL}/order`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: quantity,
                user_id: localStorage.getItem('user_id') || 'guest_' + Date.now()
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            console.log(`✅ Order placed: ${data.order_id}`);
            
            // Simulate AWS auto-scaling
            simulateAutoScaling();
            
            return data;
        } else {
            throw new Error(data.error || 'Order failed');
        }
        
    } catch (error) {
        console.error("❌ Order failed:", error);
        return null;
    }
}

// ==================== PRODUCT LOADING (MERGED) ====================

async function loadProducts() {
    // Try AWS first, fallback to local
    const awsProducts = await loadProductsFromAWS();
    
    if (awsProducts && awsProducts.length > 0) {
        all_products = awsProducts;
        displayProducts(awsProducts);
    } else {
        await loadLocalProducts();
    }
    
    localStorage.setItem("all-products", JSON.stringify(all_products));
}

async function loadLocalProducts() {
    try {
        let res = await fetch("Products.json");
        let data = await res.json();
        all_products = data;
        displayProducts(data);
    } catch (error) {
        console.log("Error loading local products:", error);
        createSampleFlashProducts();
        displayProducts(all_products);
    }
}

// ==================== PRODUCT DISPLAY ====================

function displayProducts(products) {
    const productsGrid = document.getElementById('featured-products') || 
                        document.querySelector('.items') || 
                        document.getElementById('products-container');
    
    if (!productsGrid) {
        console.error("❌ Products container not found");
        return;
    }
    
    productsGrid.innerHTML = '';
    
    products.forEach(product => {
        const productElement = createProductElement(product);
        productsGrid.appendChild(productElement);
    });
    
    console.log(`✅ Displayed ${products.length} products`);
}

function createProductElement(product) {
    const div = document.createElement('div');
    div.className = 'item';
    div.dataset.id = product.id;
    
    const discount = product.discount || 
                    Math.round((1 - (product.price || product.price) / (product.original_price || product.originalPrice)) * 100) || 0;
    const isFlashSale = product.flash_sale || product.flashSale || false;
    const price = product.price || 0;
    const originalPrice = product.original_price || product.originalPrice || price;
    
    div.innerHTML = `
        ${isFlashSale ? '<div class="flash-badge">⚡ FLASH SALE</div>' : ''}
        <img src="${product.image_url || product.image || 'Images/default-product.jpg'}" 
             alt="${product.name}" 
             class="product-img">
        <p>${product.name}</p>
        <div class="item-prices">
            <div class="item-price-new">$${price.toFixed(2)}</div>
            ${originalPrice > price ? 
                `<div class="item-price-old">$${originalPrice.toFixed(2)}</div>` : ''}
        </div>
        ${discount > 0 ? `<p style="color:#27ae60; font-size:14px;">${discount}% OFF!</p>` : ''}
        <button class="btn-add-cart" onclick="addToCart(${product.id})">
            🛒 Add to Cart
        </button>
    `;
    
    // Add click event for product details
    div.addEventListener('click', function(e) {
        if (!e.target.classList.contains('btn-add-cart')) {
            go_to_product_details(this);
        }
    });
    
    return div;
}

// ==================== CART FUNCTIONS (MERGED) ====================

function addToCart(productId) {
    // Get product
    const product = all_products.find(p => p.id == productId);
    
    if (product) {
        // Add to local cart
        cart.push({
            id: product.id,
            name: product.name,
            price: product.price || 0,
            quantity: 1
        });
        
        localStorage.setItem("cart", JSON.stringify(cart));
        cart_count.textContent = cart.length;
        
        // Try to sync with AWS
        syncOrderToAWS(productId, 1);
        
        alert(`Added to cart! ${isAWSConnected() ? '(Synced to AWS)' : '(Local only - AWS offline)'}`);
    }
}

async function syncOrderToAWS(productId, quantity) {
    try {
        const result = await placeOrderToAWS(productId, quantity);
        if (result) {
            console.log("✅ Order synced to AWS:", result.order_id);
        }
    } catch (error) {
        console.log("⚠️ Order not synced to AWS (offline mode)");
    }
}

function isAWSConnected() {
    const healthElement = document.getElementById('aws-health');
    return healthElement && healthElement.innerHTML.includes('HEALTHY');
}

// ==================== AWS STATUS SIMULATION (YOUR EXISTING CODE) ====================

function updateAWSStatus() {
    // Simulate AWS status changes
    const loadIndicator = document.getElementById('load-indicator');
    const currentLoad = document.getElementById('current-load');
    const regionUS = document.getElementById('region-us');
    const regionEU = document.getElementById('region-eu');
    const regionSync = document.getElementById('region-sync');
    
    if (loadIndicator && currentLoad) {
        // Simulate minor load fluctuations
        awsLoad = Math.max(30, Math.min(90, awsLoad + (Math.random() * 10 - 5)));
        loadIndicator.style.width = awsLoad + '%';
        currentLoad.textContent = Math.round(awsLoad) + '%';
        
        // Change color based on load
        if (awsLoad > 70) {
            loadIndicator.style.background = '#e74c3c';
            // Simulate auto-scaling
            if (awsLoad > 80 && awsInstances < 5) {
                awsInstances++;
                updateInstanceCount();
            }
        } else if (awsLoad > 50) {
            loadIndicator.style.background = '#f39c12';
        } else {
            loadIndicator.style.background = '#2ecc71';
            // Scale down if load is low
            if (awsLoad < 40 && awsInstances > 2) {
                awsInstances--;
                updateInstanceCount();
            }
        }
    }
    
    // Update region status
    if (regionUS && regionEU && regionSync) {
        // US region - always active (primary)
        regionUS.className = 'region-dot active';
        
        // EU region - simulate occasional sync delays
        if (Math.random() > 0.9) {
            regionEU.className = 'region-dot syncing';
        } else {
            regionEU.className = 'region-dot active';
        }
        
        // Database sync status
        const syncStates = ['syncing', 'active', 'syncing'];
        regionSync.className = 'region-dot ' + syncStates[Math.floor(Math.random() * syncStates.length)];
    }
}

function updateInstanceCount() {
    const ec2Status = document.getElementById('ec2-status');
    const scalingStatus = document.getElementById('scaling-status');
    
    if (ec2Status) {
        ec2Status.textContent = awsInstances + ' Active';
        
        // Show scaling animation
        if (ec2Status.className === 'service-status active') {
            ec2Status.className = 'service-status syncing';
            setTimeout(() => {
                ec2Status.className = 'service-status active';
            }, 1000);
        }
    }
    
    if (scalingStatus) {
        scalingStatus.textContent = awsInstances > 2 ? 'Scaling Up' : 'Normal';
    }
}

function simulateAutoScaling() {
    // Simulate increased load
    awsLoad = Math.min(100, awsLoad + 15);
    
    // Simulate auto-scaling
    if (awsLoad > 70 && awsInstances < 5) {
        awsInstances++;
        updateInstanceCount();
    }
    
    // Update UI
    const loadIndicator = document.getElementById('load-indicator');
    const currentLoad = document.getElementById('current-load');
    
    if (loadIndicator && currentLoad) {
        loadIndicator.style.width = `${awsLoad}%`;
        currentLoad.textContent = `${awsLoad}%`;
        
        // Change color based on load
        if (awsLoad > 80) {
            loadIndicator.style.background = '#e74c3c';
        } else if (awsLoad > 60) {
            loadIndicator.style.background = '#f39c12';
        } else {
            loadIndicator.style.background = '#2ecc71';
        }
    }
}

function updateCloudStatusDisplay(apiData) {
    // Update region status if elements exist
    const regionStatus = document.getElementById('region-status');
    if (regionStatus && apiData.region) {
        regionStatus.innerHTML = `
            <div class="region">
                <span class="region-dot active"></span>
                <span>${apiData.region}</span>
            </div>
            <div class="region">
                <span class="region-dot active"></span>
                <span>eu-west-1</span>
            </div>
        `;
    }
}

// ==================== LOAD TESTING SIMULATION ====================

function simulateLoadTest(level) {
    let users, loadPercentage, color;
    
    switch(level) {
        case 'low':
            users = 100;
            loadPercentage = 40;
            color = '#2ecc71';
            break;
        case 'medium':
            users = 1000;
            loadPercentage = 65;
            color = '#f39c12';
            break;
        case 'high':
            users = 10000;
            loadPercentage = 85;
            color = '#e74c3c';
            break;
    }
    
    // Update UI
    const loadIndicator = document.getElementById('load-indicator');
    const currentLoad = document.getElementById('current-load');
    const loadStatus = document.getElementById('load-status');
    
    if (loadIndicator && currentLoad && loadStatus) {
        loadIndicator.style.width = `${loadPercentage}%`;
        loadIndicator.style.background = color;
        currentLoad.textContent = `${loadPercentage}%`;
        loadStatus.textContent = `Simulating ${users.toLocaleString()} users`;
        loadStatus.style.color = color;
    }
    
    // Simulate auto-scaling response
    simulateAutoScalingResponse(level);
    
    // Try to call AWS load test endpoint
    try {
        fetch(`${AWS_BACKEND_URL}/simulate-load`, {
            method: 'POST'
        }).catch(e => console.log("AWS load test endpoint not available"));
    } catch (e) {
        // Ignore if not available
    }
    
    alert(`⚡ Load test started!\nSimulating: ${users.toLocaleString()} users\nAWS auto-scaling triggered: ${awsInstances} instances active`);
}

function simulateAutoScalingResponse(level) {
    switch(level) {
        case 'low':
            awsInstances = 2;
            break;
        case 'medium':
            awsInstances = 3;
            break;
        case 'high':
            awsInstances = 5;
            break;
    }
    updateInstanceCount();
}

// ==================== YOUR EXISTING FUNCTIONS ====================

function change_mode() {
    if (mode === "light") {
        body.style.backgroundColor = "black";
        body.style.color = "white";
        toggle_btn.style = "justify-content: end";
        if (link_1) link_1.style = "color: white;";
        if (link_2) link_2.style = "color: white;";
        if (link_3) link_2.style = "color: white;";
        if (link_4) link_4.style = "color: white;";
        mode = "dark";
    } else {
        body.style.backgroundColor = "white";
        body.style.color = "black";
        toggle_btn.style = "justify-content: start";
        if (link_1) link_1.style = "color: black;";
        if (link_2) link_2.style = "color: black;";
        if (link_3) link_3.style = "color: black;";
        if (link_4) link_4.style = "color: black;";
        mode = "light";
    }
};

function go_to_product_details(element) {
    product_id = element.getAttribute("data-id");
    localStorage.setItem("product-id", JSON.stringify(product_id));
    location = "Product Details.html";
};

function createSampleFlashProducts() {
    all_products = [
        {
            id: 1,
            name: "⚡ Flash Sale: Men's Premium Shirt",
            price: 29.99,
            originalPrice: 59.99,
            category: "men",
            flashSale: true,
            discount: 50,
            image_url: "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400"
        },
        {
            id: 2,
            name: "⚡ Flash Sale: Women's Summer Dress",
            price: 34.99,
            originalPrice: 69.99,
            category: "women",
            flashSale: true,
            discount: 50,
            image_url: "https://images.unsplash.com/photo-1567095761054-7a02e69e5c43?w=400"
        },
        {
            id: 3,
            name: "⚡ Flash Sale: Kids Party Wear",
            price: 19.99,
            originalPrice: 39.99,
            category: "kids",
            flashSale: true,
            discount: 50,
            image_url: "https://images.unsplash.com/photo-1534321452387-cc6d5e2e8b03?w=400"
        }
    ];
    
    localStorage.setItem("all-products", JSON.stringify(all_products));
}

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', function() {
    console.log('%c⚡ FLASH SALE CLOUD PROJECT', 'color: #3498db; font-size: 16px; font-weight: bold;');
    console.log('%cArchitecture: AWS EC2 + RDS + Auto-scaling + Multi-Region', 'color: #2ecc71;');
    console.log('%cBackend: http://3.91.160.131:5000', 'color: #9b59b6;');
    console.log('%cCourse: CE408 - Cloud and Distributed Computing', 'color: #e74c3c;');
    
    // Start load reduction simulation
    setInterval(() => {
        if (awsLoad > 30) {
            awsLoad = Math.max(30, awsLoad - 5);
            updateAWSStatus();
        }
    }, 10000);
});