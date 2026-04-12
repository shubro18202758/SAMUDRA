"""
ws/telemetry.py — Bidirectional WebSocket Telemetry Channel
============================================================
Streams Pydantic-validated, physics-derived telemetry frames over a
persistent WebSocket connection at 250 ms (4 Hz).

Incoming commands (JSON) from the frontend are processed concurrently:
  { "command": "set_ai_mode", "enabled": true|false }
"""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings
from app.models import TelemetryFrame
from app.physics.hydrodynamics import HydrodynamicEngine

logger = logging.getLogger("samudra.telemetry")
router = APIRouter()


async def _receive_commands(
    websocket: WebSocket,
    engine: HydrodynamicEngine,
) -> None:
    """Listen for incoming JSON commands and mutate engine state."""
    try:
        while True:
            text = await websocket.receive_text()
            try:
                msg = json.loads(text)
            except json.JSONDecodeError:
                logger.warning("Malformed command: %s", text[:120])
                continue

            cmd = msg.get("command")
            if cmd == "set_ai_mode":
                enabled = bool(msg.get("enabled", True))
                engine.ai_enabled = enabled
                logger.info("AI Advisory Mode → %s", "ON" if enabled else "OFF")
            else:
                logger.warning("Unknown command: %s", cmd)
    except (WebSocketDisconnect, Exception):
        pass


async def _send_telemetry(
    websocket: WebSocket,
    engine: HydrodynamicEngine,
    dt: float,
) -> None:
    """Continuously emit telemetry frames at the configured tick rate."""
    # Import history buffer from main (lazy to avoid circular)
    from app.main import telemetry_history

    while True:
        raw = engine.tick(dt)
        frame = TelemetryFrame(**raw)
        frame_json = frame.model_dump(mode="json")
        telemetry_history.append(frame_json)
        await websocket.send_text(frame.model_dump_json())
        await asyncio.sleep(dt)


@router.websocket("/ws/telemetry")
async def telemetry_stream(websocket: WebSocket) -> None:
    """Bidirectional telemetry channel — send frames, receive commands."""
    await websocket.accept()

    engine = HydrodynamicEngine()
    dt = settings.ws_tick_rate_ms / 1000.0

    sender = asyncio.create_task(_send_telemetry(websocket, engine, dt))
    receiver = asyncio.create_task(_receive_commands(websocket, engine))

    try:
        # Wait until either task finishes (disconnect or error)
        done, pending = await asyncio.wait(
            {sender, receiver},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    except Exception:
        sender.cancel()
        receiver.cancel()
    finally:
        try:
            await websocket.close(code=1000)
        except Exception:
            pass
