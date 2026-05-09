// Main application logic: product filtering, searching, and page-specific init.

// ===== Utility =====
function getQueryParam(key) {
  const params = new URLSearchParams(window.location.search);
  return params.get(key);
}

function getProductById(id) {
  return PRODUCTS.find(function (p) { return p.id === parseInt(id); });
}

function getCategoryName(categoryId) {
  var category = typeof getCategoryById === 'function' ? getCategoryById(categoryId) : null;
  return category ? category.name : categoryId;
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
  var clearFiltersBtn = document.getElementById('clearFiltersBtn');
  var navSearch = document.getElementById('navSearchInput');

  // Find max price for range slider first so URL state can clamp correctly.
  var maxPrice = Math.max.apply(null, PRODUCTS.map(function (p) { return p.price; }));
  if (priceRange) {
    priceRange.max = Math.ceil(maxPrice / 10) * 10 + 50;
    priceRange.value = priceRange.max;
  }

  function hasOption(selectEl, value) {
    if (!selectEl) return false;
    return Array.prototype.some.call(selectEl.options, function (opt) {
      return opt.value === value;
    });
  }

  function clampNumber(value, min, max) {
    if (!isFinite(value)) return max;
    return Math.max(min, Math.min(max, value));
  }

  function parseUrlState() {
    var params = new URLSearchParams(window.location.search);
    var category = params.get('category') || 'all';
    var sort = params.get('sort') || 'default';
    var search = (params.get('search') || '').trim();
    var maxP = parseFloat(params.get('maxPrice'));

    if (!hasOption(categoryFilter, category)) category = 'all';
    if (!hasOption(sortFilter, sort)) sort = 'default';

    if (priceRange) {
      var sliderMax = parseFloat(priceRange.max);
      maxP = clampNumber(maxP, 0, sliderMax);
    }

    return {
      category: category,
      sort: sort,
      search: search,
      maxP: maxP
    };
  }

  function applyState(state) {
    if (categoryFilter) categoryFilter.value = state.category;
    if (sortFilter) sortFilter.value = state.sort;

    if (priceRange) {
      var sliderMax = parseFloat(priceRange.max);
      var nextMax = isFinite(state.maxP) ? state.maxP : sliderMax;
      priceRange.value = String(clampNumber(nextMax, 0, sliderMax));
    }

    if (navSearch) {
      navSearch.value = state.search || '';
    }
  }

  function getCurrentState() {
    return {
      category: categoryFilter ? categoryFilter.value : 'all',
      sort: sortFilter ? sortFilter.value : 'default',
      search: navSearch ? navSearch.value.trim() : '',
      maxP: priceRange ? parseFloat(priceRange.value) : Infinity
    };
  }

  function updateUrlFromState(state) {
    var params = new URLSearchParams();

    if (state.category && state.category !== 'all') params.set('category', state.category);
    if (state.search) params.set('search', state.search);
    if (state.sort && state.sort !== 'default') params.set('sort', state.sort);

    if (priceRange) {
      var sliderMax = parseFloat(priceRange.max);
      if (state.maxP < sliderMax) {
        params.set('maxPrice', String(Math.round(state.maxP)));
      }
    }

    var query = params.toString();
    var newPath = 'products.html' + (query ? '?' + query : '');
    var currentPath = window.location.pathname.split('/').pop() + window.location.search;

    if (newPath !== currentPath) {
      history.replaceState({ filters: state }, '', newPath);
    }
  }

  function buildResultSummary(count, state) {
    var summary = count + ' offer' + (count !== 1 ? 's' : '') + ' found';
    var details = [];

    if (state.category !== 'all') {
      details.push(getCategoryName(state.category));
    }

    if (state.search) {
      details.push('search: "' + state.search + '"');
    }

    if (priceRange) {
      var sliderMax = parseFloat(priceRange.max);
      if (state.maxP < sliderMax) {
        details.push('max $' + state.maxP.toFixed(0));
      }
    }

    if (details.length) {
      summary += ' • ' + details.join(' • ');
    }

    return summary;
  }

  function hasActiveFilters(state) {
    if (!state) return false;
    if (state.category !== 'all') return true;
    if (state.sort !== 'default') return true;
    if (state.search) return true;
    if (priceRange) {
      var sliderMax = parseFloat(priceRange.max);
      if (state.maxP < sliderMax) return true;
    }
    return false;
  }

  function clearAllFilters() {
    if (categoryFilter) categoryFilter.value = 'all';
    if (sortFilter) sortFilter.value = 'default';
    if (priceRange) priceRange.value = priceRange.max;
    if (navSearch) navSearch.value = '';
    renderProducts();
  }

  function renderProducts(options) {
    options = options || {};
    var state = getCurrentState();
    var category = state.category;
    var sort = state.sort;
    var maxP = state.maxP;
    var search = state.search.toLowerCase();

    var filtered = PRODUCTS.filter(function (p) {
      var catMatch = category === 'all' || p.category === category;
      var priceMatch = p.price <= maxP;
      var categoryName = getCategoryName(p.category).toLowerCase();
      var searchMatch = !search ||
        p.name.toLowerCase().indexOf(search) !== -1 ||
        p.description.toLowerCase().indexOf(search) !== -1 ||
        categoryName.indexOf(search) !== -1;
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
      resultsCount.textContent = buildResultSummary(filtered.length, state);
    }

    if (clearFiltersBtn) {
      clearFiltersBtn.disabled = !hasActiveFilters(state);
    }

    if (priceLabel) {
      priceLabel.textContent = '$' + maxP.toFixed(0);
    }

    if (grid) {
      if (filtered.length === 0) {
        grid.innerHTML = '<div class="no-results"><i class="fa-solid fa-box-open"></i><p>No offers match your current filters.</p></div>';
      } else {
        grid.innerHTML = filtered.map(renderProductCard).join('');
      }
    }

    if (!options.skipUrlSync) {
      updateUrlFromState(state);
    }
  }

  function applyUrlStateAndRender() {
    var state = parseUrlState();
    applyState(state);
    renderProducts({ skipUrlSync: true });
  }

  // Event listeners
  if (categoryFilter) categoryFilter.addEventListener('change', renderProducts);
  if (sortFilter) sortFilter.addEventListener('change', renderProducts);
  if (priceRange) priceRange.addEventListener('input', renderProducts);
  if (clearFiltersBtn) clearFiltersBtn.addEventListener('click', clearAllFilters);

  // Re-filter on nav search input
  if (navSearch) {
    navSearch.addEventListener('input', renderProducts);
  }

  window.addEventListener('store:nav-search-submit', function (event) {
    if (!navSearch) return;
    if (event && event.detail && typeof event.detail.query === 'string') {
      navSearch.value = event.detail.query;
      renderProducts();
    }
  });

  document.addEventListener('keydown', function (event) {
    if (!navSearch) return;

    var activeEl = document.activeElement;
    var tag = activeEl && activeEl.tagName ? activeEl.tagName.toLowerCase() : '';
    var isTyping = tag === 'input' || tag === 'textarea' || (activeEl && activeEl.isContentEditable);

    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      navSearch.focus();
      navSearch.select();
      return;
    }

    if (event.key === '/' && !isTyping) {
      event.preventDefault();
      navSearch.focus();
      return;
    }

    if (event.key === 'Escape' && hasActiveFilters(getCurrentState())) {
      event.preventDefault();
      clearAllFilters();
    }
  });

  window.addEventListener('popstate', function () {
    applyUrlStateAndRender();
  });

  applyUrlStateAndRender();
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
        '<h2>Offer Not Found</h2>' +
        '<p style="margin:16px 0;">The offer you are looking for does not exist.</p>' +
        '<a href="products.html" class="btn btn-primary">Browse Catalog</a></div>';
    }
    return;
  }

  // Set page title
  document.title = product.name + ' - Aria Store';

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
      '<a href="products.html">Catalog</a> / ' +
      '<span>' + product.name + '</span>' +
    '</div>' +
    '<div class="product-detail-grid">' +
      '<div class="product-detail-image">' +
        '<img src="' + product.image + '" alt="' + product.name + '">' +
      '</div>' +
      '<div class="product-detail-info">' +
        '<div class="product-detail-category">' + getCategoryName(product.category) + '</div>' +
        '<h1>' + product.name + '</h1>' +
        '<div class="product-detail-price">$' + product.price.toFixed(2) + '</div>' +
        '<p class="product-detail-description">' + product.description + '</p>' +
        featuresHtml +
        '<div class="product-detail-actions">' +
          '<a href="contact.html?product=' + encodeURIComponent(product.name) + '" class="btn btn-primary">' +
            '<i class="fa-solid fa-envelope"></i> Talk to the Team' +
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

      var title = subject || 'Store inquiry';
      var body = '### Store inquiry\n' +
        '- Name: ' + name + '\n' +
        '- Email: ' + email + '\n' +
        '- Page: docs/store/contact.html\n\n' +
        message;
      var issueUrl = 'https://github.com/Bryan-Roe/Aria/issues/new?title=' +
        encodeURIComponent(title) + '&body=' + encodeURIComponent(body);

      window.location.href = issueUrl;
    });
  }
}
