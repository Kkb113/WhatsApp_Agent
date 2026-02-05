const els = {
  statusPill: document.getElementById("statusPill"),
  btnEnable: document.getElementById("btnEnable"),
  btnStart: document.getElementById("btnStart"),
  btnStop: document.getElementById("btnStop"),
  btnCalibrate: document.getElementById("btnCalibrate"),
  btnTestVibe: document.getElementById("btnTestVibe"),
  btnSave: document.getElementById("btnSave"),
  btnReset: document.getElementById("btnReset"),
  curAngle: document.getElementById("curAngle"),
  baseline: document.getElementById("baseline"),
  delta: document.getElementById("delta"),
  gaugeBar: document.getElementById("gaugeBar"),
  threshold: document.getElementById("threshold"),
  thresholdVal: document.getElementById("thresholdVal"),
  holdMs: document.getElementById("holdMs"),
  holdVal: document.getElementById("holdVal"),
  cooldownMs: document.getElementById("cooldownMs"),
  cooldownVal: document.getElementById("cooldownVal"),
  log: document.getElementById("log"),
};

const LS_KEY = "postureVibeSettings:v1";

let state = {
  enabled: false,
  running: false,

  // settings
  baseline: 0,
  threshold: 15,
  hold_ms: 1200,
  cooldown_ms: 2500,

  // live
  angle: null,
  smoothedAngle: null,
  lastOkTs: performance.now(),
  breachStartTs: null,
  lastVibeTs: 0,
};

function setStatus(text, kind="idle"){
  els.statusPill.textContent = text;
  els.statusPill.style.color =
    kind === "ok" ? "var(--ok)" :
    kind === "bad" ? "var(--danger)" :
    "var(--muted)";
}

function fmt(n){ return (n === null || n === undefined) ? "--" : `${n.toFixed(1)}°`; }

function logItem(title, sub){
  const div = document.createElement("div");
  div.className = "logItem";
  div.innerHTML = `<div><b>${title}</b><div><small>${sub}</small></div></div><div><small>${new Date().toLocaleTimeString()}</small></div>`;
  els.log.prepend(div);
  while (els.log.children.length > 8) els.log.removeChild(els.log.lastChild);
}

// Map device orientation -> "bend angle"
// We use beta (front-back tilt) as our primary "pitch-like" signal.
// Depending on how the phone is worn/placed, user can calibrate baseline.
function handleOrientation(e){
  // e.beta ranges roughly [-180, 180]
  const beta = (typeof e.beta === "number") ? e.beta : null;
  if (beta === null) return;
  const angle = beta;

  // exponential smoothing
  const alpha = 0.18; // 0..1 (higher = more responsive)
  state.smoothedAngle = state.smoothedAngle === null ? angle : (alpha * angle + (1 - alpha) * state.smoothedAngle);
  state.angle = angle;

  renderAndDetect();
}

function renderAndDetect(){
  if (state.smoothedAngle === null) return;

  const cur = state.smoothedAngle;
  const delta = Math.abs(cur - state.baseline);

  els.curAngle.textContent = fmt(cur);
  els.baseline.textContent = fmt(state.baseline);
  els.delta.textContent = fmt(delta);

  // gauge 0..40deg => 0..100
  const pct = Math.max(0, Math.min(100, (delta / 40) * 100));
  els.gaugeBar.style.width = `${pct}%`;

  if (!state.running) {
    setStatus("Ready", "idle");
    return;
  }

  const now = performance.now();

  const inCooldown = (now - state.lastVibeTs) < state.cooldown_ms;

  if (delta <= state.threshold){
    state.breachStartTs = null;
    setStatus(inCooldown ? "Cooldown" : "Good posture", "ok");
    return;
  }

  // threshold exceeded
  setStatus("Too much bend", "bad");

  if (inCooldown) return;

  if (state.breachStartTs === null) state.breachStartTs = now;

  const breachedFor = now - state.breachStartTs;
  if (breachedFor >= state.hold_ms) {
    vibratePattern();
    state.lastVibeTs = now;
    state.breachStartTs = null;

    const msg = `Δ ${delta.toFixed(1)}° (thr ${state.threshold}°)`;
    logItem("Vibration alert", msg);

    // optional backend log
    fetch("/api/event", {
      method:"POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ type:"vibe", angle: cur, delta })
    }).catch(()=>{});
  }
}

function vibratePattern(){
  if (!("vibrate" in navigator)) {
    logItem("Vibration not supported", "This browser/device may block vibration.");
    return;
  }
  // Short pattern: vibrate-pause-vibrate
  navigator.vibrate([180, 80, 180]);
}

async function requestMotionPermissionIfNeeded(){
  // iOS Safari requires explicit permission for motion/orientation events
  const D = window.DeviceOrientationEvent;
  if (D && typeof D.requestPermission === "function") {
    const res = await D.requestPermission();
    if (res !== "granted") throw new Error("Motion permission denied");
  }
}

function startListening(){
  window.addEventListener("deviceorientation", handleOrientation, { passive:true });
}

function stopListening(){
  window.removeEventListener("deviceorientation", handleOrientation);
}

function applyUI(){
  els.threshold.value = state.threshold;
  els.thresholdVal.textContent = `${state.threshold}°`;
  els.holdMs.value = state.hold_ms;
  els.holdVal.textContent = `${state.hold_ms}`;
  els.cooldownMs.value = state.cooldown_ms;
  els.cooldownVal.textContent = `${state.cooldown_ms}`;
  els.baseline.textContent = fmt(state.baseline);
}

function saveLocal(){
  localStorage.setItem(LS_KEY, JSON.stringify({
    baseline: state.baseline,
    threshold: state.threshold,
    hold_ms: state.hold_ms,
    cooldown_ms: state.cooldown_ms,
  }));
}

function loadLocal(){
  try{
    const raw = localStorage.getItem(LS_KEY);
    if (!raw) return;
    const v = JSON.parse(raw);
    if (typeof v.baseline === "number") state.baseline = v.baseline;
    if (typeof v.threshold === "number") state.threshold = v.threshold;
    if (typeof v.hold_ms === "number") state.hold_ms = v.hold_ms;
    if (typeof v.cooldown_ms === "number") state.cooldown_ms = v.cooldown_ms;
  } catch {}
}

async function loadServerSettings(){
  try{
    const r = await fetch("/api/settings");
    const s = await r.json();
    if (typeof s.baseline === "number") state.baseline = s.baseline;
    if (typeof s.threshold === "number") state.threshold = s.threshold;
    if (typeof s.hold_ms === "number") state.hold_ms = s.hold_ms;
    if (typeof s.cooldown_ms === "number") state.cooldown_ms = s.cooldown_ms;
  } catch {}
}

async function saveServerSettings(){
  await fetch("/api/settings", {
    method:"POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({
      baseline: state.baseline,
      threshold: state.threshold,
      hold_ms: state.hold_ms,
      cooldown_ms: state.cooldown_ms,
    })
  });
}

els.btnEnable.addEventListener("click", async () => {
  try{
    await requestMotionPermissionIfNeeded();
    state.enabled = true;
    startListening();
    setStatus("Sensors enabled", "ok");
    els.btnEnable.disabled = true;
  } catch (e){
    setStatus("Permission denied", "bad");
    logItem("Permission error", e.message || "Could not enable motion sensors");
  }
});

els.btnStart.addEventListener("click", () => {
  if (!state.enabled) {
    logItem("Enable sensors first", "Tap “Enable Sensors”");
    return;
  }
  state.running = true;
  els.btnStart.disabled = true;
  els.btnStop.disabled = false;
  setStatus("Monitoring", "ok");
});

els.btnStop.addEventListener("click", () => {
  state.running = false;
  els.btnStart.disabled = false;
  els.btnStop.disabled = true;
  setStatus("Stopped", "idle");
});

els.btnCalibrate.addEventListener("click", () => {
  if (state.smoothedAngle === null) {
    logItem("No sensor data", "Enable sensors and move the phone slightly");
    return;
  }
  state.baseline = state.smoothedAngle;
  saveLocal();
  setStatus("Baseline set", "ok");
  logItem("Calibrated", `Baseline = ${state.baseline.toFixed(1)}°`);
});

els.btnTestVibe.addEventListener("click", () => {
  vibratePattern();
});

els.threshold.addEventListener("input", (e) => {
  state.threshold = parseInt(e.target.value, 10);
  els.thresholdVal.textContent = `${state.threshold}°`;
  saveLocal();
});
els.holdMs.addEventListener("input", (e) => {
  state.hold_ms = parseInt(e.target.value, 10);
  els.holdVal.textContent = `${state.hold_ms}`;
  saveLocal();
});
els.cooldownMs.addEventListener("input", (e) => {
  state.cooldown_ms = parseInt(e.target.value, 10);
  els.cooldownVal.textContent = `${state.cooldown_ms}`;
  saveLocal();
});

els.btnSave.addEventListener("click", async () => {
  saveLocal();
  try{
    await saveServerSettings();
    logItem("Saved", "Settings saved to server + device");
  } catch {
    logItem("Saved locally", "Server save failed (offline?)");
  }
});

els.btnReset.addEventListener("click", async () => {
  state.baseline = 0;
  state.threshold = 15;
  state.hold_ms = 1200;
  state.cooldown_ms = 2500;
  saveLocal();
  applyUI();
  setStatus("Reset", "idle");
  try { await saveServerSettings(); } catch {}
});

// init
(async function init(){
  loadLocal();
  await loadServerSettings(); // optional
  applyUI();
  setStatus("Idle", "idle");
})();
