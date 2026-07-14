/* ═══════════════════════════════════════════════════════
   ARIANTA — Frontend Application
   ═══════════════════════════════════════════════════════ */

// ─── State ───
let allProducts = [];
let activeFilter = 'All';

// ─── Category metadata (images + descriptions) ───
const categoryMeta = {
  'Dresses': {
    image: 'images/WhatsApp Image 2026-07-13 at 1.55.47 PM.jpeg',
    description: 'Effortless elegance'
  },
  'Kurtis & Sets': {
    image: 'images/WhatsApp Image 2026-07-13 at 1.55.48 PM.jpeg',
    description: 'Traditional charm'
  },
  'Co-ord Sets': {
    image: 'images/WhatsApp Image 2026-07-13 at 1.55.48 PM (1).jpeg',
    description: 'Modern pairings'
  }
};

// ─── DOM Ready ───
document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initHamburger();
  initScrollReveal();
  initSmoothScroll();
  initNewsletter();
  fetchProducts();
});

// ═══════════════════════════════════════════════════════
// NAVBAR — Scroll Effect
// ═══════════════════════════════════════════════════════
function initNavbar() {
  const navbar = document.getElementById('navbar');
  let lastScroll = 0;

  window.addEventListener('scroll', () => {
    const currentScroll = window.scrollY;

    if (currentScroll > 60) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }

    lastScroll = currentScroll;
  });

  // Active nav link highlighting
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.navbar-links a');

  window.addEventListener('scroll', () => {
    let current = '';
    sections.forEach(section => {
      const sectionTop = section.offsetTop - 120;
      if (window.scrollY >= sectionTop) {
        current = section.getAttribute('id');
      }
    });

    navLinks.forEach(link => {
      link.classList.remove('active');
      if (link.getAttribute('href') === `#${current}`) {
        link.classList.add('active');
      }
    });
  });
}

// ═══════════════════════════════════════════════════════
// HAMBURGER MENU
// ═══════════════════════════════════════════════════════
function initHamburger() {
  const hamburger = document.getElementById('hamburger');
  const navLinks = document.getElementById('navLinks');

  hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('active');
    navLinks.classList.toggle('open');
  });

  // Close on link click
  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      hamburger.classList.remove('active');
      navLinks.classList.remove('open');
    });
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!hamburger.contains(e.target) && !navLinks.contains(e.target)) {
      hamburger.classList.remove('active');
      navLinks.classList.remove('open');
    }
  });
}

// ═══════════════════════════════════════════════════════
// SCROLL REVEAL
// ═══════════════════════════════════════════════════════
function initScrollReveal() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
  );

  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
}

// ═══════════════════════════════════════════════════════
// SMOOTH SCROLL
// ═══════════════════════════════════════════════════════
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        const offset = 80;
        const y = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top: y, behavior: 'smooth' });
      }
    });
  });
}

// ═══════════════════════════════════════════════════════
// NEWSLETTER
// ═══════════════════════════════════════════════════════
function initNewsletter() {
  const form = document.getElementById('newsletterForm');
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const email = document.getElementById('newsletterEmail');
    const btn = form.querySelector('.btn');
    const originalText = btn.innerHTML;

    btn.innerHTML = '✓ Subscribed!';
    btn.style.background = 'linear-gradient(135deg, #8a9a72, #6b8055)';
    email.value = '';

    setTimeout(() => {
      btn.innerHTML = originalText;
      btn.style.background = '';
    }, 3000);
  });
}

// ═══════════════════════════════════════════════════════
// FETCH PRODUCTS — API first, then static JSON fallback
// ═══════════════════════════════════════════════════════
async function fetchProducts() {
  try {
    // Show skeletons while loading
    showLoadingSkeletons();

    let products = null;

    // Try 1: Express API (local development)
    try {
      const res = await fetch('api/products');
      if (res.ok) {
        const data = await res.json();
        if (data.success) products = data.products;
      }
    } catch (e) {
      // API not available, will try static fallback
    }

    // Try 2: Static JSON file (GitHub Pages / static hosting)
    if (!products) {
      try {
        const res = await fetch('data/products.json');
        if (res.ok) {
          products = await res.json();
        }
      } catch (e) {
        // Static file also not available
      }
    }

    if (products && products.length > 0) {
      allProducts = products;
      renderCategories();
      renderFilterPills();
      renderProducts(allProducts);
    } else {
      throw new Error('No products loaded');
    }
  } catch (err) {
    console.error('Failed to fetch products:', err);
    document.getElementById('productsGrid').innerHTML =
      '<p style="color:var(--color-text-muted);grid-column:1/-1;text-align:center;">Failed to load products. Please refresh.</p>';
  }
}

// ═══════════════════════════════════════════════════════
// LOADING SKELETONS
// ═══════════════════════════════════════════════════════
function showLoadingSkeletons() {
  const grid = document.getElementById('productsGrid');
  let html = '';
  for (let i = 0; i < 6; i++) {
    html += `
      <div class="product-card" style="pointer-events:none;">
        <div class="product-card-image skeleton" style="aspect-ratio:3/4;"></div>
        <div class="product-card-info">
          <div class="skeleton" style="height:12px;width:60%;margin-bottom:8px;"></div>
          <div class="skeleton" style="height:18px;width:90%;margin-bottom:8px;"></div>
          <div class="skeleton" style="height:14px;width:40%;"></div>
        </div>
      </div>`;
  }
  grid.innerHTML = html;
}

// ═══════════════════════════════════════════════════════
// RENDER CATEGORIES
// ═══════════════════════════════════════════════════════
function renderCategories() {
  const grid = document.getElementById('categoriesGrid');
  const categories = [...new Set(allProducts.map(p => p.category))];

  grid.innerHTML = categories.map(cat => {
    const meta = categoryMeta[cat] || {};
    const count = allProducts.filter(p => p.category === cat).length;
    return `
      <div class="category-card reveal" onclick="filterByCategory('${cat}')">
        <img src="${meta.image || ''}" alt="${cat}" loading="lazy">
        <div class="category-card-overlay">
          <h3 class="category-card-title">${cat}</h3>
          <span class="category-card-count">${count} piece${count !== 1 ? 's' : ''}</span>
        </div>
        <div class="category-card-arrow">→</div>
      </div>`;
  }).join('');

  // Re-observe new reveal elements
  initScrollReveal();
}

// ═══════════════════════════════════════════════════════
// RENDER FILTER PILLS
// ═══════════════════════════════════════════════════════
function renderFilterPills() {
  const container = document.getElementById('filterPills');
  const categories = ['All', ...new Set(allProducts.map(p => p.category))];

  container.innerHTML = categories.map(cat =>
    `<button class="filter-pill${cat === activeFilter ? ' active' : ''}" 
             onclick="filterProducts('${cat}')"
             id="filter-${cat.replace(/\s+/g, '-')}">${cat}</button>`
  ).join('');
}

// ═══════════════════════════════════════════════════════
// FILTER PRODUCTS
// ═══════════════════════════════════════════════════════
function filterProducts(category) {
  activeFilter = category;
  renderFilterPills();

  const filtered = category === 'All'
    ? allProducts
    : allProducts.filter(p => p.category === category);

  renderProducts(filtered);
}

function filterByCategory(category) {
  // Scroll to products section first
  const productsSection = document.getElementById('products');
  const offset = 80;
  const y = productsSection.getBoundingClientRect().top + window.scrollY - offset;
  window.scrollTo({ top: y, behavior: 'smooth' });

  // Apply filter after a short delay for visual flow
  setTimeout(() => filterProducts(category), 400);
}

// ═══════════════════════════════════════════════════════
// RENDER PRODUCTS
// ═══════════════════════════════════════════════════════
function renderProducts(products) {
  const grid = document.getElementById('productsGrid');

  grid.innerHTML = products.map((product, index) => {
    const discount = Math.round((1 - product.price / product.originalPrice) * 100);
    const tagClass = getTagClass(product.tag);

    return `
      <div class="product-card reveal" style="transition-delay: ${index * 80}ms;" id="product-card-${product.id}">
        <div class="product-card-image">
          <img src="${product.image}" alt="${product.name}" loading="lazy">
          ${product.tag ? `<span class="product-tag ${tagClass}">${product.tag}</span>` : ''}
          <button class="product-quick-view" onclick="openModal(${product.id})">Quick View</button>
        </div>
        <div class="product-card-info" onclick="openModal(${product.id})">
          <div class="product-card-category">${product.category}</div>
          <h3 class="product-card-name">${product.name}</h3>
          <div class="product-card-price">
            <span class="product-price-current">₹${product.price.toLocaleString('en-IN')}</span>
            <span class="product-price-original">₹${product.originalPrice.toLocaleString('en-IN')}</span>
            <span class="product-price-discount">${discount}% OFF</span>
          </div>
        </div>
      </div>`;
  }).join('');

  // Re-observe new reveal elements
  initScrollReveal();
}

function getTagClass(tag) {
  if (!tag) return '';
  const lower = tag.toLowerCase();
  if (lower.includes('new') || lower.includes('summer')) return 'new';
  if (lower.includes('trend') || lower.includes('best')) return 'trending';
  if (lower.includes('festive') || lower.includes('premium')) return 'festive';
  return '';
}

// ═══════════════════════════════════════════════════════
// PRODUCT MODAL
// ═══════════════════════════════════════════════════════
function openModal(productId) {
  const product = allProducts.find(p => p.id === productId);
  if (!product) return;

  const discount = Math.round((1 - product.price / product.originalPrice) * 100);

  document.getElementById('modalImage').src = product.image;
  document.getElementById('modalImage').alt = product.name;
  document.getElementById('modalTag').textContent = product.tag || product.category;
  document.getElementById('modalName').textContent = product.name;
  document.getElementById('modalPrice').textContent = `₹${product.price.toLocaleString('en-IN')}`;
  document.getElementById('modalOriginalPrice').textContent = `₹${product.originalPrice.toLocaleString('en-IN')}`;
  document.getElementById('modalDiscount').textContent = `${discount}% OFF`;
  document.getElementById('modalDescription').textContent = product.description;
  document.getElementById('modalFabric').textContent = product.fabric;
  document.getElementById('modalColor').textContent = product.colors.join(', ');

  // Sizes
  document.getElementById('modalSizes').innerHTML = product.sizes.map(size =>
    `<span class="modal-size">${size}</span>`
  ).join('');

  // Show modal
  const overlay = document.getElementById('productModal');
  overlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  const overlay = document.getElementById('productModal');
  overlay.classList.remove('active');
  document.body.style.overflow = '';
}

// Close modal on overlay click
document.getElementById('productModal').addEventListener('click', (e) => {
  if (e.target === e.currentTarget) closeModal();
});

// Close modal on close button
document.getElementById('modalClose').addEventListener('click', closeModal);

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeModal();
});
