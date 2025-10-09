// ============================================================
// Endemar Server – Phase 1
// - Serves /Public
// - Basic world/session endpoints
// - Product claim/release placeholders
// ============================================================
const express = require("express");
const path = require("path");
const fs = require("fs");

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, "Public")));
app.get("/favicon.ico", (req,res)=>res.status(204).end());

// --- In-memory state ---
let sessions = {};
let claims = {};   // productId -> { by: sessionId, t: ms }
let products = [
  // Phase 2 will load real inventory here (dice per product)
  { id:"dice_apoth_001", name:"Moonpetal Elixir", mediaCount:6, shop:"apothecary" },
  { id:"dice_tavern_001", name:"Starlit Mead", mediaCount:6, shop:"tavern_inn" },
  { id:"dice_arm_001",    name:"Star-Forge Blade Tee", mediaCount:8, shop:"armory" },
  { id:"dice_curio_001",  name:"Oracle’s Charm", mediaCount:10, shop:"curio" }
];

// --- API: session start (very basic) ---
app.post("/api/session/start", (req,res)=>{
  const id = `${Date.now().toString(36)}_${Math.random().toString(36).slice(2,8)}`;
  sessions[id] = { id, started: Date.now(), cart: [] };
  res.json({ ok:true, id });
});

// --- API: list products (Phase 2: filter by shop/nearby) ---
app.get("/api/products", (req,res)=>{
  res.json(products);
});

// --- API: claim / release dice (exclusive interaction) ---
app.post("/api/item/claim", (req,res)=>{
  const { productId, sessionId } = req.body || {};
  if(!productId) return res.status(400).json({ ok:false, error:"Missing productId" });
  if(claims[productId] && claims[productId].by && claims[productId].by !== sessionId){
    return res.json({ ok:false, claimed:true, by: claims[productId].by });
  }
  claims[productId] = { by: sessionId || "anon", t: Date.now() };
  res.json({ ok:true, productId });
});
app.post("/api/item/release", (req,res)=>{
  const { productId, sessionId } = req.body || {};
  if(!productId) return res.status(400).json({ ok:false, error:"Missing productId" });
  const c = claims[productId];
  if(c && c.by && sessionId && c.by !== sessionId){
    return res.json({ ok:false, error:"Not owner" });
  }
  delete claims[productId];
  res.json({ ok:true, productId });
});

// --- Root ---
app.get("/", (req,res)=>{
  res.sendFile(path.join(__dirname, "Public", "index.html"));
});

// --- Start ---
app.listen(PORT, ()=> {
  console.log(`🔥 Endemar server running on port ${PORT}`);
});
