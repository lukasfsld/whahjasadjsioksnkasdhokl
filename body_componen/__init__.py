import { useEffect, useRef, useState, useCallback } from "react";
import * as THREE from "three";

// ============================================================
// Der Körper ist jetzt EINE durchgehende Oberfläche:
// Er wird als Signed-Distance-Field aus weich verschmolzenen
// Grundformen (Metaball-Prinzip) definiert und per Surface-Nets
// in ein einziges zusammenhängendes Mesh umgewandelt.
// Dadurch gibt es keinerlei Nähte, Spalten oder Übergänge mehr.
// ============================================================

// Weiche Vereinigung zweier Distanzen (Verschmelzungsradius k)
function smin(a, b, k) {
  const h = Math.min(Math.max(0.5 + 0.5 * (b - a) / k, 0), 1);
  return b * (1 - h) + a * h - k * h * (1 - h);
}

// Distanz zu einem Ellipsoid (gute Näherung)
function sdEll(px, py, pz, e) {
  const dx = (px - e.cx) / e.rx, dy = (py - e.cy) / e.ry, dz = (pz - e.cz) / e.rz;
  const k0 = Math.sqrt(dx * dx + dy * dy + dz * dz);
  const gx = dx / e.rx, gy = dy / e.ry, gz = dz / e.rz;
  const k1 = Math.sqrt(gx * gx + gy * gy + gz * gz);
  return k1 > 1e-9 ? (k0 * (k0 - 1)) / k1 : -Math.min(e.rx, e.ry, e.rz);
}

// Distanz zu einer Kapsel mit variablem Radius (Gliedmaßen)
function sdCap(px, py, pz, c) {
  const abx = c.bx - c.ax, aby = c.by - c.ay, abz = c.bz - c.az;
  const ab2 = abx * abx + aby * aby + abz * abz;
  let t = ((px - c.ax) * abx + (py - c.ay) * aby + (pz - c.az) * abz) / ab2;
  t = Math.min(Math.max(t, 0), 1);
  const qx = px - (c.ax + t * abx), qy = py - (c.ay + t * aby), qz = pz - (c.az + t * abz);
  return Math.sqrt(qx * qx + qy * qy + qz * qz) - (c.ra + (c.rb - c.ra) * t);
}

// ---------- Körperdefinition aus den Reglerwerten ----------

function makePrims(P) {
  const po = P.po, hu = P.hueften, ta = P.taille, sch = P.schultern;
  const os = P.oberschenkel, wa = P.waden, arm = P.arme, bauch = P.bauch;
  const br = P.brust, k = P.kopf;
  const neckTop = 1.425 + 0.085 * P.hals;
  const hx = 0.085 * Math.sqrt(hu);          // Beinabstand
  const shx = 0.150 * sch + 0.012;           // Schulteransatz

  const E = (cx, cy, cz, rx, ry, rz, blend = 0.045) =>
    ({ t: 0, cx, cy, cz, rx, ry, rz, blend });
  const C = (ax, ay, az, bx, by, bz, ra, rb, blend = 0.045) =>
    ({ t: 1, ax, ay, az, bx, by, bz, ra, rb, blend });

  const prims = [];

  // Becken & Rumpf
  prims.push(E(0, 0.86, 0, 0.150 * hu, 0.125, 0.100));                                   // Becken
  prims.push(E(0, 0.99, 0.015 + 0.04 * bauch, 0.108, 0.115, 0.068 + 0.05 * bauch));      // Bauch
  prims.push(E(0, 1.06, 0, 0.104 * ta, 0.10, 0.080 * ta));                               // Taille
  prims.push(E(0, 1.17, 0, 0.130, 0.125, 0.094));                                        // Brustkorb
  prims.push(E(0, 1.27, 0.004, 0.135, 0.085, 0.092));                                    // oberer Brustkorb
  prims.push(C(-0.145 * sch, 1.34, 0, 0.145 * sch, 1.34, 0, 0.052, 0.052));              // Schulterachse

  // Po – zwei große Halbkugeln, weich ins Becken und die Oberschenkel verschmolzen
  const gRx = 0.072 + 0.026 * (po - 1);
  const gRy = 0.074 + 0.032 * (po - 1);
  const gRz = 0.064 + 0.052 * (po - 1);
  const gZ = -(0.048 + 0.048 * (po - 1));
  for (const s of [-1, 1]) {
    prims.push(E(s * 0.057, 0.835, gZ, gRx, gRy, gRz, 0.06));
  }

  // Brust
  const bR = 0.036 + 0.033 * br;
  for (const s of [-1, 1]) {
    prims.push(E(s * (0.055 + 0.012 * br), 1.205, 0.048 + 0.028 * br, bR, bR * 0.94, bR * 0.78, 0.05));
  }

  // Hals & Kopf
  prims.push(C(0, 1.33, 0, 0, neckTop, 0.006, 0.051, 0.046));
  prims.push(E(0, neckTop + 0.07 * k, 0.012, 0.082 * k, 0.112 * k, 0.094 * k, 0.05));

  // Beine
  for (const s of [-1, 1]) {
    prims.push(C(s * hx, 0.85, 0, s * 0.082, 0.47, 0, 0.082 * os, 0.057, 0.06));         // Oberschenkel
    prims.push(C(s * 0.082, 0.47, 0, s * 0.084, 0.075, -0.012, 0.054, 0.034));           // Unterschenkel
    prims.push(E(s * 0.083, 0.33, -0.016, 0.048 * wa, 0.095, 0.058 * wa));               // Wade
    prims.push(E(s * 0.085, 0.035, 0.048, 0.044, 0.032, 0.108));                          // Fuß
  }

  // Arme
  for (const s of [-1, 1]) {
    prims.push(E(s * (shx + 0.006), 1.325, 0, 0.052 * arm, 0.058, 0.052 * arm, 0.055));  // Deltamuskel
    prims.push(C(s * (shx + 0.004), 1.32, 0, s * (shx + 0.018), 1.07, 0.005,
      0.046 * arm, 0.035 * arm, 0.05));                                                   // Oberarm
    prims.push(C(s * (shx + 0.018), 1.07, 0.005, s * (shx + 0.024), 0.80, 0.015,
      0.035 * arm, 0.025 * arm));                                                         // Unterarm
    prims.push(E(s * (shx + 0.025), 0.745, 0.02, 0.030, 0.052, 0.022));                   // Hand
  }

  return prims;
}

function evalBody(px, py, pz, prims) {
  let d = 1e9;
  for (let i = 0; i < prims.length; i++) {
    const p = prims[i];
    const di = p.t === 0 ? sdEll(px, py, pz, p) : sdCap(px, py, pz, p);
    d = smin(d, di, p.blend);
  }
  return d;
}

// ---------- Surface Nets: SDF -> ein zusammenhängendes Mesh ----------

const X0 = -0.38, Y0 = -0.02, Z0 = -0.34;
const STEP = 0.019;
const NX = 41, NY = 98, NZ = 37; // NX ungerade -> exakt spiegelsymmetrisch

function buildMesh(P, material) {
  const prims = makePrims(P);
  const field = new Float32Array(NX * NY * NZ);
  const fi = (x, y, z) => x + NX * (y + NY * z);
  const mid = (NX - 1) / 2;

  // Feld abtasten (nur rechte Hälfte rechnen, links spiegeln)
  for (let z = 0; z < NZ; z++) {
    const pz = Z0 + z * STEP;
    for (let y = 0; y < NY; y++) {
      const py = Y0 + y * STEP;
      for (let x = mid; x < NX; x++) {
        const v = evalBody(X0 + x * STEP, py, pz, prims);
        field[fi(x, y, z)] = v;
        field[fi(2 * mid - x, y, z)] = v;
      }
    }
  }

  // Zell-Vertices
  const ci = (x, y, z) => x + (NX - 1) * (y + (NY - 1) * z);
  const cellIdx = new Int32Array((NX - 1) * (NY - 1) * (NZ - 1)).fill(-1);
  const verts = [];
  const corners = [[0,0,0],[1,0,0],[0,1,0],[1,1,0],[0,0,1],[1,0,1],[0,1,1],[1,1,1]];
  const edges = [[0,1],[2,3],[4,5],[6,7],[0,2],[1,3],[4,6],[5,7],[0,4],[1,5],[2,6],[3,7]];
  const s8 = new Float32Array(8);

  for (let z = 0; z < NZ - 1; z++) {
    for (let y = 0; y < NY - 1; y++) {
      for (let x = 0; x < NX - 1; x++) {
        let mask = 0;
        for (let c = 0; c < 8; c++) {
          s8[c] = field[fi(x + corners[c][0], y + corners[c][1], z + corners[c][2])];
          if (s8[c] < 0) mask |= 1 << c;
        }
        if (mask === 0 || mask === 255) continue;
        let vx = 0, vy = 0, vz = 0, cnt = 0;
        for (let e = 0; e < 12; e++) {
          const a = edges[e][0], b = edges[e][1];
          if ((s8[a] < 0) !== (s8[b] < 0)) {
            const t = s8[a] / (s8[a] - s8[b]);
            vx += corners[a][0] + t * (corners[b][0] - corners[a][0]);
            vy += corners[a][1] + t * (corners[b][1] - corners[a][1]);
            vz += corners[a][2] + t * (corners[b][2] - corners[a][2]);
            cnt++;
          }
        }
        cellIdx[ci(x, y, z)] = verts.length / 3;
        verts.push(X0 + (x + vx / cnt) * STEP, Y0 + (y + vy / cnt) * STEP, Z0 + (z + vz / cnt) * STEP);
      }
    }
  }

  // Flächen über Vorzeichenwechsel an Gitterkanten
  const indices = [];
  const quad = (a, b, c, d, flip) => {
    if (a < 0 || b < 0 || c < 0 || d < 0) return;
    if (flip) indices.push(a, b, c, a, c, d);
    else indices.push(a, c, b, a, d, c);
  };
  for (let z = 0; z < NZ; z++) {
    for (let y = 0; y < NY; y++) {
      for (let x = 0; x < NX; x++) {
        const p = field[fi(x, y, z)];
        if (x < NX - 1 && y > 0 && y < NY - 1 && z > 0 && z < NZ - 1) {
          const q = field[fi(x + 1, y, z)];
          if ((p < 0) !== (q < 0))
            quad(cellIdx[ci(x, y - 1, z - 1)], cellIdx[ci(x, y, z - 1)],
                 cellIdx[ci(x, y, z)], cellIdx[ci(x, y - 1, z)], p < 0);
        }
        if (y < NY - 1 && x > 0 && x < NX - 1 && z > 0 && z < NZ - 1) {
          const q = field[fi(x, y + 1, z)];
          if ((p < 0) !== (q < 0))
            quad(cellIdx[ci(x - 1, y, z - 1)], cellIdx[ci(x - 1, y, z)],
                 cellIdx[ci(x, y, z)], cellIdx[ci(x, y, z - 1)], p < 0);
        }
        if (z < NZ - 1 && x > 0 && x < NX - 1 && y > 0 && y < NY - 1) {
          const q = field[fi(x, y, z + 1)];
          if ((p < 0) !== (q < 0))
            quad(cellIdx[ci(x - 1, y - 1, z)], cellIdx[ci(x, y - 1, z)],
                 cellIdx[ci(x, y, z)], cellIdx[ci(x - 1, y, z)], p < 0);
        }
      }
    }
  }

  // Normalen direkt aus dem Distanzfeld (immer korrekt nach außen)
  const normals = new Float32Array(verts.length);
  const eps = 0.008;
  for (let i = 0; i < verts.length; i += 3) {
    const x = verts[i], y = verts[i + 1], z = verts[i + 2];
    let nx = evalBody(x + eps, y, z, prims) - evalBody(x - eps, y, z, prims);
    let ny = evalBody(x, y + eps, z, prims) - evalBody(x, y - eps, z, prims);
    let nz = evalBody(x, y, z + eps, prims) - evalBody(x, y, z - eps, prims);
    const l = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;
    normals[i] = nx / l; normals[i + 1] = ny / l; normals[i + 2] = nz / l;
  }

  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(verts, 3));
  g.setAttribute("normal", new THREE.BufferAttribute(normals, 3));
  g.setIndex(indices);

  const mesh = new THREE.Mesh(g, material);
  const group = new THREE.Group();
  group.add(mesh);
  const s = P.groesse / 170;
  group.scale.set(s, s, s);
  return group;
}

// ---------- Regler ----------

const SLIDERS = [
  { key: "groesse",      label: "Körpergröße", min: 150, max: 195, step: 1, def: 170, unit: "cm" },
  { key: "kopf",         label: "Kopfgröße",   min: 0.85, max: 1.15, step: 0.01, def: 1 },
  { key: "hals",         label: "Halslänge",   min: 0.5,  max: 1.7,  step: 0.01, def: 1 },
  { key: "schultern",    label: "Schulterbreite", min: 0.75, max: 1.3, step: 0.01, def: 1 },
  { key: "brust",        label: "Brustgröße",  min: 0.2,  max: 2.0,  step: 0.01, def: 1 },
  { key: "taille",       label: "Taille",      min: 0.7,  max: 1.45, step: 0.01, def: 1 },
  { key: "bauch",        label: "Bauch",       min: 0,    max: 1.2,  step: 0.01, def: 0.15 },
  { key: "hueften",      label: "Hüftbreite",  min: 0.75, max: 1.45, step: 0.01, def: 1 },
  { key: "po",           label: "Po",          min: 0.6,  max: 2.4,  step: 0.01, def: 1 },
  { key: "oberschenkel", label: "Oberschenkel", min: 0.75, max: 1.45, step: 0.01, def: 1 },
  { key: "waden",        label: "Waden",       min: 0.75, max: 1.45, step: 0.01, def: 1 },
  { key: "arme",         label: "Arme",        min: 0.7,  max: 1.45, step: 0.01, def: 1 },
];

const defaults = () => Object.fromEntries(SLIDERS.map(s => [s.key, s.def]));

// ---------- Komponente ----------

export default function KoerperEditor() {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const bodyRef = useRef(null);
  const matRef = useRef(null);
  const rotRef = useRef({ y: 0.4, x: 0, auto: true });
  const timerRef = useRef(null);
  const [params, setParams] = useState(defaults);

  useEffect(() => {
    const mount = mountRef.current;
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x16171b);
    mount.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 50);
    camera.position.set(0, 0.96, 3.1);
    camera.lookAt(0, 0.92, 0);

    scene.add(new THREE.HemisphereLight(0xfff3e6, 0x33343c, 0.85));
    const key = new THREE.DirectionalLight(0xffffff, 0.85);
    key.position.set(2.2, 3.2, 2.6);
    scene.add(key);
    const rim = new THREE.DirectionalLight(0x9fb4ff, 0.45);
    rim.position.set(-2.5, 1.6, -2.4);
    scene.add(rim);

    const floor = new THREE.Mesh(
      new THREE.CircleGeometry(1.4, 48),
      new THREE.MeshStandardMaterial({ color: 0x232429, roughness: 0.95 })
    );
    floor.rotation.x = -Math.PI / 2;
    scene.add(floor);

    matRef.current = new THREE.MeshStandardMaterial({
      color: 0xd6a88c, roughness: 0.62, metalness: 0.02, side: THREE.DoubleSide,
    });

    let dragging = false, lx = 0, ly = 0;
    const onDown = (e) => { dragging = true; rotRef.current.auto = false; lx = e.clientX; ly = e.clientY; };
    const onMove = (e) => {
      if (!dragging) return;
      rotRef.current.y += (e.clientX - lx) * 0.01;
      rotRef.current.x = Math.max(-0.5, Math.min(0.5, rotRef.current.x + (e.clientY - ly) * 0.005));
      lx = e.clientX; ly = e.clientY;
    };
    const onUp = () => { dragging = false; };
    const onWheel = (e) => {
      e.preventDefault();
      camera.position.z = Math.max(1.6, Math.min(5.5, camera.position.z + e.deltaY * 0.0018));
    };
    renderer.domElement.addEventListener("pointerdown", onDown);
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    renderer.domElement.addEventListener("wheel", onWheel, { passive: false });
    renderer.domElement.style.cursor = "grab";
    renderer.domElement.style.touchAction = "none";

    const resize = () => {
      const w = mount.clientWidth, h = mount.clientHeight;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(mount);

    let raf;
    const loop = () => {
      raf = requestAnimationFrame(loop);
      if (rotRef.current.auto) rotRef.current.y += 0.004;
      const b = bodyRef.current;
      if (b) { b.rotation.y = rotRef.current.y; b.rotation.x = rotRef.current.x; }
      renderer.render(scene, camera);
    };
    loop();

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, []);

  // Neuaufbau (leicht entprellt, da das Feld berechnet werden muss)
  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      const scene = sceneRef.current;
      if (!scene || !matRef.current) return;
      if (bodyRef.current) {
        scene.remove(bodyRef.current);
        bodyRef.current.traverse((o) => { if (o.geometry) o.geometry.dispose(); });
      }
      const body = buildMesh(params, matRef.current);
      body.rotation.y = rotRef.current.y;
      body.rotation.x = rotRef.current.x;
      bodyRef.current = body;
      scene.add(body);
    }, 40);
  }, [params]);

  const set = useCallback((k, v) => setParams(p => ({ ...p, [k]: v })), []);

  return (
    <div style={{
      display: "flex", width: "100%", height: "100vh", minHeight: 560,
      background: "#16171b", color: "#e8e6e1",
      fontFamily: "'Avenir Next','Segoe UI',system-ui,sans-serif",
    }}>
      <div ref={mountRef} style={{ flex: 1, minWidth: 0, position: "relative" }}>
        <div style={{
          position: "absolute", left: 18, top: 16, pointerEvents: "none",
          fontSize: 12, letterSpacing: "0.18em", textTransform: "uppercase", color: "#8b8a93",
        }}>
          Ziehen = drehen · Scrollen = zoomen
        </div>
      </div>

      <div style={{
        width: 300, flexShrink: 0, overflowY: "auto",
        borderLeft: "1px solid #2b2c33", padding: "22px 22px 28px",
        background: "#1b1c21",
      }}>
        <div style={{ fontSize: 19, fontWeight: 600, letterSpacing: "-0.01em" }}>
          Körper-Editor
        </div>
        <div style={{ fontSize: 12.5, color: "#9a99a2", margin: "4px 0 18px" }}>
          Ein durchgehender Körper – Proportionen in Echtzeit
        </div>

        {SLIDERS.map((s) => (
          <label key={s.key} style={{ display: "block", marginBottom: 15 }}>
            <div style={{
              display: "flex", justifyContent: "space-between",
              fontSize: 13, marginBottom: 5,
            }}>
              <span>{s.label}</span>
              <span style={{ color: "#b9b7c0", fontVariantNumeric: "tabular-nums" }}>
                {s.unit ? `${params[s.key]} ${s.unit}` : `${Math.round(params[s.key] * 100)} %`}
              </span>
            </div>
            <input
              type="range"
              min={s.min} max={s.max} step={s.step}
              value={params[s.key]}
              onChange={(e) => set(s.key, parseFloat(e.target.value))}
              style={{ width: "100%", accentColor: "#d6a88c", cursor: "pointer" }}
            />
          </label>
        ))}

        <button
          onClick={() => setParams(defaults())}
          style={{
            width: "100%", marginTop: 6, padding: "9px 0",
            background: "transparent", color: "#d6a88c",
            border: "1px solid #d6a88c55", borderRadius: 8,
            fontSize: 13.5, cursor: "pointer",
          }}
        >
          Zurücksetzen
        </button>
      </div>
    </div>
  );
}
