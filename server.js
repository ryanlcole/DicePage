const express = require('express');
const path = require('path');
const app = express();

app.use(express.static(path.join(__dirname, 'Public')));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'Public', 'index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🔥 Shaelvien DiceMall running on port ${PORT}`));

// === Temporary in-memory world (for persistence test) ===
let world = { version: 1, zones: [], updated: Date.now() };

// API: get current world
app.get('/api/world', (req, res) => res.json(world));

// API: update or add a zone
app.post('/api/zone', express.json(), (req, res) => {
  const { id, element, energy } = req.body;
  const existing = world.zones.find(z => z.id === id);
  if (existing) Object.assign(existing, { element, energy });
  else world.zones.push({ id, element, energy });
  world.updated = Date.now();
  res.json({ ok: true });
});
