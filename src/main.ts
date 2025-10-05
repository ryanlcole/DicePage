import * as THREE from "three";
import { FontLoader } from "three/examples/jsm/loaders/FontLoader.js";
import { TextGeometry } from "three/examples/jsm/geometries/TextGeometry.js";

// Scene, Camera, Renderer
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 0, 6);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Lights
scene.add(new THREE.AmbientLight(0xffffff, 0.4));
const light = new THREE.PointLight(0xffffff, 1.2);
light.position.set(5, 5, 5);
scene.add(light);

// D20 Geometry
const d20 = new THREE.Mesh(
  new THREE.IcosahedronGeometry(1, 0),
  new THREE.MeshStandardMaterial({
    color: 0x888888,
    metalness: 0.7,
    roughness: 0.2
  })
);
scene.add(d20);

// Stars
const starGeo = new THREE.BufferGeometry();
const starCount = 1000;
const starPos = new Float32Array(starCount * 3);

for (let i = 0; i < starCount; i++) {
  starPos[i * 3] = (Math.random() - 0.5) * 200;
  starPos[i * 3 + 1] = (Math.random() - 0.5) * 200;
  starPos[i * 3 + 2] = (Math.random() - 0.5) * 200;
}
starGeo.setAttribute("position", new THREE.BufferAttribute(starPos, 3));

const stars = new THREE.Points(
  starGeo,
  new THREE.PointsMaterial({ color: 0xffffff, size: 0.6 })
);
scene.add(stars);

// Add Numbers
const loader = new FontLoader();
loader.load("https://threejs.org/examples/fonts/helvetiker_bold.typeface.json", (font) => {
  const numbers = Array.from({ length: 20 }, (_, i) => (i + 1).toString());
  const pos = d20.geometry.attributes.position;
  const index = d20.geometry.index!;
  const faceCount = index.count / 3;

  for (let i = 0; i < faceCount; i++) {
    const a = index.getX(i * 3);
    const b = index.getX(i * 3 + 1);
    const c = index.getX(i * 3 + 2);

    const vA = new THREE.Vector3().fromBufferAttribute(pos, a);
    const vB = new THREE.Vector3().fromBufferAttribute(pos, b);
    const vC = new THREE.Vector3().fromBufferAttribute(pos, c);

    const center = new THREE.Vector3().addVectors(vA, vB).add(vC).divideScalar(3);

    const textGeo = new TextGeometry(numbers[i % numbers.length], {
      font,
      size: 0.25,
      height: 0.05
    });
    const textMat = new THREE.MeshStandardMaterial({ color: 0xffcc00, emissive: 0x333300 });
    const textMesh = new THREE.Mesh(textGeo, textMat);

    textGeo.computeBoundingBox();
    const offset = textGeo.boundingBox!.getCenter(new THREE.Vector3()).multiplyScalar(-1);
    textMesh.position.copy(center).add(offset.multiplyScalar(0.01));
    textMesh.lookAt(center.clone().multiplyScalar(2));

    d20.add(textMesh);
  }
});

// Title Text
loader.load("https://threejs.org/examples/fonts/helvetiker_bold.typeface.json", (font) => {
  function makeTitle(text: string, y: number) {
    const geo = new TextGeometry(text, {
      font,
      size: 0.7,
      height: 0.1,
      bevelEnabled: true,
      bevelThickness: 0.02,
      bevelSize: 0.01,
      bevelSegments: 3
    });
    const mat = new THREE.MeshStandardMaterial({
      color: 0xcccccc,
      metalness: 1,
      roughness: 0.3
    });
    const mesh = new THREE.Mesh(geo, mat);
    geo.computeBoundingBox();
    mesh.position.set(-geo.boundingBox!.max.x / 2 * 0.01, y, -1);
    mesh.scale.set(0.01, 0.01, 0.01); // auto fit
    scene.add(mesh);
  }

  makeTitle("ReLiC", 2);
  makeTitle("GameMaster", -2);
});

// Animate
function animate() {
  requestAnimationFrame(animate);
  d20.rotation.y += 0.01;
  d20.rotation.x += 0.005;
  renderer.render(scene, camera);
}
animate();

// Resize
window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
