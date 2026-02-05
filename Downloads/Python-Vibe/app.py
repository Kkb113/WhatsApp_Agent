from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# For demo: in-memory store (replace with DB later)
USER_SETTINGS = {
    "baseline": 0.0,
    "threshold": 15.0,
    "hold_ms": 1200,
    "cooldown_ms": 2500,
}

EVENT_LOG = []  # posture events

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/settings")
def get_settings():
    return jsonify(USER_SETTINGS)

@app.post("/api/settings")
def save_settings():
    data = request.get_json(force=True) or {}
    for k in ["baseline", "threshold", "hold_ms", "cooldown_ms"]:
        if k in data:
            USER_SETTINGS[k] = float(data[k]) if k in ["baseline", "threshold"] else int(data[k])
    return jsonify({"ok": True, "settings": USER_SETTINGS})

@app.post("/api/event")
def log_event():
    data = request.get_json(force=True) or {}
    EVENT_LOG.append({
        "ts": datetime.utcnow().isoformat() + "Z",
        "type": data.get("type", "unknown"),
        "angle": data.get("angle"),
        "delta": data.get("delta"),
    })
    # keep small
    if len(EVENT_LOG) > 500:
        del EVENT_LOG[:100]
    return jsonify({"ok": True})

@app.get("/api/events")
def get_events():
    return jsonify(EVENT_LOG[-50:])

if __name__ == "__main__":
    # NOTE: sensors require HTTPS on phone.
    # For local dev: run and use https via a tunnel (ngrok/cloudflared) OR localhost on device emulator.
    port = int(os.environ.get("PORT", 5000))  # default to 5000 locally
    app.run(host="0.0.0.0", port=port, debug=True)
