// Shared UI components rendered via JavaScript.
// These keep the navbar and footer consistent across all pages.

function getNavbar(activePage) {
  return `
  <div class="platform-nav" style="display:flex;gap:8px;padding:8px 16px;background:#1a1a2e;align-items:center;flex-wrap:wrap;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
    <span style="color:rgba(255,255,255,0.4);font-size:0.75em;text-transform:uppercase;letter-spacing:0.5px;margin-right:4px;">Aria Platform</span>
    <a href="../aria/" style="color:rgba(255,255,255,0.85);text-decoration:none;padding:4px 12px;border-radius:6px;font-size:0.82em;font-weight:500;background:rgba(255,255,255,0.06);transition:all 0.2s;">👤 Aria</a>
    <a href="../chat/" style="color:rgba(255,255,255,0.85);text-decoration:none;padding:4px 12px;border-radius:6px;font-size:0.82em;font-weight:500;background:rgba(255,255,255,0.06);transition:all 0.2s;">💬 Chat</a>
    <a href="../dashboard/" style="color:rgba(255,255,255,0.85);text-decoration:none;padding:4px 12px;border-radius:6px;font-size:0.82em;font-weight:500;background:rgba(255,255,255,0.06);transition:all 0.2s;">📊 Dashboard</a>
    <a href="./" style="color:#fff;text-decoration:none;padding:4px 12px;border-radius:6px;font-size:0.82em;font-weight:500;background:rgba(102,126,234,0.35);transition:all 0.2s;">🛒 Store</a>
  </div>
  <header class="header">
    <div class="container">
      <a href="index.html" class="logo">
        <i class="fa-solid fa-bolt"></i>
        TechDrop
      </a>
      <nav class="nav-links" id="navLinks">
        <a href="index.html" class="${activePage === 'home' ? 'active' : ''}">Home</a>
        <a href="products.html" class="${activePage === 'shop' ? 'active' : ''}">Shop</a>
        <a href="about.html" class="${activePage === 'about' ? 'active' : ''}">About</a>
        <a href="contact.html" class="${activePage === 'contact' ? 'active' : ''}">Contact</a>
      </nav>
      <div class="nav-search">
        <input type="text" class="nav-search-input" placeholder="Search products..." id="navSearchInput">
      </div>
      <button class="mobile-menu-btn" id="mobileMenuBtn" aria-label="Toggle menu">
        <i class="fa-solid fa-bars"></i>
      </button>
    </div>
  </header>`;
}

function getFooter() {
  const year = new Date().getFullYear();
  return `
  <footer class="footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-about">
          <div class="logo">
            <i class="fa-solid fa-bolt"></i>
            TechDrop
          </div>
          <p>Your one-stop shop for the latest electronics and gadgets. We source the best products at unbeatable prices.</p>
          <div class="footer-social">
            <a href="#" aria-label="Facebook"><i class="fa-brands fa-facebook-f"></i></a>
            <a href="#" aria-label="Twitter"><i class="fa-brands fa-twitter"></i></a>
            <a href="#" aria-label="Instagram"><i class="fa-brands fa-instagram"></i></a>
          </div>
        </div>
        <div class="footer-links">
          <h4>Shop</h4>
          <a href="products.html">All Products</a>
          <a href="products.html?category=smartphones">Smartphones</a>
          <a href="products.html?category=audio">Audio</a>
          <a href="products.html?category=wearables">Wearables</a>
        </div>
        <div class="footer-links">
          <h4>Company</h4>
          <a href="about.html">About Us</a>
          <a href="contact.html">Contact</a>
          <a href="#">Privacy Policy</a>
          <a href="#">Terms of Service</a>
        </div>
        <div class="footer-links">
          <h4>Support</h4>
          <a href="contact.html">Help Center</a>
          <a href="#">Shipping Info</a>
          <a href="#">Returns</a>
          <a href="#">FAQ</a>
        </div>
      </div>
      <div class="footer-bottom">
        &copy; ${year} TechDrop. All rights reserved.
        <span style="margin-left:16px;opacity:0.6;font-size:0.85em">
          Part of the <a href="../aria/" style="color:inherit;text-decoration:underline">Aria</a> platform
        </span>
      </div>
    </div>
  </footer>`;
}

function renderProductCard(product) {
  return `
  <div class="product-card">
    <a href="product.html?id=${product.id}">
      <div class="product-card-image">
        <img src="${product.image}" alt="${product.name}" loading="lazy">
      </div>
    </a>
    <div class="product-card-body">
      <div class="product-card-category">${product.category}</div>
      <h3 class="product-card-title">
        <a href="product.html?id=${product.id}">${product.name}</a>
      </h3>
      <div class="product-card-price">$${product.price.toFixed(2)}</div>
      <a href="product.html?id=${product.id}" class="btn btn-primary">View Details</a>
    </div>
  </div>`;
}

// Initialize shared components
function initComponents(activePage) {
  // Insert navbar
  const headerSlot = document.getElementById('header-slot');
  if (headerSlot) {
    headerSlot.innerHTML = getNavbar(activePage);
  }

  // Insert footer
  const footerSlot = document.getElementById('footer-slot');
  if (footerSlot) {
    footerSlot.innerHTML = getFooter();
  }

  // Mobile menu toggle
  document.addEventListener('click', function (e) {
    if (e.target.closest('#mobileMenuBtn')) {
      const nav = document.getElementById('navLinks');
      if (nav) nav.classList.toggle('open');
    }
  });

  // Nav search (redirect to products page with query)
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && e.target.id === 'navSearchInput') {
      const query = e.target.value.trim();
      if (query) {
        window.location.href = `products.html?search=${encodeURIComponent(query)}`;
      }
    }
  });
}
