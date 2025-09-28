// server.js
const express = require("express");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3000;

// Serve all static files from "Public" (JS, CSS, images, etc.)
app.use(express.static(path.join(__dirname, "Public")));

// Route: serve index.html for root
app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "Public", "index.html"));
});

// Start server
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
