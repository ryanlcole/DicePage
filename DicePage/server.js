const express = require("express");
const path = require("path");
const fs = require("fs");

const app = express();
const PORT = process.env.PORT || 3000;

// 🔒 Force HTTPS + Redirect www → non-www
app.use((req, res, next) => {
    // Redirect HTTP to HTTPS
    if (req.headers["x-forwarded-proto"] !== "https") {
        return res.redirect(301, `https://${req.headers.host}${req.url}`);
    }

    // Redirect www to non-www
    if (req.headers.host && req.headers.host.startsWith("www.")) {
        const newHost = req.headers.host.slice(4); // remove "www."
        return res.redirect(301, `https://${newHost}${req.url}`);
    }

    next();
});

// Serve static files from /Public
app.use(express.static(path.join(__dirname, "Public")));

// Load product data
let products = {};
try {
    const raw = fs.readFileSync(path.join(__dirname, "products.json"), "utf-8");
    products = JSON.parse(raw);
} catch (err) {
    console.error("❌ Could not load products.json:", err.message);
}

// Build category routes dynamically
const categories = Object.keys(products);

categories.forEach((cat) => {
    app.get(`/${cat}`, (req, res) => {
        const items = products[cat] || [];
        const grid = items
            .map(
                (p) => `
      <div style="border:1px solid #ccc; padding:10px; margin:10px; width:150px; text-align:center;">
        <img src="${p.image}" alt="${p.name}" style="max-width:100px; display:block; margin:auto;" />
        <h3>${p.name}</h3>
        <p>$${p.price}</p>
      </div>
    `
            )
            .join("");

        res.send(`
      <html>
        <head>
          <title>${cat} - Shaelvien Dice Page</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .grid { display: flex; flex-wrap: wrap; }
            a { display:inline-block; margin:20px; text-decoration:none; color:blue; }
          </style>
        </head>
        <body>
          <h1>${cat.toUpperCase()}</h1>
          <div class="grid">${grid}</div>
          <p><a href="/">⬅ Back to Dice</a></p>
        </body>
      </html>
    `);
    });
});

// API endpoint for categories
app.get("/api/categories", (req, res) => {
    res.json(categories);
});

// Root route
app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "Public", "index.html"));
});

// Fallback 404
app.use((req, res) => {
    res.status(404).send("<h1>404 Not Found</h1><p>This path does not exist.</p>");
});

app.listen(PORT, () => {
    console.log(`✅ Server running at http://localhost:${PORT}`);
});
