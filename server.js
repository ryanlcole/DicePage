const express=require("express"); const path=require("path");
const app=express(); const PORT=process.env.PORT||3000;
app.use(express.json()); app.use(express.static(path.join(__dirname,"Public")));
app.get("/favicon.ico",(req,res)=>res.status(204).end());
let claims={}, products=[
  {id:"dice_apoth_001",name:"Moonpetal Elixir",mediaCount:6,shop:"apothecary"},
  {id:"dice_tavern_001",name:"Starlit Mead",mediaCount:6,shop:"tavern_inn"}
];
app.get("/",(req,res)=>res.sendFile(path.join(__dirname,"Public","index.html")));
app.get("/api/products",(req,res)=>res.json(products));
app.post("/api/item/claim",(req,res)=>{const {productId,sessionId}=req.body||{};
  if(!productId) return res.status(400).json({ok:false,error:"Missing productId"});
  if(claims[productId] && claims[productId].by && claims[productId].by!==sessionId)
    return res.json({ok:false,claimed:true,by:claims[productId].by});
  claims[productId]={by:sessionId||"anon",t:Date.now()}; res.json({ok:true,productId});
});
app.post("/api/item/release",(req,res)=>{const {productId,sessionId}=req.body||{};
  if(!productId) return res.status(400).json({ok:false,error:"Missing productId"});
  const c=claims[productId]; if(c && c.by && sessionId && c.by!==sessionId) return res.json({ok:false,error:"Not owner"});
  delete claims[productId]; res.json({ok:true,productId});
});
app.listen(PORT,()=>console.log(`🔥 Endemar server on ${PORT}`));

