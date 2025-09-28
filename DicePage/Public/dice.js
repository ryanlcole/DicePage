// dice.js
let scene, camera, renderer, dice, raycaster, mouse;
let hoveredFace = null;

// 🔒 Fixed face → category mapping (20 total, matches products.json)
const lockedCategories = [
    "dice",
    "apparel",
    "stickers",
    "posters",
    "tote-bags",
    "jewelry",
    "3d-print-files",
    "cosplay",
    "mugs",
    "hoodies",
    "hats",
    "wall-art",
    "digital-downloads",
    "campaign-mods",
    "rpg-accessories",
    "music",
    "prints",
    "commissions",
    "maps",
    "bundles"
];

// --- Scene setup ---
scene = new THREE.Scene();
camera = new THREE.PerspectiveCamera(
    75,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
);

renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// --- Lighting ---
const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(5, 5, 5).normalize();
scene.add(light);

// --- D20 Dice Geometry ---
const geometry = new THREE.IcosahedronGeometry(2, 0); // 20 faces
const material = new THREE.MeshStandardMaterial({
    color: 0x0088ff,
    flatShading: true
});
dice = new THREE.Mesh(geometry, material);
scene.add(dice);

camera.position.z = 6;
raycaster = new THREE.Raycaster();
mouse = new THREE.Vector2();

// --- Tooltip ---
const tooltip = document.createElement("div");
tooltip.style.position = "absolute";
tooltip.style.padding = "6px 10px";
tooltip.style.background = "rgba(0,0,0,0.7)";
tooltip.style.color = "#fff";
tooltip.style.borderRadius = "4px";
tooltip.style.fontFamily = "Arial, sans-serif";
tooltip.style.fontSize = "14px";
tooltip.style.display = "none";
tooltip.style.pointerEvents = "none";
document.body.appendChild(tooltip);

// --- Featured Product Card ---
const featuredDiv = document.createElement("div");
featuredDiv.style.position = "absolute";
featuredDiv.style.bottom = "20px";
featuredDiv.style.left = "50%";
featuredDiv.style.transform = "translateX(-50%)";
featuredDiv.style.background = "rgba(255,255,255,0.9)";
featuredDiv.style.border = "1px solid #ccc";
featuredDiv.style.borderRadius = "8px";
featuredDiv.style.padding = "10px";
featuredDiv.style.fontFamily = "Arial, sans-serif";
featuredDiv.style.width = "200px";
featuredDiv.style.textAlign = "center";
featuredDiv.style.display = "none";
document.body.appendChild(featuredDiv);

// --- Cache of product data ---
let productCache = {};

// Fetch product data for a category
async function loadFeatured(category) {
    if (productCache[category]) {
        return productCache[category];
    }

    try {
        const res = await fetch(`/${category}`);
        const html = await res.text();

        // crude scrape of first product (works with server.js output)
        const match = html.match(/<div style=.*?<img src="(.*?)".*?<h3>(.*?)<\/h3>.*?\$(.*?)<\/p>/s);

        if (match) {
            const product = {
                image: match[1],
                name: match[2],
                price: match[3]
            };
            productCache[category] = product;
            return product;
        }
    } catch (err) {
        console.error("❌ Failed to load product for", category, err);
    }

    return null;
}

// --- Animate Dice ---
function animate() {
    requestAnimationFrame(animate);
    dice.rotation.x += 0.01;
    dice.rotation.y += 0.01;
    renderer.render(scene, camera);
}
animate();

// --- Hover Detection ---
document.addEventListener("mousemove", async (event) => {
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const hit = raycaster.intersectObject(dice)[0];

    if (hit) {
        hoveredFace = hit.faceIndex % 20; // always 0–19
        const category = lockedCategories[hoveredFace];

        // Tooltip at cursor
        tooltip.style.display = "block";
        tooltip.innerText = category;
        tooltip.style.left = event.clientX + 15 + "px";
        tooltip.style.top = event.clientY + 15 + "px";

        // Load featured product
        const product = await loadFeatured(category);
        if (product) {
            featuredDiv.style.display = "block";
            featuredDiv.innerHTML = `
        <img src="${product.image}" alt="${product.name}" style="max-width:100px; margin-bottom:10px;" />
        <h4>${product.name}</h4>
        <p>$${product.price}</p>
      `;
        }
    } else {
        hoveredFace = null;
        tooltip.style.display = "none";
        featuredDiv.style.display = "none";
    }
});

// --- Click Navigation ---
document.addEventListener("click", () => {
    if (hoveredFace !== null) {
        const category = lockedCategories[hoveredFace];
        console.log("Clicked face:", hoveredFace, "→", category);
        window.location.href = `/${category}`;
    }
});

// --- Resize Handling ---
window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
