"""Inspector web backend.

FastAPI + WebSocket layer over the same Inspector pipeline used from
Python (`d.inspect()`), per docs/UIAUTOMATOR3_ARCHITECTURE.md section 11.
Binds to localhost by default per project spec section 52 (security):
the device service must not expose unrestricted functionality on a public
interface without explicit opt-in.
"""
import asyncio
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from uiautomator3.client.connect import connect as u3_connect
from uiautomator3.device.device import Device
from uiautomator3.inspector.inspector import Inspector
from uiautomator3.inspector.serialize import tree_to_dict
from uiautomator3.logging_config import get_logger

logger = get_logger("inspector.server")

app = FastAPI(title="UIAutomator 3.0 Inspector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_devices: Dict[str, Device] = {}


def get_or_connect(serial: Optional[str] = None) -> Device:
    key = serial or "__default__"
    if key not in _devices:
        _devices[key] = u3_connect(serial)
    return _devices[key]


@app.get("/api/devices")
def list_devices():
    from uiautomator3.adb.discovery import list_devices as _list

    return [{"serial": d.serial} for d in _list()]


@app.get("/api/inspect")
def inspect(serial: Optional[str] = None):
    try:
        device = get_or_connect(serial)
        snapshot = Inspector(device).inspect()
    except Exception as e:
        logger.exception("inspect failed")
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {
        "package_name": snapshot.package_name,
        "activity": snapshot.activity,
        "screen_width": snapshot.screen_width,
        "screen_height": snapshot.screen_height,
        "timestamp": snapshot.timestamp,
        "screenshot_png_base64": snapshot.screenshot_png_base64,
        "hierarchy": tree_to_dict(snapshot.tree),
    }


@app.get("/api/hierarchy")
def hierarchy(serial: Optional[str] = None):
    try:
        device = get_or_connect(serial)
        tree = device.inspect()
    except Exception as e:
        logger.exception("hierarchy failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    return tree_to_dict(tree)


@app.get("/api/screenshot")
def screenshot(serial: Optional[str] = None):
    import base64
    import io

    try:
        device = get_or_connect(serial)
        image = device.screenshot()
    except Exception as e:
        logger.exception("screenshot failed")
        raise HTTPException(status_code=500, detail=str(e)) from e

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return {"png_base64": base64.b64encode(buf.getvalue()).decode("ascii")}


@app.post("/api/click")
def click(x: int, y: int, serial: Optional[str] = None):
    try:
        device = get_or_connect(serial)
        device.click(x, y)
    except Exception as e:
        logger.exception("click failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"ok": True}


@app.websocket("/ws/inspect")
async def ws_inspect(websocket: WebSocket, serial: Optional[str] = None):
    """Push inspection snapshots to the client at a fixed interval."""
    await websocket.accept()
    try:
        device = get_or_connect(serial)
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()
        return

    inspector = Inspector(device)
    try:
        while True:
            try:
                snapshot = await asyncio.to_thread(inspector.inspect)
            except Exception as e:
                await websocket.send_json({"type": "error", "message": str(e)})
                await asyncio.sleep(1.0)
                continue

            await websocket.send_json(
                {
                    "type": "snapshot",
                    "package_name": snapshot.package_name,
                    "activity": snapshot.activity,
                    "screen_width": snapshot.screen_width,
                    "screen_height": snapshot.screen_height,
                    "timestamp": snapshot.timestamp,
                    "screenshot_png_base64": snapshot.screenshot_png_base64,
                    "hierarchy": tree_to_dict(snapshot.tree),
                }
            )
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        logger.debug("inspector websocket disconnected")


def serve(host: str = "127.0.0.1", port: int = 17920, serial: Optional[str] = None) -> None:
    import uvicorn

    if serial:
        get_or_connect(serial)
    uvicorn.run(app, host=host, port=port)
