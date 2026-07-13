const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));
app.use('/images', express.static(path.join(__dirname, 'image')));

// Helper: read products
function getProducts() {
  const data = fs.readFileSync(path.join(__dirname, 'data', 'products.json'), 'utf-8');
  return JSON.parse(data);
}

// ─── API Routes ───

// GET all products (optional ?category= filter)
app.get('/api/products', (req, res) => {
  try {
    let products = getProducts();
    const { category } = req.query;

    if (category && category !== 'All') {
      products = products.filter(p => p.category === category);
    }

    res.json({ success: true, count: products.length, products });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Failed to load products' });
  }
});

// GET single product by ID
app.get('/api/products/:id', (req, res) => {
  try {
    const products = getProducts();
    const product = products.find(p => p.id === parseInt(req.params.id));

    if (!product) {
      return res.status(404).json({ success: false, message: 'Product not found' });
    }

    res.json({ success: true, product });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Failed to load product' });
  }
});

// GET all categories
app.get('/api/categories', (req, res) => {
  try {
    const products = getProducts();
    const categories = [...new Set(products.map(p => p.category))];
    res.json({ success: true, categories });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Failed to load categories' });
  }
});

// Fallback: serve index.html for any non-API route
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start server
app.listen(PORT, () => {
  console.log(`\n  ✨ Arianta is running at http://localhost:${PORT}\n`);
});
