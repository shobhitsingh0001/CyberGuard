// --- Backend Config ---
const API_BASE_URL = "http://127.0.0.1:8000";

// --- Data Source (backend se aayega) ---
let products = [];
let orders = [];

// App State
let cart = [];
let wishlist = new Set();
let searchTerm = "";
let searchTimer;

// --- Category master list ---
const categories = [
  { name: "Audio", image: "https://th.bing.com/th/id/OIP.Kwva19RYoGa6bcpAtOulVgHaHa?w=152&h=180&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3" },
  { name: "Wearables", image: "https://th.bing.com/th?q=Weird+Wearables&w=120&h=120&c=1&rs=1&qlt=70&r=0&o=7&cb=1&dpr=1.3&pid=InlineBlock&rm=3&mkt=en-IN&cc=IN&setlang=en&adlt=moderate&t=1&mw=247" },
  { name: "Computers", image: "https://th.bing.com/th?q=MacBook+Pro+PNG&w=120&h=120&c=1&rs=1&qlt=70&r=0&o=7&cb=1&dpr=1.3&pid=InlineBlock&rm=3&mkt=en-IN&cc=IN&setlang=en&adlt=moderate&t=1&mw=247" },
  { name: "Accessories", image: "https://th.bing.com/th/id/OIP.R3fVt8cbjA1rI5hzroD9NwHaE7?w=275&h=183&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3" },
  { name: "Fashion", image: "https://th.bing.com/th/id/OIP.kjqZU0DyM7h9mMs8_rrXUwHaHa?w=185&h=185&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3" },
  { name: "Sports", image: "https://th.bing.com/th/id/OIP.RjcvOpDa0rpu2mmzPsRA1gHaJQ?w=143&h=180&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3" },
  { name: "Home & Kitchen", image: "https://th.bing.com/th/id/OIP.vi4vzi1iVsn7qOqHiVjZygHaEJ?w=320&h=180&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3" },
  { name: "Beauty", image: "https://th.bing.com/th/id/OIP.Y4aAa3FbCxmddYmiajU0JgHaEJ?w=329&h=187&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3" },
  { name: "Grocery", image: "https://th.bing.com/th/id/OIP.tX2d_nhdBNijw-biOB9vCwHaE8?w=259&h=180&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3" },
  { name: "Books & Stationery", image: "https://th.bing.com/th/id/OIP.q-hNw3ZVC8kyoNq78N8ZoQHaHa?w=161&h=180&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3" },
];

const FALLBACK_IMAGE =
  "data:image/svg+xml;charset=UTF-8," +
  encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="500" height="375" viewBox="0 0 500 375">
      <rect width="500" height="375" fill="#ECE7DE"/>
      <text x="50%" y="50%" font-family="Arial" font-size="20" fill="#6B7280" text-anchor="middle" dominant-baseline="middle">Image not available</text>
    </svg>
  `);

function getRating(id) {
  const seed = (id * 37) % 100;
  return (3.5 + (seed / 100) * 1.5).toFixed(1);
}

function getReviewCount(id) {
  return 20 + ((id * 53) % 480);
}

function getDiscountPercent(id) {
  const options = [0, 0, 10, 15, 20, 25, 30];
  return options[id % options.length];
}

function formatINR(amount) {
  return `₹${Math.round(amount).toLocaleString('en-IN')}`;
}

function productImageUrl(product) {
  return product.image_url && product.image_url !== "PASTE_IMAGE_LINK_HERE"
    ? product.image_url
    : FALLBACK_IMAGE;
}

function categoryImageUrl(category) {
  return category.image && category.image !== "PASTE_IMAGE_LINK_HERE"
    ? category.image
    : FALLBACK_IMAGE;
}

function handleImageError(imgEl) {
  imgEl.onerror = null;
  imgEl.src = FALLBACK_IMAGE;
}

// --- Account (login.html / signup.html handle the actual auth calls;
//     this just reflects login state in the header and lets you log out) ---
function updateAccountUI() {
  const label = document.getElementById('accountLabel');
  if (!label) return;
  const user = JSON.parse(localStorage.getItem('bharat_user') || 'null');
  label.innerText = user ? user.full_name.split(' ')[0] : 'Login';
}

function handleAccountClick() {
  const user = JSON.parse(localStorage.getItem('bharat_user') || 'null');
  if (user) {
    if (confirm(`Signed in as ${user.full_name}. Logout?`)) {
      localStorage.removeItem('bharat_token');
      localStorage.removeItem('bharat_user');
      updateAccountUI();
    }
  } else {
    window.location.href = 'login.html';
  }
}

// --- Fetch Products from Backend ---
async function loadProducts() {
  try {
    const res = await fetch(`${API_BASE_URL}/products`);
    if (!res.ok) throw new Error(`Server returned ${res.status}`);
    products = await res.json();
    renderProducts(products);
  } catch (err) {
    console.error("Failed to load products from backend:", err);
    const grid = document.getElementById('productGrid');
    grid.innerHTML = `<p style="color:#E63946;">Could not load products. Is the backend running at ${API_BASE_URL}?</p>`;
  }
}

// --- Fetch Orders from Backend ---
async function loadOrders() {
  try {
    const res = await fetch(`${API_BASE_URL}/orders`);
    if (!res.ok) throw new Error(`Server returned ${res.status}`);
    orders = await res.json();
    renderOrders();
  } catch (err) {
    console.error("Failed to load orders from backend:", err);
    const list = document.getElementById('ordersList');
    list.innerHTML = `<p style="color:#E63946;">Could not load orders. Is the backend running at ${API_BASE_URL}?</p>`;
  }
}

// --- Navigation ---
function switchTab(sectionId, element) {
  document.querySelectorAll('.section').forEach(sec => sec.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));

  document.getElementById(sectionId).classList.add('active');
  if (element) element.classList.add('active');
}

function resetAndGoHome(element) {
  searchTerm = "";
  const searchInput = document.getElementById('searchInput');
  if (searchInput) searchInput.value = "";
  renderProducts(products);
  document.getElementById('gridTitle').innerText = "Featured Products";
  document.getElementById('resetFilterBtn').style.display = "none";
  const homeBtn = element || document.querySelectorAll('.nav-btn')[0];
  switchTab('home', homeBtn);
}

// --- Search ---
function handleSearch(value) {
  searchTerm = value.trim().toLowerCase();
  clearTimeout(searchTimer);
  if (searchTerm === "") {
    renderProducts(products);
    document.getElementById('gridTitle').innerText = "Featured Products";
    document.getElementById('resetFilterBtn').style.display = "none";
    return;
  }
  switchTab('home', document.querySelectorAll('.nav-btn')[0]);
  searchTimer = setTimeout(async () => {
    try {
      const params = new URLSearchParams({ search: searchTerm });
      const res = await fetch(`${API_BASE_URL}/products?${params}`);
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const results = await res.json();
      if (searchTerm !== params.get('search')) return;
      renderProducts(results);
      document.getElementById('gridTitle').innerText = `Results for "${value}"`;
      document.getElementById('resetFilterBtn').style.display = "inline-block";
    } catch (err) {
      console.error("Failed to search products:", err);
    }
  }, 300);
}

// --- Wishlist (visual only, client-side) ---
function toggleWishlist(productId, event) {
  event.stopPropagation();
  if (wishlist.has(productId)) {
    wishlist.delete(productId);
  } else {
    wishlist.add(productId);
  }
  const btn = event.currentTarget;
  btn.classList.toggle('active');
  btn.innerText = wishlist.has(productId) ? "♥" : "♡";
}

// --- Render Products ---
function renderProducts(items) {
  const grid = document.getElementById('productGrid');

  if (!items || items.length === 0) {
    grid.innerHTML = `<p style="color:#6B7280;">No products found.</p>`;
    return;
  }

  grid.innerHTML = items.map(p => {
    const rating = getRating(p.id);
    const reviews = getReviewCount(p.id);
    const discount = getDiscountPercent(p.id);
    const originalPrice = discount > 0 ? p.price / (1 - discount / 100) : null;
    const isWishlisted = wishlist.has(p.id);

    return `
      <div class="product-card">
        <div class="product-image-wrap">
          <img class="product-image" src="${productImageUrl(p)}" alt="${p.name}" loading="lazy" referrerpolicy="no-referrer" onerror="handleImageError(this)">
          ${discount > 0 ? `<span class="badge-discount">${discount}% OFF</span>` : ''}
          <button class="wishlist-btn ${isWishlisted ? 'active' : ''}" onclick="toggleWishlist(${p.id}, event)" aria-label="Add to wishlist">${isWishlisted ? '♥' : '♡'}</button>
        </div>
        <div class="product-info">
          <div class="product-category">${p.category}</div>
          <div class="product-title">${p.name}</div>
          <div class="rating">
            <span class="stars">★ ${rating}</span>
            <span class="review-count">(${reviews})</span>
          </div>
          <div class="product-bottom">
            <div class="price-block">
              <span class="price">${formatINR(p.price)}</span>
              ${originalPrice ? `<span class="price-original">${formatINR(originalPrice)}</span>` : ''}
            </div>
            <button class="btn-add" onclick="addToCart(${p.id})">Add to Cart</button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// --- Render Categories ---
function renderCategories() {
  const grid = document.getElementById('categoryGrid');
  grid.innerHTML = categories.map(c => `
    <div class="category-card" onclick="filterCategory('${c.name}')">
      <div class="category-image-wrap">
        <img class="category-image" src="${categoryImageUrl(c)}" alt="${c.name}" loading="lazy" referrerpolicy="no-referrer" onerror="handleImageError(this)">
      </div>
      <h3>${c.name}</h3>
    </div>
  `).join('');
}

// --- Category Filter ---
function filterCategory(categoryName) {
  searchTerm = "";
  const searchInput = document.getElementById('searchInput');
  if (searchInput) searchInput.value = "";
  const filtered = products.filter(p => p.category === categoryName);
  renderProducts(filtered);
  document.getElementById('gridTitle').innerText = `${categoryName} Category`;
  document.getElementById('resetFilterBtn').style.display = "inline-block";

  switchTab('home', document.querySelectorAll('.nav-btn')[0]);
}

// --- Cart Management ---
function addToCart(productId) {
  const item = products.find(p => p.id === productId);
  if (!item) return;
  cart.push(item);
  updateCartUI();
}

function removeFromCart(index) {
  cart.splice(index, 1);
  updateCartUI();
}

function updateCartUI() {
  document.getElementById('cartCount').innerText = cart.length;

  const container = document.getElementById('cartItemsContainer');
  if (cart.length === 0) {
    container.innerHTML = `<p style="text-align:center; color:#6B7280; margin-top:2rem;">Your cart is empty.</p>`;
    document.getElementById('cartTotal').innerText = "₹0";
    return;
  }

  let total = 0;
  container.innerHTML = cart.map((item, index) => {
    total += item.price;
    return `
      <div class="cart-item">
        <div class="cart-item-info">
          <img class="cart-item-image" src="${productImageUrl(item)}" alt="${item.name}" referrerpolicy="no-referrer" onerror="handleImageError(this)">
          <div>
            <strong>${item.name}</strong>
            <div style="font-size:0.85rem; color:#6B7280;">${formatINR(item.price)}</div>
          </div>
        </div>
        <button onclick="removeFromCart(${index})" style="background:none; border:none; color:#E63946; cursor:pointer; font-weight:600;">Remove</button>
      </div>
    `;
  }).join('');

  document.getElementById('cartTotal').innerText = formatINR(total);
}

function toggleCart() {
  const modal = document.getElementById('cartModal');
  modal.classList.toggle('open');
}

// --- Update Order Status (Shipped / Delivered / Cancelled) ---
async function updateOrderStatus(orderId, newStatus) {
  try {
    const res = await fetch(`${API_BASE_URL}/orders/${orderId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });

    if (!res.ok) throw new Error(`Server returned ${res.status}`);

    await loadOrders();
  } catch (err) {
    console.error("Status update failed:", err);
    alert("Status update nahi ho paya. Backend check karo.");
  }
}

// --- Checkout System (order database me save hota hai) ---
async function checkout() {
  if (cart.length === 0) {
    alert("Your cart is empty!");
    return;
  }

  const payload = {
    items: cart.map(item => ({
      product_id: item.id,
      name: item.name,
      image_url: item.image_url,
      price: item.price
    }))
  };

  try {
    const res = await fetch(`${API_BASE_URL}/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`Server returned ${res.status}`);

    cart = [];
    updateCartUI();
    toggleCart();

    await loadOrders();

    switchTab('orders', document.querySelectorAll('.nav-btn')[2]);
    alert("Order placed successfully!");
  } catch (err) {
    console.error("Checkout failed:", err);
    alert("Order place nahi ho paya. Backend check karo.");
  }
}

// --- Render Orders ---
function renderOrders() {
  const list = document.getElementById('ordersList');
  if (!orders || orders.length === 0) {
    list.innerHTML = `<p style="color:#6B7280;">No orders yet.</p>`;
    return;
  }

  list.innerHTML = orders.map(o => {
    const itemNames = o.items.map(i => i.name).join(', ');
    const dateStr = new Date(o.created_at).toLocaleDateString('en-IN', {
      month: 'short', day: 'numeric', year: 'numeric'
    });

    return `
      <div class="order-item">
        <div>
          <strong>Order #${o.order_code}</strong>
          <p style="color:#6B7280; font-size:0.85rem; margin-top:4px;">
            Placed on ${dateStr} • ${o.items.length} Item(s)
          </p>
          <p style="font-size:0.8rem; color:#333; margin-top:4px;">
            Items: ${itemNames}
          </p>
        </div>
        <div style="text-align:right;">
          <span class="order-status" data-status="${o.status}">${o.status}</span>
          <div style="font-weight:700; margin-top:6px; font-family:'IBM Plex Mono', monospace;">${formatINR(o.total)}</div>
        </div>
      </div>
    `;
  }).join('');
}

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
  renderCategories();
  loadProducts();
  loadOrders();
  updateAccountUI();
});
