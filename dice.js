import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js";
import { OrbitControls } from "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js";

let scene, camera, renderer, controls, d20, banner;
const categories = [
  "TTRPG", "Anime", "Retro", "Cosplay", "Fantasy",
  "Music", "Sci-Fi", "Art", "Indie", "Guilds",
  "Lore", "Tools", "Events", "Shops", "Creators",
  "Magic", "Dice", "Streams", "Games", "Worlds"
];

init();
animate();

function init() {
  banner = document.getElementById("banner");

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.z = 4;

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  document.body.appendChild(renderer.domElement);

  const geometry = new THREE.IcosahedronGeometry(1, 0);
  const material = new THREE.MeshStandardMaterial({
    color: 0x6699ff,
    metalness: 0.6,
    roughness: 0.2,
  });
  d20 = new THREE.Mesh(geometry, material);
  scene.add(d20);

  const light = new THREE.PointLight(0xffffff, 2);
  light.position.set(5, 5, 5);
  scene.add(light);
  scene.add(new THREE.AmbientLight(0x404040));

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 2.0;

  window.addEventListener("resize", onWindowResize);
  window.addEventListener("click", lockDie);
}

function lockDie() {
  controls.autoRotate = false;
  const category = categories[Math.floor(Math.random() * categories.length)];
  banner.textContent = category + " ✨";
  banner.style.opacity = 1;
  setTimeout(() => (banner.style.opacity = 0), 4000);
}

function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}
