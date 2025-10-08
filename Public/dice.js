import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js";
import { OrbitControls } from "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js";

const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById("d20"), antialias: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(devicePixelRatio);
renderer.setClearColor(0x000000);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.25;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, innerWidth/innerHeight, 0.1, 100);
camera.position.set(0, 0, 6);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.enablePan = false;
controls.minDistance = 3;
controls.maxDistance = 10;

// lights
const light1 = new THREE.PointLight(0xffffff, 2, 0);
light1.position.set(4, 3, 4);
const light2 = new THREE.PointLight(0x77ccff, 1, 0);
light2.position.set(-3, -2, -4);
scene.add(light1, light2);

// D20
const geo = new THREE.IcosahedronGeometry(1.5, 0);
const mat = new THREE.MeshPhysicalMaterial({
  metalness: 0,
  roughness: 0.05,
  transmission: 1,
  thickness: 0.35,
  ior: 2.45,
  envMapIntensity: 1.5,
  clearcoat: 1,
  clearcoatRoughness: 0.05,
  reflectivity: 0.9
});
const d20 = new THREE.Mesh(geo, mat);
scene.add(d20);

// animation
let t = 0;
function animate() {
  requestAnimationFrame(animate);
  t += 0.01;
  d20.rotation.x += 0.0015;
  d20.rotation.y += 0.002;
  controls.update();
  renderer.render(scene, camera);
}
animate();

addEventListener("resize", () => {
  camera.aspect = innerWidth/innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

