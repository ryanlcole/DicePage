// ============================================================
// Shaelvien DiceMall Dynamic Server (v3.0)
// Author: Ryan L. Cole (ReLiC_GameMaster)
// ============================================================

const express = require("express");
const path = require("path");
const fs = require("fs");

const app = express();
const PORT = process.env.PORT || 3000;

// === Middleware ===
app.use(express.json());
app.use(express.static(path.join(__dirname, "Public")));

// === In-memory world object (auto-loaded from file if present) ===
let world = {
  version: 1,
  zones: [],
  updated: Date.now(),
};

// Load saved world state if exists
const savePath = path.join(__dirname, "world.json");
if (fs.existsSync(savePath)) {
  try {
    const data = JSON.parse(fs.readFileSync(savePath, "utf8"));
    world = data;
    console.log("🌍 Loaded saved world from world.json");
  } catch (err) {
    console.error("⚠️ Failed to parse world.json:", err);
  }
}

// === ROUTES ===

// Root route – serve the main page
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "Public", "index.html"));
});

// Get current world state
app.get("/api/world", (req, res) => {
  res.json(world);
});

// Add or update a zone
app.post("/api/zone", (req, res) => {
  const { id, element, energy } = req.body;
  if (!id) return res.status(400).json({ error: "Missing id" });

  const existing = world.zones.find((z) => z.id === id);
  if (existing) {
    Object.assign(existing, { element, energy });
  } else {
    world.zones.push({ id, element, energy });
  }
  world.updated = Date.now();
  res.json({ ok: true, zones: world.zones.length });
});

// Save the world to file
app.post("/api/save", (req, res) => {
  try {
    fs.writeFileSync(savePath, JSON.stringify(world, null, 2));
    world.updated = Date.now();
    res.json({ saved: true, time: world.updated });
  } catch (err) {
    res.status(500).json({ saved: false, error: err.message });
  }
});

// Load world from file
app.get("/api/load", (req, res) => {
  if (!fs.existsSync(savePath)) {
    return res.status(404).json({ error: "No saved world found" });
  }
  try {
    const data = JSON.parse(fs.readFileSync(savePath, "utf8"));
    world = data;
    res.json({ loaded: true, world });
  } catch (err) {
    res.status(500).json({ loaded: false, error: err.message });
  }
});

// === Server ===
app.listen(PORT, () => {
  console.log(`🔥 Shaelvien DiceMall running on port ${PORT}`);
  console.log(`➡️  Visit http://localhost:${PORT}/ or your Azure URL`);
});
