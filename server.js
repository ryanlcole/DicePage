// ============================================================
// Shaelvien DiceMall Dynamic Server v3.1 (Express)
// Serves /Public, REST API for world state, favicon handler
// ============================================================
const express = require("express");
const path = require("path");
const fs = require("fs");

const app = express();
const PORT = process.env.PORT || 3000;

// --- middleware ---
app.use(express.json());
app.use(express.static(path.join(__dirname, "Public")));

// --- favicon handler (silences stray requests if any) ---
app.get("/favicon.ico", (req, res) => res.status(204).end());

// --- in-memory world (persists via world.json) ---
let world = { version: 1, zones: [], updated: Date.now() };
const savePath = path.join(__dirname, "world.json");
if (fs.existsSync(savePath)) {
  try {
    world = JSON.parse(fs.readFileSync(savePath, "utf8"));
    console.log("🌍 Loaded saved world.json");
  } catch (e) {
    console.warn("⚠️ Failed to parse world.json:", e.message);
  }
}

// --- routes ---
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "Public", "index.html"));
});

app.get("/api/world", (req, res) => {
  res.json(world);
});

app.post("/api/zone", (req, res) => {
  const { id, element, energy } = req.body || {};
  if (!id) return res.status(400).json({ error: "Missing id" });
  const z = world.zones.find((v) => v.id === id);
  if (z) Object.assign(z, { element, energy });
  else world.zones.push({ id, element, energy });
  world.updated = Date.now();
  res.json({ ok: true, zones: world.zones.length });
});

app.post("/api/save", (req, res) => {
  try {
    fs.writeFileSync(savePath, JSON.stringify(world, null, 2));
    world.updated = Date.now();
    res.json({ saved: true, time: world.updated });
  } catch (e) {
    res.status(500).json({ saved: false, error: e.message });
  }
});

app.get("/api/load", (req, res) => {
  if (!fs.existsSync(savePath)) {
    return res.status(404).json({ error: "No saved world found" });
  }
  try {
    world = JSON.parse(fs.readFileSync(savePath, "utf8"));
    res.json({ loaded: true, world });
  } catch (e) {
    res.status(500).json({ loaded: false, error: e.message });
  }
});

// --- start ---
app.listen(PORT, () => {
  console.log(`🔥 Shaelvien DiceMall running on port ${PORT}`);
});

