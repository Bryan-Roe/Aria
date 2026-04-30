// Shared UI components rendered via JavaScript.
// These keep the navbar and footer consistent across all pages.

function getNavbar(activePage) {
  return `
  <a class="skip-link" href="#main-content">Skip to main content</a>
  <div class="store-platform-bar">
    <div class="container store-platform-inner">
      <span class="store-platform-label">Aria Platform</span>
      <div class="store-platform-links">
        <a href="../">Home</a>
        <a href="../documentation.html">Docs</a>
        <a href="../aria/">Aria</a>
        <a href="../chat/">Chat</a>
        <a href="../dashboard/hub.html">Dashboards</a>
        <a href="../monetization/pricing.html">Pricing</a>
        <a href="https://github.com/Bryan-Roe/Aria" target="_blank" rel="noreferrer" style="font-weight:700">★ Star on GitHub</a>
      </div>
    </div>
  </div>
  <header class="header">
    <div class="container">
      <a href="index.html" class="logo logo-store">
        <span class="logo-mark" aria-hidden="true"></span>
        <span class="logo-copy">
          <strong>Aria Store</strong>
          <span>plans, training, and deployment offers</span>
        </span>
      </a>
      <nav class="nav-links" id="navLinks">
        <a href="index.html" class="${activePage === 'home' ? 'active' : ''}">Overview</a>
        <a href="products.html" class="${activePage === 'shop' ? 'active' : ''}">Catalog</a>
        <a href="about.html" class="${activePage === 'about' ? 'active' : ''}">About</a>
        <a href="contact.html" class="${activePage === 'contact' ? 'active' : ''}">Contact</a>
      </nav>
      <div class="nav-search">
        <input type="text" class="nav-search-input" placeholder="Search offers… (/ or ⌘K)" id="navSearchInput">
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
          <div class="logo logo-store footer-logo">
            <span class="logo-mark" aria-hidden="true"></span>
            <span class="logo-copy">
              <strong>Aria Store</strong>
              <span>commercial routes for the Aria platform</span>
            </span>
          </div>
          <p>Aria Store packages subscriptions, training, quantum pilots, and deployment support so teams can adopt the platform without reverse-engineering the repo first.</p>
          <div class="footer-social">
            <a href="../documentation.html" aria-label="Documentation"><i class="fa-solid fa-book-open"></i></a>
            <a href="https://github.com/Bryan-Roe/Aria" target="_blank" rel="noreferrer" aria-label="GitHub"><i class="fa-brands fa-github"></i></a>
            <a href="https://github.com/Bryan-Roe/Aria/issues" target="_blank" rel="noreferrer" aria-label="Issues"><i class="fa-solid fa-life-ring"></i></a>
          </div>
        </div>
        <div class="footer-links">
          <h4>Catalog</h4>
          <a href="products.html">All Offers</a>
          <a href="products.html?category=subscriptions">Subscriptions</a>
          <a href="products.html?category=training">Training</a>
          <a href="products.html?category=quantum">Quantum Programs</a>
        </div>
        <div class="footer-links">
          <h4>Platform</h4>
          <a href="../">Landing Page</a>
          <a href="../documentation.html">Docs</a>
          <a href="../dashboard/hub.html">Dashboards</a>
          <a href="../monetization/pricing.html">Pricing</a>
        </div>
        <div class="footer-links">
          <h4>Customer</h4>
          <a href="about.html">How It Works</a>
          <a href="contact.html">Contact</a>
          <a href="../monetization/account.html">Account</a>
          <a href="https://github.com/Bryan-Roe/Aria/issues" target="_blank" rel="noreferrer">Issues</a>
        </div>
      </div>
      <div class="footer-bottom">
        &copy; ${year} Aria Store. All rights reserved.
        <span class="footer-meta">
          Part of the <a href="../aria/" style="color:inherit;text-decoration:underline">Aria</a> platform
        </span>
      </div>
    </div>
  </footer>`;
}

function renderProductCard(product) {
  var category = typeof getCategoryById === 'function' ? getCategoryById(product.category) : null;
  var categoryLabel = category ? category.name : product.category;
  return `
  <div class="product-card">
    <a href="product.html?id=${product.id}">
      <div class="product-card-image">
        <img src="${product.image}" alt="${product.name}" loading="lazy">
      </div>
    </a>
    <div class="product-card-body">
      <div class="product-card-category">${categoryLabel}</div>
      <h3 class="product-card-title">
        <a href="product.html?id=${product.id}">${product.name}</a>
      </h3>
      <div class="product-card-price">$${product.price.toFixed(2)}</div>
      <a href="product.html?id=${product.id}" class="btn btn-primary">View Offer</a>
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
      return;
    }

    const nav = document.getElementById('navLinks');
    const toggle = document.getElementById('mobileMenuBtn');
    if (nav && nav.classList.contains('open')) {
      const clickedNav = nav.contains(e.target);
      const clickedToggle = toggle && toggle.contains(e.target);
      if (!clickedNav && !clickedToggle) {
        nav.classList.remove('open');
      }
    }
  });

  // Nav search (redirect to products page with query)
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && e.target.id === 'navSearchInput') {
      const query = e.target.value.trim();
      if (query) {
        const onCatalogPage = /\/products\.html$/i.test(window.location.pathname || '');
        if (onCatalogPage) {
          window.dispatchEvent(new CustomEvent('store:nav-search-submit', { detail: { query: query } }));
        } else {
          window.location.href = `products.html?search=${encodeURIComponent(query)}`;
        }
      }
    }
  });

  if (!window.__storeSearchHotkeysBound) {
    window.__storeSearchHotkeysBound = true;
    document.addEventListener('keydown', function (e) {
      const navSearch = document.getElementById('navSearchInput');
      if (!navSearch) return;

      const activeEl = document.activeElement;
      const tag = activeEl && activeEl.tagName ? activeEl.tagName.toLowerCase() : '';
      const isTyping = tag === 'input' || tag === 'textarea' || (activeEl && activeEl.isContentEditable);

      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        navSearch.focus();
        navSearch.select();
        return;
      }

      if (e.key === '/' && !isTyping) {
        e.preventDefault();
        navSearch.focus();
      }
    });
  }
}
