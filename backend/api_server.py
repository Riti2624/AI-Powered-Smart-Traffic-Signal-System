from __future__ import annotations

from flask import Flask, jsonify

from backend.telemetry import TelemetryStore


def create_app(telemetry: TelemetryStore) -> Flask:
    app = Flask(__name__)

    @app.get("/api/health")
    def health():
        latest_state = telemetry.latest()
        return jsonify(
            {
                "status": "ok",
                "mode": latest_state.get("mode", "unknown"),
                "step": latest_state.get("step", 0),
            }
        )

    @app.get("/api/latest")
    def latest():
        return jsonify(telemetry.latest())

    return app
