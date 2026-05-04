// Main application logic: product filtering, searching, and page-specific init.

// ===== Utility =====
function getQueryParam(key) {
  const params = new URLSearchParams(window.location.search);
  return params.get(key);
}

function getProductById(id) {
  return PRODUCTS.find(function (p) { return p.id === parseInt(id); });
}

// ===== Homepage =====
function initHomePage() {
  initComponents('home');

  // Render category cards
  var catGrid = document.getElementById('categoriesGrid');
  if (catGrid) {
    catGrid.innerHTML = CATEGORIES.map(function (cat) {
      return '<a href="products.html?category=' + cat.id + '" class="category-card">' +
        '<i class="fa-solid ' + cat.icon + '"></i>' +
        '<h3>' + cat.name + '</h3>' +
        '<p>Browse ' + cat.name + '</p>' +
        '</a>';
    }).join('');
  }

  // Render featured products
  var featuredGrid = document.getElementById('featuredGrid');
  if (featuredGrid) {
    var featured = PRODUCTS.filter(function (p) { return p.featured; });
    if (featured.length === 0) featured = PRODUCTS.slice(0, 4);
    featuredGrid.innerHTML = featured.map(renderProductCard).join('');
  }
}

// ===== Shop / Products Listing =====
function initShopPage() {
  initComponents('shop');

  var categoryFilter = document.getElementById('categoryFilter');
  var sortFilter = document.getElementById('sortFilter');
  var priceRange = document.getElementById('priceRange');
  var priceLabel = document.getElementById('priceLabel');
  var grid = document.getElementById('shopProductsGrid');
  var resultsCount = document.getElementById('resultsCount');

  // Set initial category from URL
  var urlCategory = getQueryParam('category');
  if (urlCategory && categoryFilter) {
    categoryFilter.value = urlCategory;
  }

  // Set initial search from URL
  var urlSearch = getQueryParam('search');
  var navSearch = document.getElementById('navSearchInput');
  if (urlSearch && navSearch) {
    navSearch.value = urlSearch;
  }

  // Find max price for range slider
  var maxPrice = Math.max.apply(null, PRODUCTS.map(function (p) { return p.price; }));
  if (priceRange) {
    priceRange.max = Math.ceil(maxPrice / 10) * 10 + 50;
    priceRange.value = priceRange.max;
  }

  function renderProducts() {
    var category = categoryFilter ? categoryFilter.value : 'all';
    var sort = sortFilter ? sortFilter.value : 'default';
    var maxP = priceRange ? parseFloat(priceRange.value) : Infinity;
    var search = navSearch ? navSearch.value.trim().toLowerCase() : '';

    // Also check URL search param
    if (!search && urlSearch) {
      search = urlSearch.toLowerCase();
    }

    var filtered = PRODUCTS.filter(function (p) {
      var catMatch = category === 'all' || p.category === category;
      var priceMatch = p.price <= maxP;
      var searchMatch = !search ||
        p.name.toLowerCase().indexOf(search) !== -1 ||
        p.description.toLowerCase().indexOf(search) !== -1 ||
        p.category.toLowerCase().indexOf(search) !== -1;
      return catMatch && priceMatch && searchMatch;
    });

    // Sort
    if (sort === 'price-low') {
      filtered.sort(function (a, b) { return a.price - b.price; });
    } else if (sort === 'price-high') {
      filtered.sort(function (a, b) { return b.price - a.price; });
    } else if (sort === 'name') {
      filtered.sort(function (a, b) { return a.name.localeCompare(b.name); });
    }

    if (resultsCount) {
      resultsCount.textContent = filtered.length + ' product' + (filtered.length !== 1 ? 's' : '') + ' found';
    }

    if (priceLabel) {
      priceLabel.textContent = '$' + maxP.toFixed(0);
    }

    if (grid) {
      if (filtered.length === 0) {
        grid.innerHTML = '<div class="no-results"><i class="fa-solid fa-box-open"></i><p>No products match your filters.</p></div>';
      } else {
        grid.innerHTML = filtered.map(renderProductCard).join('');
      }
    }
  }

  // Event listeners
  if (categoryFilter) categoryFilter.addEventListener('change', renderProducts);
  if (sortFilter) sortFilter.addEventListener('change', renderProducts);
  if (priceRange) priceRange.addEventListener('input', renderProducts);

  // Re-filter on nav search input
  if (navSearch) {
    navSearch.addEventListener('input', function () {
      urlSearch = '';  // Clear URL search when user types
      renderProducts();
    });
  }

  renderProducts();
}

// ===== Product Detail =====
function initProductPage() {
  initComponents('shop');

  var productId = getQueryParam('id');
  var product = productId ? getProductById(productId) : null;
  var container = document.getElementById('productDetail');
  var relatedGrid = document.getElementById('relatedGrid');

  if (!product || !container) {
    if (container) {
      container.innerHTML = '<div style="text-align:center;padding:60px 20px;">' +
        '<h2>Product Not Found</h2>' +
        '<p style="margin:16px 0;">The product you are looking for does not exist.</p>' +
        '<a href="products.html" class="btn btn-primary">Browse Products</a></div>';
    }
    return;
  }

  // Set page title
  document.title = product.name + ' - TechDrop';

  // Render breadcrumb + detail
  var featuresHtml = '';
  if (product.features && product.features.length > 0) {
    featuresHtml = '<div class="product-detail-features">' +
      '<h3>Key Features</h3><ul>' +
      product.features.map(function (f) { return '<li>' + f + '</li>'; }).join('') +
      '</ul></div>';
  }

  container.innerHTML =
    '<div class="breadcrumb">' +
      '<a href="index.html">Home</a> / ' +
      '<a href="products.html">Shop</a> / ' +
      '<span>' + product.name + '</span>' +
    '</div>' +
    '<div class="product-detail-grid">' +
      '<div class="product-detail-image">' +
        '<img src="' + product.image + '" alt="' + product.name + '">' +
      '</div>' +
      '<div class="product-detail-info">' +
        '<div class="product-detail-category">' + product.category + '</div>' +
        '<h1>' + product.name + '</h1>' +
        '<div class="product-detail-price">$' + product.price.toFixed(2) + '</div>' +
        '<p class="product-detail-description">' + product.description + '</p>' +
        featuresHtml +
        '<div class="product-detail-actions">' +
          '<a href="contact.html?product=' + encodeURIComponent(product.name) + '" class="btn btn-primary">' +
            '<i class="fa-solid fa-envelope"></i> Inquire About This Product' +
          '</a>' +
        '</div>' +
      '</div>' +
    '</div>';

  // Related products (same category, different id)
  if (relatedGrid) {
    var related = PRODUCTS.filter(function (p) {
      return p.category === product.category && p.id !== product.id;
    }).slice(0, 4);

    // If not enough in same category, fill with others
    if (related.length < 4) {
      var others = PRODUCTS.filter(function (p) {
        return p.id !== product.id && related.indexOf(p) === -1;
      });
      related = related.concat(others).slice(0, 4);
    }

    if (related.length > 0) {
      relatedGrid.innerHTML = related.map(renderProductCard).join('');
    }
  }
}

// ===== About Page =====
function initAboutPage() {
  initComponents('about');
}

// ===== Contact Page =====
function initContactPage() {
  initComponents('contact');

  // Pre-fill product subject if coming from product detail page
  var productName = getQueryParam('product');
  var subjectInput = document.getElementById('contactSubject');
  if (productName && subjectInput) {
    subjectInput.value = 'Inquiry about: ' + productName;
  }

  // Handle form submission (mailto fallback)
  var form = document.getElementById('contactForm');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = document.getElementById('contactName').value;
      var email = document.getElementById('contactEmail').value;
      var subject = document.getElementById('contactSubject').value;
      var message = document.getElementById('contactMessage').value;

      var body = 'Name: ' + name + '\nEmail: ' + email + '\n\n' + message;
      var mailto = 'mailto:contact@example.com?subject=' +
        encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);

      window.location.href = mailto;
    });
  }
}
