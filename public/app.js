// SmartFlow GreenCorridor AI - Nagpur Arterial Emergency Corridor Engine
// High-Fidelity Physics-Based Traffic Simulation & Emergency Preemption Visualizer

const API_BASE = window.location.origin;

// Constants & Geometry
const NODE_KEYS = ["NODE_1_SITABULDI", "NODE_2_MEDICAL_SQ", "NODE_3_WARDHA_RD", "NODE_4_AIIMS_GMC"];
const NODE_X_RATIO = [0.13, 0.38, 0.63, 0.88]; // Balanced node positions
const NODE_NAMES = ["1. Sitabuldi Interchange", "2. Medical Square", "3. Wardha Road Viaduct", "4. AIIMS / GMC Hospital"];
const VEHICLE_TYPES = ["auto", "car", "cab", "bus", "bike"];
const MAX_CONSOLE_ENTRIES = 200;

// State
let isRunning = false;
let simInterval = null;
let simSpeed = 1.0;
let surgeRate = 0.3;
let lastFrameTime = performance.now();
let frameCount = 0;
let currentFps = 60;

let gridState = {
  time: 0.0,
  nodes: {},
  active_emergencies: [],
  active_preemption: false,
  avg_delay_reduction_pct: 71.6,
  lives_assisted: 0
};

// Canvas
const canvas = document.getElementById("corridorCanvas");
const ctx = canvas.getContext("2d");

// Vehicle State Arrays with physics
let corridorVehicles = [];   // Horizontal Highway traffic
let crossVehicles = [];      // Vertical Cross-Street traffic

// DOM Elements
const btnPlayPause = document.getElementById("btnPlayPause");
const playPauseText = document.getElementById("playPauseText");
const btnStep = document.getElementById("btnStep");
const btnReset = document.getElementById("btnReset");
const btnDispatchAmbulance = document.getElementById("btnDispatchAmbulance");
const btnDispatchFire = document.getElementById("btnDispatchFire");
const btnRunAllTests = document.getElementById("btnRunAllTests");
const speedSlider = document.getElementById("simSpeed");
const speedValue = document.getElementById("speedValue");
const surgeSlider = document.getElementById("trafficSurgeRate");
const surgeRateLabel = document.getElementById("surgeRateLabel");
const timeSavedVal = document.getElementById("timeSavedVal");
const activeEmgVal = document.getElementById("activeEmgVal");
const activeEmgSub = document.getElementById("activeEmgSub");
const greenWaveVal = document.getElementById("greenWaveVal");
const livesVal = document.getElementById("livesVal");
const corridorStatusPill = document.getElementById("corridorStatusPill");
const corridorStatusText = document.getElementById("corridorStatusText");
const ttiVal = document.getElementById("ttiVal");
const consoleLogs = document.getElementById("consoleLogs");
const fpsDisplay = document.getElementById("fpsDisplay");

// ─── Initialize ───
window.addEventListener("DOMContentLoaded", () => {
  setupCanvas();
  setupEventListeners();
  initTrafficFleet();
  fetchStatus();
  requestAnimationFrame(renderLoop);
});

function setupCanvas() {
  const resize = () => {
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(rect.width * dpr);
    canvas.height = Math.round(rect.height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  };
  if (typeof ResizeObserver !== "undefined") {
    new ResizeObserver(resize).observe(canvas);
  } else {
    resize();
    window.addEventListener("resize", resize);
  }
}

function setupEventListeners() {
  btnPlayPause.addEventListener("click", toggleSimulation);
  btnStep.addEventListener("click", () => stepSimulation(1.0));
  btnReset.addEventListener("click", resetSimulation);
  btnDispatchAmbulance.addEventListener("click", () => dispatchEmergency("ambulance", 1));
  btnDispatchFire.addEventListener("click", () => dispatchEmergency("fire_engine", 2));
  btnRunAllTests.addEventListener("click", runAutomatedTestSuite);

  speedSlider.addEventListener("input", (e) => {
    simSpeed = parseFloat(e.target.value);
    speedValue.innerText = `${simSpeed.toFixed(1)}x`;
    if (isRunning) restartInterval();
  });

  surgeSlider.addEventListener("input", (e) => {
    surgeRate = parseFloat(e.target.value);
    surgeRateLabel.innerText = `${surgeRate.toFixed(1)}/s`;
    fetch(`${API_BASE}/api/grid/set_surge`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ surge_rate: surgeRate })
    });
  });
}

// ─── Traffic Population & Safe Spacing ───
function initTrafficFleet() {
  corridorVehicles = [];
  crossVehicles = [];

  // 1. Horizontal Corridor Traffic: Left-Hand Traffic (LHT)
  // Eastbound (towards AIIMS hospital) = Bottom Half (Lanes 0 and 1)
  // Westbound (away from AIIMS) = Top Half (Lanes 2 and 3)
  const corridorLanes = [
    { dir: "east", laneId: 0, targetYOffset: 12, maxSpeed: 1.2 },
    { dir: "east", laneId: 1, targetYOffset: 32, maxSpeed: 1.0 },
    { dir: "west", laneId: 2, targetYOffset: -12, maxSpeed: 1.2 },
    { dir: "west", laneId: 3, targetYOffset: -32, maxSpeed: 1.0 }
  ];

  corridorLanes.forEach(lane => {
    // Spawn 3-4 vehicles per lane with at least 180px initial spacing (ZERO overlapping spawn)
    for (let i = 0; i < 4; i++) {
      const initX = i * 240 + Math.random() * 60;
      corridorVehicles.push({
        id: Math.random(),
        type: VEHICLE_TYPES[Math.floor(Math.random() * VEHICLE_TYPES.length)],
        dir: lane.dir,
        laneId: lane.laneId,
        x: lane.dir === "east" ? initX : (960 - initX),
        yOffset: lane.targetYOffset,
        targetYOffset: lane.targetYOffset,
        speed: lane.maxSpeed * (0.85 + Math.random() * 0.3),
        maxSpeed: lane.maxSpeed * (0.85 + Math.random() * 0.3),
        currentSpeed: 0,
        length: 26,
        width: 14,
        isYielding: false
      });
    }
  });

  // 2. Vertical Cross-Street Traffic for each of the 4 nodes
  // Left side going down, Right side going up (LHT)
  for (let nodeIdx = 0; nodeIdx < 4; nodeIdx++) {
    // Southbound (Going Down, left side of cross street)
    for (let i = 0; i < 2; i++) {
      crossVehicles.push({
        id: Math.random(),
        nodeIdx: nodeIdx,
        dir: "south",
        laneXOffset: -16,
        y: i * 180 + Math.random() * 40,
        speed: 0.8 + Math.random() * 0.4,
        maxSpeed: 0.8 + Math.random() * 0.4,
        currentSpeed: 0.8,
        length: 22,
        width: 13,
        stopped: false
      });
    }

    // Northbound (Going Up, right side of cross street)
    for (let i = 0; i < 2; i++) {
      crossVehicles.push({
        id: Math.random(),
        nodeIdx: nodeIdx,
        dir: "north",
        laneXOffset: 16,
        y: 420 - (i * 180 + Math.random() * 40),
        speed: 0.8 + Math.random() * 0.4,
        maxSpeed: 0.8 + Math.random() * 0.4,
        currentSpeed: 0.8,
        length: 22,
        width: 13,
        stopped: false
      });
    }
  }
}

// ─── Main Render Loop ───
function renderLoop(ts) {
  frameCount++;
  if (ts - lastFrameTime >= 1000) {
    currentFps = Math.round((frameCount * 1000) / (ts - lastFrameTime));
    if (fpsDisplay) fpsDisplay.innerText = `${currentFps} FPS`;
    frameCount = 0;
    lastFrameTime = ts;
  }
  updatePhysicsAndDraw();
  requestAnimationFrame(renderLoop);
}

// ─── Physics Simulation & Visual Rendering ───
function updatePhysicsAndDraw() {
  const rect = canvas.getBoundingClientRect();
  const W = rect.width;
  const H = rect.height;
  const CY = H / 2;
  const roadH = H * 0.28;
  const crossW = W * 0.088;
  const nodeX = NODE_X_RATIO.map(r => r * W);

  // Clear Canvas
  ctx.fillStyle = "#070b12";
  ctx.fillRect(0, 0, W, H);

  // Background Ground (Cyber City Grid)
  drawBackgroundCityGrid(W, H, CY, roadH, nodeX, crossW);

  // Draw Vertical Cross Streets
  nodeX.forEach((nx, idx) => {
    // Cross road asphalt
    ctx.fillStyle = "#121929";
    ctx.fillRect(nx - crossW / 2, 0, crossW, H);

    // Cross Street Center Divider
    ctx.strokeStyle = "rgba(255,255,255,0.15)";
    ctx.setLineDash([5, 7]);
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(nx, 0);
    ctx.lineTo(nx, H);
    ctx.stroke();
    ctx.setLineDash([]);

    // Curbs
    ctx.strokeStyle = "rgba(0, 242, 254, 0.12)";
    ctx.lineWidth = 1;
    ctx.strokeRect(nx - crossW / 2, 0, crossW, H);
  });

  // Draw Main Horizontal Highway Corridor
  ctx.fillStyle = "#162035";
  ctx.fillRect(0, CY - roadH / 2, W, roadH);

  // Highway Glowing Curbs (Cyan Glow)
  ctx.strokeStyle = "rgba(0, 242, 254, 0.4)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0, CY - roadH / 2);
  ctx.lineTo(W, CY - roadH / 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(0, CY + roadH / 2);
  ctx.lineTo(W, CY + roadH / 2);
  ctx.stroke();

  // Highway Center Divider (Yellow Solid/Dashed)
  ctx.strokeStyle = "rgba(250, 204, 21, 0.4)";
  ctx.setLineDash([14, 10]);
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0, CY);
  ctx.lineTo(W, CY);
  ctx.stroke();
  ctx.setLineDash([]);

  // Sub-lane Guideline dashes
  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
  ctx.setLineDash([6, 12]);
  ctx.lineWidth = 1;
  [CY - roadH * 0.25, CY + roadH * 0.25].forEach(y => {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(W, y);
    ctx.stroke();
  });
  ctx.setLineDash([]);

  // Draw Intersection Signals, Crosswalks, and Status HUD
  nodeX.forEach((nx, idx) => {
    const nodeData = gridState.nodes ? gridState.nodes[NODE_KEYS[idx]] : null;
    const isCorridorGreen = nodeData ? (nodeData.phase === "MAIN_CORRIDOR" || nodeData.is_preempted) : true;
    const isCrossGreen = nodeData ? (nodeData.phase === "CROSS_STREET" && !nodeData.is_preempted) : false;
    const isPreempted = nodeData ? nodeData.is_preempted : false;

    // Crosswalks
    drawCrosswalk(nx - crossW / 2, CY - roadH / 2 - 8, crossW, 6);
    drawCrosswalk(nx - crossW / 2, CY + roadH / 2 + 2, crossW, 6);

    // Stop lines on Cross Streets
    ctx.fillStyle = isCrossGreen ? "rgba(16, 185, 129, 0.5)" : "rgba(244, 63, 94, 0.7)";
    ctx.fillRect(nx - crossW / 2, CY - roadH / 2 - 2, crossW / 2 - 2, 3); // top southbound stop bar
    ctx.fillRect(nx + 2, CY + roadH / 2 - 1, crossW / 2 - 2, 3);          // bottom northbound stop bar

    // Stop lines on Main Corridor
    if (!isCorridorGreen) {
      ctx.fillStyle = "rgba(244, 63, 94, 0.7)";
      ctx.fillRect(nx - crossW / 2 - 3, CY, 3, roadH / 2); // eastbound stop line
      ctx.fillRect(nx + crossW / 2, CY - roadH / 2, 3, roadH / 2); // westbound stop line
    }

    // Traffic Signals
    drawSignal(nx + crossW / 2 + 5, CY - roadH / 2 - 22, isCorridorGreen, isPreempted);
    drawSignal(nx - crossW / 2 - 22, CY + roadH / 2 + 4, isCorridorGreen, isPreempted);
    drawSignal(nx + crossW / 2 + 5, CY + roadH / 2 + 4, isCrossGreen, false);
    drawSignal(nx - crossW / 2 - 22, CY - roadH / 2 - 22, isCrossGreen, false);

    // Landmark Name Label
    ctx.fillStyle = isPreempted ? "#f43f5e" : "#38bdf8";
    ctx.font = `bold ${Math.max(9, W * 0.0105)}px Plus Jakarta Sans`;
    ctx.textAlign = "center";
    ctx.fillText(NODE_NAMES[idx], nx, CY - roadH / 2 - 28);
  });

  // Draw AIIMS ER Building with Helipad
  drawHospitalBuilding(nodeX[3] + crossW / 2 + 10, 15);

  // Active Emergency Vehicle Telemetry
  const activeEV = gridState.active_emergencies
    ? gridState.active_emergencies.find(e => e.status === "in_transit" || e.status === "dispatched")
    : null;

  let evX = null;
  if (activeEV) {
    const corridorStart = nodeX[0] - 40;
    const corridorEnd = nodeX[3] + 40;
    evX = corridorStart + (activeEV.pos_progress / 100) * (corridorEnd - corridorStart);

    // Glowing Green Wave Beam ahead of ambulance (both lanes for full-width impact)
    const beamLen = Math.min(corridorEnd - evX, W * 0.35);
    if (beamLen > 0) {
      const grad = ctx.createLinearGradient(evX, CY, evX + beamLen, CY);
      grad.addColorStop(0, "rgba(16, 185, 129, 0.45)");
      grad.addColorStop(1, "rgba(16, 185, 129, 0.0)");
      ctx.fillStyle = grad;
      ctx.fillRect(evX, CY - roadH / 2, beamLen, roadH);
    }

    // Dynamic Siren Wave Pulses
    drawSirenWaves(evX, CY + roadH * 0.2);
  }

  // ─── 1. Cross-Street Vehicle Physics (Zero Overlap Queuing) ───
  crossVehicles.forEach((veh, vIdx) => {
    const nx = nodeX[veh.nodeIdx];
    const nodeData = gridState.nodes ? gridState.nodes[NODE_KEYS[veh.nodeIdx]] : null;
    const isCrossGreen = nodeData ? (nodeData.phase === "CROSS_STREET" && !nodeData.is_preempted) : false;

    const stopLineY = veh.dir === "south" ? (CY - roadH / 2 - 12) : (CY + roadH / 2 + 12);
    let targetSpeed = veh.maxSpeed;

    // Check if there is another vehicle ahead of this one in the same direction
    let distToLead = 999;
    crossVehicles.forEach((other, oIdx) => {
      if (vIdx === oIdx || other.nodeIdx !== veh.nodeIdx || other.dir !== veh.dir) return;
      if (veh.dir === "south" && other.y > veh.y) {
        distToLead = Math.min(distToLead, other.y - veh.y);
      } else if (veh.dir === "north" && other.y < veh.y) {
        distToLead = Math.min(distToLead, veh.y - other.y);
      }
    });

    // Stop line check
    let distToStop = 999;
    if (veh.dir === "south") {
      if (!isCrossGreen && veh.y < stopLineY) {
        distToStop = stopLineY - veh.y;
      }
    } else {
      if (!isCrossGreen && veh.y > stopLineY) {
        distToStop = veh.y - stopLineY;
      }
    }

    // Car-following & Queue physics: If close to lead vehicle or stop line, decelerate/stop!
    const effectiveStopDist = Math.min(distToLead - 28, distToStop);

    if (effectiveStopDist < 8) {
      targetSpeed = 0; // Complete stop in queue
    } else if (effectiveStopDist < 35) {
      targetSpeed = veh.maxSpeed * (effectiveStopDist / 35); // Smooth braking
    }

    // Apply speed
    veh.currentSpeed = targetSpeed;
    if (veh.dir === "south") {
      veh.y += veh.currentSpeed;
      if (veh.y > H + 40) veh.y = -40; // wrap around
      drawCivilianVehicle(nx + veh.laneXOffset, veh.y, Math.PI / 2, veh.type);
    } else {
      veh.y -= veh.currentSpeed;
      if (veh.y < -40) veh.y = H + 40; // wrap around
      drawCivilianVehicle(nx + veh.laneXOffset, veh.y, -Math.PI / 2, veh.type);
    }
  });

  // ─── 2. Main Corridor Vehicle Physics (No Overlap + Ambulance Yielding) ───
  corridorVehicles.forEach((veh, vIdx) => {
    let targetSpeed = veh.maxSpeed;

    // Check collision distance to lead vehicle in the same lane
    let distToLead = 999;
    corridorVehicles.forEach((other, oIdx) => {
      if (vIdx === oIdx || other.laneId !== veh.laneId) return;
      if (veh.dir === "east") {
        let d = other.x - veh.x;
        if (d < 0) d += (W + 80); // account for wrap-around
        distToLead = Math.min(distToLead, d);
      } else {
        let d = veh.x - other.x;
        if (d < 0) d += (W + 80);
        distToLead = Math.min(distToLead, d);
      }
    });

    // Check Red signal at next intersection ahead
    let distToSignalStop = 999;
    nodeX.forEach((nx, idx) => {
      const nodeData = gridState.nodes ? gridState.nodes[NODE_KEYS[idx]] : null;
      const isCorridorGreen = nodeData ? (nodeData.phase === "MAIN_CORRIDOR" || nodeData.is_preempted) : true;
      if (!isCorridorGreen) {
        if (veh.dir === "east" && veh.x < (nx - crossW / 2 - 10)) {
          distToSignalStop = Math.min(distToSignalStop, (nx - crossW / 2 - 10) - veh.x);
        } else if (veh.dir === "west" && veh.x > (nx + crossW / 2 + 10)) {
          distToSignalStop = Math.min(distToSignalStop, veh.x - (nx + crossW / 2 + 10));
        }
      }
    });

    // Yield to approaching Ambulance: Pull over to shoulder!
    if (activeEV && evX !== null && veh.dir === "east") {
      const distBehindAmbulance = veh.x - evX;
      // If car is ahead of ambulance within 180px, pull over to shoulder (Y offset shifts down)
      if (distBehindAmbulance > -15 && distBehindAmbulance < 220) {
        veh.targetYOffset = 34; // pull to edge
        targetSpeed = veh.maxSpeed * 0.45; // slow down for safe clearance
      } else {
        veh.targetYOffset = veh.laneId === 0 ? 12 : 30;
      }
    }

    // Smooth lane offset interpolation (yielding movement)
    veh.yOffset += (veh.targetYOffset - veh.yOffset) * 0.08;

    // Apply safe-braking distance logic
    const effectiveStopDist = Math.min(distToLead - 34, distToSignalStop);
    if (effectiveStopDist < 8) {
      targetSpeed = 0;
    } else if (effectiveStopDist < 45) {
      targetSpeed = veh.maxSpeed * (effectiveStopDist / 45);
    }

    veh.currentSpeed = targetSpeed;

    // Advance position
    if (veh.dir === "east") {
      veh.x += veh.currentSpeed;
      if (veh.x > W + 40) veh.x = -40;
      drawCivilianVehicle(veh.x, CY + veh.yOffset, 0, veh.type);
    } else {
      veh.x -= veh.currentSpeed;
      if (veh.x < -40) veh.x = W + 40;
      drawCivilianVehicle(veh.x, CY + veh.yOffset, Math.PI, veh.type);
    }
  });

  // ─── 3. Draw Emergency Vehicle (Ambulance / Fire Engine) ───
  if (activeEV && evX !== null) {
    drawEmergencyVehicle(evX, CY + 14, activeEV.vehicle_type);
  }
}

// ─── Drawing Components & Vehicle Sprites ───

function drawBackgroundCityGrid(W, H, CY, roadH, nodeX, crossW) {
  // Decorative Building Blocks with glowing windows
  ctx.fillStyle = "rgba(14, 21, 37, 0.7)";
  ctx.fillRect(0, 0, W, CY - roadH / 2 - 2);
  ctx.fillRect(0, CY + roadH / 2 + 2, W, H - (CY + roadH / 2));

  // City Block Grid Lines
  ctx.strokeStyle = "rgba(56, 189, 248, 0.04)";
  ctx.lineWidth = 1;
  for (let x = 20; x < W; x += 40) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, CY - roadH / 2 - 5);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x, CY + roadH / 2 + 5);
    ctx.lineTo(x, H);
    ctx.stroke();
  }
}

function drawCrosswalk(x, y, w, h) {
  ctx.fillStyle = "rgba(255, 255, 255, 0.15)";
  const stripes = 6;
  const sw = w / (stripes * 2);
  for (let i = 0; i < stripes * 2; i += 2) {
    ctx.fillRect(x + i * sw, y, sw, h);
  }
}

function drawSignal(x, y, isGreen, isPreempted) {
  // Signal housing box
  ctx.fillStyle = "#0a0e18";
  ctx.strokeStyle = isPreempted ? "#f43f5e" : "rgba(255, 255, 255, 0.18)";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.roundRect(x, y, 18, 18, 4);
  ctx.fill();
  ctx.stroke();

  // LED Signal Light
  const color = isGreen ? "#10b981" : "#f43f5e";
  ctx.fillStyle = color;
  ctx.shadowColor = color;
  ctx.shadowBlur = isPreempted ? 16 : 8;
  ctx.beginPath();
  ctx.arc(x + 9, y + 9, 5, 0, Math.PI * 2);
  ctx.fill();
  ctx.shadowBlur = 0;
}

function drawHospitalBuilding(x, y) {
  // AIIMS ER Bay Building
  ctx.fillStyle = "#0d1527";
  ctx.strokeStyle = "rgba(244, 63, 94, 0.5)";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.roundRect(x, y, 68, 44, 6);
  ctx.fill();
  ctx.stroke();

  // Red Cross Icon
  ctx.fillStyle = "#f43f5e";
  ctx.fillRect(x + 29, y + 8, 10, 22);
  ctx.fillRect(x + 23, y + 14, 22, 10);

  // Label
  ctx.fillStyle = "#f8fafc";
  ctx.font = "bold 8px Plus Jakarta Sans";
  ctx.textAlign = "center";
  ctx.fillText("AIIMS ER BAY", x + 34, y + 38);
}

function drawCivilianVehicle(x, y, angle, type) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);

  // Drop Shadow
  ctx.fillStyle = "rgba(0, 0, 0, 0.4)";
  ctx.fillRect(-11, -6, 22, 12);

  if (type === "auto") {
    // 🛺 Nagpur Auto-rickshaw (Green CNG chassis with Yellow Hood)
    ctx.fillStyle = "#15803d";
    ctx.beginPath();
    ctx.roundRect(-9, -5, 18, 10, 3);
    ctx.fill();
    ctx.fillStyle = "#facc15";
    ctx.beginPath();
    ctx.roundRect(-7, -4, 11, 8, 2);
    ctx.fill();
  } else if (type === "bus") {
    // 🚌 Red City Bus
    ctx.fillStyle = "#dc2626";
    ctx.beginPath();
    ctx.roundRect(-16, -7, 32, 14, 3);
    ctx.fill();
    ctx.fillStyle = "#0f172a";
    for (let i = 0; i < 4; i++) {
      ctx.fillRect(-12 + i * 7, -5, 5, 4);
    }
  } else if (type === "bike") {
    // 🏍️ Two-wheeler
    ctx.fillStyle = "#475569";
    ctx.fillRect(-5, -3, 10, 6);
    ctx.fillStyle = "#94a3b8";
    ctx.fillRect(-3, -2, 6, 4);
  } else if (type === "cab") {
    // 🚖 Kaali-Peeli City Cab
    ctx.fillStyle = "#facc15";
    ctx.beginPath();
    ctx.roundRect(-11, -6, 22, 12, 3);
    ctx.fill();
    ctx.fillStyle = "#0f172a";
    ctx.beginPath();
    ctx.roundRect(-5, -4, 8, 8, 2);
    ctx.fill();
    // Roof light
    ctx.fillStyle = "#fef08a";
    ctx.fillRect(-3, -7, 6, 2);
  } else {
    // 🚗 Modern Sedan
    ctx.fillStyle = "#38bdf8";
    ctx.beginPath();
    ctx.roundRect(-11, -6, 22, 12, 3);
    ctx.fill();
    ctx.fillStyle = "#0f172a";
    ctx.beginPath();
    ctx.roundRect(-5, -4, 8, 8, 2);
    ctx.fill();
  }

  // Headlights (Warm glow)
  ctx.fillStyle = "#fef08a";
  ctx.beginPath();
  ctx.arc(type === "bus" ? 16 : 11, -3, 1.5, 0, Math.PI * 2);
  ctx.arc(type === "bus" ? 16 : 11, 3, 1.5, 0, Math.PI * 2);
  ctx.fill();

  // Taillights (Red LED)
  ctx.fillStyle = "#ef4444";
  ctx.beginPath();
  ctx.arc(type === "bus" ? -16 : -11, -3, 1.2, 0, Math.PI * 2);
  ctx.arc(type === "bus" ? -16 : -11, 3, 1.2, 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();
}

function drawEmergencyVehicle(x, y, type) {
  ctx.save();
  ctx.translate(x, y);

  const L = 34, W = 16;

  // Drop Shadow
  ctx.fillStyle = "rgba(0,0,0,0.6)";
  ctx.beginPath();
  ctx.roundRect(-L / 2 + 2, -W / 2 + 2, L, W, 4);
  ctx.fill();

  if (type === "fire_engine") {
    // 🚒 Fire Engine
    ctx.fillStyle = "#ea580c";
    ctx.beginPath();
    ctx.roundRect(-L / 2, -W / 2, L, W, 4);
    ctx.fill();
    ctx.fillStyle = "#f97316";
    ctx.beginPath();
    ctx.roundRect(-L / 2 + 4, -W / 2 + 2, L - 8, W - 4, 2);
    ctx.fill();
  } else {
    // 🚨 Cardiac Ambulance (White with Red cross)
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.roundRect(-L / 2, -W / 2, L, W, 4);
    ctx.fill();

    // Red Side Stripes
    ctx.fillStyle = "#f43f5e";
    ctx.fillRect(-L / 2 + 3, -W / 2 + 1, L - 6, 2);
    ctx.fillRect(-L / 2 + 3, W / 2 - 3, L - 6, 2);

    // Red Cross on Roof
    ctx.fillRect(-2, -5, 4, 10);
    ctx.fillRect(-5, -2, 10, 4);
  }

  // Alternating High-Intensity Siren Beacons (Red & Blue flashing)
  const flash = Math.floor(Date.now() / 110) % 2 === 0;
  const c1 = flash ? "#f43f5e" : "#00f2fe";
  const c2 = flash ? "#00f2fe" : "#f43f5e";

  ctx.fillStyle = c1;
  ctx.shadowColor = c1;
  ctx.shadowBlur = 18;
  ctx.beginPath();
  ctx.arc(-8, 0, 3.5, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = c2;
  ctx.shadowColor = c2;
  ctx.beginPath();
  ctx.arc(8, 0, 3.5, 0, Math.PI * 2);
  ctx.fill();
  ctx.shadowBlur = 0;

  // Headlights
  ctx.fillStyle = "#fef08a";
  ctx.fillRect(L / 2 - 2, -W / 2 + 2, 3, 3);
  ctx.fillRect(L / 2 - 2, W / 2 - 5, 3, 3);

  ctx.restore();
}

function drawSirenWaves(x, y) {
  for (let i = 0; i < 2; i++) {
    const t = ((Date.now() + i * 500) % 1200) / 1200;
    const r = 16 + t * 45;
    const alpha = (1 - t) * 0.75;
    ctx.strokeStyle = i === 0 ? `rgba(244, 63, 94, ${alpha})` : `rgba(0, 242, 254, ${alpha})`;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.stroke();
  }
}

// ─── API Communication & Console ───

function logToConsole(msg, type = "info") {
  const t = new Date().toTimeString().split(" ")[0];
  const div = document.createElement("div");
  div.className = `log-entry ${type}`;
  div.innerHTML = `<span class="log-time">[${t}]</span> ${msg}`;
  consoleLogs.appendChild(div);
  while (consoleLogs.childElementCount > MAX_CONSOLE_ENTRIES) consoleLogs.removeChild(consoleLogs.firstChild);
  consoleLogs.scrollTop = consoleLogs.scrollHeight;
}

async function fetchStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/grid/status`);
    if (res.ok) updateState(await res.json());
  } catch (e) { console.error(e); }
}

function toggleSimulation() {
  isRunning = !isRunning;
  if (isRunning) {
    playPauseText.innerText = "Pause Simulation";
    btnPlayPause.classList.add("btn-danger");
    btnPlayPause.classList.remove("btn-primary");
    logToConsole("City grid simulation running.", "success");
    restartInterval();
  } else {
    playPauseText.innerText = "Run Simulation";
    btnPlayPause.classList.remove("btn-danger");
    btnPlayPause.classList.add("btn-primary");
    logToConsole("Simulation paused.", "warning");
    clearInterval(simInterval);
  }
}

function restartInterval() {
  clearInterval(simInterval);
  simInterval = setInterval(() => stepSimulation(1.0), Math.max(50, Math.floor(1000 / simSpeed)));
}

async function stepSimulation(dt = 1.0) {
  try {
    const res = await fetch(`${API_BASE}/api/grid/step`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dt })
    });
    if (res.ok) updateState(await res.json());
  } catch (e) { logToConsole(`Step error: ${e.message}`, "error"); }
}

async function resetSimulation() {
  isRunning = false;
  clearInterval(simInterval);
  playPauseText.innerText = "Run Simulation";
  btnPlayPause.classList.remove("btn-danger");
  btnPlayPause.classList.add("btn-primary");
  try {
    const res = await fetch(`${API_BASE}/api/grid/reset`, { method: "POST" });
    if (res.ok) {
      updateState((await res.json()).grid_state);
      initTrafficFleet();
      logToConsole("Nagpur City Grid reset to standby state.", "info");
    }
  } catch (e) { logToConsole(`Reset error: ${e.message}`, "error"); }
}

async function dispatchEmergency(type, priority) {
  try {
    const res = await fetch(`${API_BASE}/api/corridor/dispatch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ vehicle_type: type, origin: "Sitabuldi Junction", destination: "AIIMS / GMC Hospital Gate", priority })
    });
    if (res.ok) {
      const data = await res.json();
      updateState(data.grid_state);
      logToConsole(`🚨 DISPATCHED: ${data.emergency_vehicle.vehicle_type.toUpperCase()} (${data.emergency_vehicle.ev_id}) -> Green Corridor Preemption Active!`, "error");
      if (!isRunning) toggleSimulation();
    }
  } catch (e) { logToConsole(`Dispatch error: ${e.message}`, "error"); }
}

function updateState(state) {
  if (!state) return;
  gridState = state;

  timeSavedVal.innerText = `${state.avg_delay_reduction_pct}%`;
  livesVal.innerText = state.lives_assisted;

  const ev = state.active_emergencies.find(e => e.status === "in_transit" || e.status === "dispatched");

  if (ev) {
    activeEmgVal.innerText = ev.vehicle_type.toUpperCase();
    activeEmgVal.className = ev.priority === 1 ? "stat-value text-rose" : "stat-value text-amber";
    activeEmgSub.innerText = `${ev.ev_id} | ${ev.current_speed_kmh} km/h | ${ev.pos_progress}%`;
    corridorStatusPill.style.borderColor = "#f43f5e";
    corridorStatusPill.style.color = "#f43f5e";
    corridorStatusPill.style.background = "rgba(244, 63, 94, 0.15)";
    corridorStatusText.innerText = "🚨 GREEN WAVE ACTIVE";
    greenWaveVal.innerText = "CASCADING GREEN";
    greenWaveVal.className = "stat-value text-emerald";

    const dist = ((100 - ev.pos_progress) / 100) * 2200;
    const spd = ev.current_speed_kmh / 3.6;
    const tti = spd > 0 ? Math.max(0, Math.round(dist / spd)) : 0;
    ttiVal.innerText = `${tti}s (~${(tti / 60).toFixed(1)} min)`;
  } else {
    activeEmgVal.innerText = "STANDBY";
    activeEmgVal.className = "stat-value text-rose";
    activeEmgSub.innerText = "No active preemption call";
    corridorStatusPill.style.borderColor = "#10b981";
    corridorStatusPill.style.color = "#10b981";
    corridorStatusPill.style.background = "rgba(16, 185, 129, 0.15)";
    corridorStatusText.innerText = "CORRIDOR ARMED";
    greenWaveVal.innerText = "STANDBY";
    greenWaveVal.className = "stat-value text-cyan";
    ttiVal.innerText = "--";
  }

  if (state.nodes) {
    NODE_KEYS.forEach((key, idx) => {
      const node = state.nodes[key];
      if (!node) return;
      const n = idx + 1;
      const sEl = document.getElementById(`stateNode${n}`);
      const qEl = document.getElementById(`queueNode${n}`);
      const bEl = document.getElementById(`boxNode${n}`);

      if (node.is_preempted) {
        sEl.innerText = "🚨 PREEMPTED (GREEN WAVE)";
        sEl.className = "node-box-state text-rose";
        bEl.style.borderColor = "rgba(244, 63, 94, 0.5)";
      } else {
        const g = node.phase === "MAIN_CORRIDOR";
        sEl.innerText = g ? "GREEN (CORRIDOR)" : "RED (CROSS ACTIVE)";
        sEl.className = g ? "node-box-state text-emerald" : "node-box-state text-amber";
        bEl.style.borderColor = "rgba(255,255,255,0.08)";
      }
      const q = Math.round((node.queues.CORRIDOR_IN || 0) + (node.queues.CROSS_LEFT || 0));
      qEl.innerText = `Queue: ${q} veh | Km ${node.km_mark}`;
    });
  }
}

// ─── Automated Test Suite ───
async function runAutomatedTestSuite() {
  logToConsole("════════════════════════════════════════", "info");
  logToConsole("Executing GreenCorridor Preemption Test Suite...", "warning");
  btnRunAllTests.disabled = true;

  for (let i = 1; i <= 5; i++) {
    const el = document.getElementById(`test-${i}`);
    if (el) {
      const b = el.querySelector(".test-badge");
      b.className = "test-badge pending";
      b.innerText = "READY";
      el.classList.remove("passed", "failed");
    }
  }

  try {
    const res = await fetch(`${API_BASE}/api/corridor/test_suite`, { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      for (const tc of data.results) {
        const el = document.getElementById(tc.id);
        if (!el) continue;
        const b = el.querySelector(".test-badge");
        b.className = "test-badge running";
        b.innerText = "RUNNING";
        await new Promise(r => setTimeout(r, 350));

        if (tc.status === "PASS") {
          b.className = "test-badge pass";
          b.innerText = "PASS";
          el.classList.add("passed");
          logToConsole(`✅ [PASS] ${tc.name} — ${tc.metrics}`, "success");
        } else {
          b.className = "test-badge fail";
          b.innerText = "FAIL";
          el.classList.add("failed");
          logToConsole(`❌ [FAIL] ${tc.name}`, "error");
        }
      }
      logToConsole(`Test Suite Complete: ${data.passed_count}/${data.total_count} Passed!`, data.all_passed ? "success" : "warning");
    }
  } catch (e) { logToConsole(`Test error: ${e.message}`, "error"); }
  finally { btnRunAllTests.disabled = false; }
}
