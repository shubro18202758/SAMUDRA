from contextlib import asynccontextmanager
import time
from collections import deque

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.ws.telemetry import router as ws_router

# ─── Shared telemetry history ring-buffer ──────────────────────────────────
# Stores the last 300 frames (~75 seconds at 4 Hz) for REST consumers
telemetry_history: deque[dict] = deque(maxlen=300)
start_time: float = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Project SAMUDRA",
    version="2.0.0",
    description="Maritime Fuel Optimisation Telemetry Backend — Industry Grade",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.frontend_port}",
        f"http://127.0.0.1:{settings.frontend_port}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)


@app.get("/health")
async def health():
    return {
        "status": "operational",
        "project": "SAMUDRA",
        "version": "2.0.0",
        "uptime_s": round(time.time() - start_time, 1),
        "history_depth": len(telemetry_history),
    }


@app.get("/api/v1/telemetry/latest")
async def telemetry_latest():
    """Return the most recent telemetry snapshot."""
    if telemetry_history:
        return telemetry_history[-1]
    return {"error": "No telemetry data yet"}


@app.get("/api/v1/telemetry/history")
async def telemetry_history_endpoint(last: int = 60):
    """Return the last N telemetry frames (default 60 = ~15s)."""
    last = min(last, len(telemetry_history))
    return list(telemetry_history)[-last:]


@app.get("/api/v1/vessel/status")
async def vessel_status():
    """Aggregated vessel status summary for dashboard widgets."""
    if not telemetry_history:
        return {"error": "No telemetry data yet"}
    latest = telemetry_history[-1]
    frames = list(telemetry_history)

    # Compute averages over available history
    avg_fuel = sum(f["engine"]["fuel_flow_kgh"] for f in frames) / len(frames)
    avg_speed = sum(f["navigation"]["speed_knots"] for f in frames) / len(frames)
    max_fuel = max(f["engine"]["fuel_flow_kgh"] for f in frames)
    min_fuel = min(f["engine"]["fuel_flow_kgh"] for f in frames)

    return {
        "current": latest,
        "averages": {
            "fuel_flow_kgh": round(avg_fuel, 2),
            "speed_knots": round(avg_speed, 2),
        },
        "ranges": {
            "fuel_flow_kgh": {"min": round(min_fuel, 2), "max": round(max_fuel, 2)},
        },
        "frame_count": len(frames),
        "uptime_s": round(time.time() - start_time, 1),
    }


# ─── Phase 4: New Endpoints for 7-Gap Modules ────────────────────────────
@app.get("/api/v1/sensors/status")
async def sensors_status():
    """Sensor Integration Hub — latest sensor health and data."""
    if not telemetry_history:
        return {"error": "No telemetry data yet"}
    latest = telemetry_history[-1]
    return latest.get("sensor_integration", {})


@app.get("/api/v1/maintenance/status")
async def maintenance_status():
    """Predictive Maintenance — component health and schedule."""
    if not telemetry_history:
        return {"error": "No telemetry data yet"}
    latest = telemetry_history[-1]
    return latest.get("predictive_maintenance", {})


@app.get("/api/v1/hull/status")
async def hull_status():
    """Hull coating & hybrid propulsion status."""
    if not telemetry_history:
        return {"error": "No telemetry data yet"}
    latest = telemetry_history[-1]
    return latest.get("hull_propulsion", {})


@app.get("/api/v1/blindspots/status")
async def blindspots_status():
    """Systemic blind spot detection results."""
    if not telemetry_history:
        return {"error": "No telemetry data yet"}
    latest = telemetry_history[-1]
    return latest.get("blind_spots", {})


@app.get("/api/v1/humanai/status")
async def humanai_status():
    """Human-AI collaboration — distribution shift, connectivity, XAI."""
    if not telemetry_history:
        return {"error": "No telemetry data yet"}
    latest = telemetry_history[-1]
    return latest.get("human_ai_collaboration", {})


@app.get("/api/v1/eexi/status")
async def eexi_status():
    """EEXI & enhanced CII compliance status."""
    if not telemetry_history:
        return {"error": "No telemetry data yet"}
    latest = telemetry_history[-1]
    return latest.get("eexi_compliance", {})


@app.get("/api/v1/data/quality")
async def data_quality():
    """Data architecture — quality scoring and sensor registry."""
    if not telemetry_history:
        return {"error": "No telemetry data yet"}
    latest = telemetry_history[-1]
    return latest.get("data_architecture", {})
