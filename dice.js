import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js";
import { OrbitControls } from "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js";

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Galaxy background
const starGeo = new THREE.BufferGeometry();
const starCount = 2000;
const starPositions = new Float32Array(starCount * 3);
for (let i = 0; i < starCount * 3; i++) {
  starPositions[i] = (Math.random() - 0.5) * 2000;
}
starGeo.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
const starMat = new THREE.PointsMaterial({ color: 0xffffff, size: 0.7 });
const stars = new THREE.Points(starGeo, starMat);
scene.add(stars);

// D20 geometry
const geometry = new THREE.IcosahedronGeometry(1.5, 0);
const material = new THREE.MeshPhysicalMaterial({
  color: 0x88aaff,
  roughness: 0.15,
  metalness: 0.2,
  reflectivity: 0.9,
  transmission: 0.6,
  ior: 1.8,
  thickness: 0.8,
  clearcoat: 1,
  clearcoatRoughness: 0.05,
  envMapIntensity: 1.5
});
const d20 = new THREE.Mesh(geometry, material);
scene.add(d20);

// Lights
const light1 = new THREE.PointLight(0xffffff, 1.4);
light1.position.set(5, 3, 5);
scene.add(light1);
const light2 = new THREE.PointLight(0x88aaff, 0.6);
light2.position.set(-5, -3, -4);
scene.add(light2);
scene.add(new THREE.AmbientLight(0x202020));

camera.position.z = 5;

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.enablePan = false;
controls.minDistance = 3;
controls.maxDistance = 10;

function animate() {
  requestAnimationFrame(animate);
  stars.rotation.y += 0.0005;
  d20.rotation.y += 0.005;
  d20.rotation.x += 0.002;
  controls.update();
  renderer.render(scene, camera);
}
animate();

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
