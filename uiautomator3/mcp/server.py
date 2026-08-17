"""MCP server exposing UIAutomator 3.0 to AI agents.

Per docs/UIAUTOMATOR3_ARCHITECTURE.md section 12: a thin tool-registration
layer over Device/AIController - each tool below is a near-1:1 wrapper, no
parallel automation logic. Tool result shapes follow project spec section
63 (role/label/locator/confidence), never raw screenshots alone except for
the explicit take_screenshot tool.

Runs only when explicitly started (`u3 mcp serve` / `serve()`), never
implicitly on import - project spec section 52 (security): the device
service must not expose unrestricted functionality by default.

`run_script` (arbitrary shell) is NOT registered unless `allow_shell=True`
is passed to `build_server()` - project spec section 52: "Never execute
arbitrary shell commands through public APIs without explicit opt-in."
"""
from typing import Any, Dict, Optional

from uiautomator3.client.connect import connect as u3_connect
from uiautomator3.device.device import Device
from uiautomator3.inspector.serialize import tree_to_dict
from uiautomator3.logging_config import get_logger

logger = get_logger("mcp.server")

_devices: Dict[str, Device] = {}


def _get_or_connect(serial: Optional[str] = None) -> Device:
    key = serial or "__default__"
    if key not in _devices:
        _devices[key] = u3_connect(serial)
    return _devices[key]


def build_server(allow_shell: bool = False):
    """Construct the MCP server with all tools registered.

    Imports the `mcp` package lazily (optional dependency, `web`/`mcp`
    extra) so importing uiautomator3.mcp never requires it unless a server
    is actually being built.
    """
    from mcp.server.mcpserver import MCPServer

    server = MCPServer(name="uiautomator3", instructions="Android UI automation for AI agents.")

    @server.tool()
    def connect_device(serial: Optional[str] = None) -> Dict[str, Any]:
        """Connect to an Android device (first attached device if serial is omitted)."""
        device = _get_or_connect(serial)
        return {"serial": device.serial, "connected": True}

    @server.tool()
    def get_device_info(serial: Optional[str] = None) -> Dict[str, Any]:
        """Return device model/brand/Android version/resolution."""
        device = _get_or_connect(serial)
        info = device.info()
        return {
            "serial": info.serial,
            "model": info.model,
            "brand": info.brand,
            "android_version": info.android_version,
            "sdk_version": info.sdk_version,
            "width": info.width,
            "height": info.height,
            "rotation": info.rotation,
        }

    @server.tool()
    def inspect_screen(serial: Optional[str] = None) -> Dict[str, Any]:
        """Structured screen description (role/label/locator/confidence per element) -
        the primary tool for an agent to understand what's on screen."""
        device = _get_or_connect(serial)
        return device.ai.inspect()

    @server.tool()
    def find_element(description: str, serial: Optional[str] = None) -> Dict[str, Any]:
        """Find element(s) matching a natural-language description, e.g. 'Login button'."""
        device = _get_or_connect(serial)
        return device.ai.find(description)

    @server.tool()
    def click_element(description: str, serial: Optional[str] = None) -> Dict[str, Any]:
        """Click the element best matching `description`."""
        device = _get_or_connect(serial)
        return device.ai.click(description)

    @server.tool()
    def type_text(description: str, text: str, serial: Optional[str] = None) -> Dict[str, Any]:
        """Click the element matching `description`, then type `text` into it."""
        device = _get_or_connect(serial)
        return device.ai.type(description, text)

    @server.tool()
    def swipe(
        from_x: int, from_y: int, to_x: int, to_y: int, duration: float = 0.5, serial: Optional[str] = None
    ) -> Dict[str, Any]:
        """Swipe from one point to another."""
        device = _get_or_connect(serial)
        device.swipe(from_x, from_y, to_x, to_y, duration=duration)
        return {"ok": True}

    @server.tool()
    def scroll(direction: str = "down", serial: Optional[str] = None) -> Dict[str, Any]:
        """Scroll the screen 'up', 'down', 'left', or 'right'."""
        device = _get_or_connect(serial)
        info = device.info()
        cx, cy = info.width // 2, info.height // 2
        offset = min(info.width, info.height) // 3
        deltas = {
            "down": (cx, cy + offset, cx, cy - offset),
            "up": (cx, cy - offset, cx, cy + offset),
            "left": (cx - offset, cy, cx + offset, cy),
            "right": (cx + offset, cy, cx - offset, cy),
        }
        if direction not in deltas:
            return {"ok": False, "error": f"invalid direction: {direction!r}"}
        fx, fy, tx, ty = deltas[direction]
        device.swipe(fx, fy, tx, ty, duration=0.3)
        return {"ok": True, "direction": direction}

    @server.tool()
    def take_screenshot(serial: Optional[str] = None) -> Dict[str, Any]:
        """Capture a screenshot, returned as base64 PNG."""
        import base64
        import io

        device = _get_or_connect(serial)
        image = device.screenshot()
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return {"png_base64": base64.b64encode(buf.getvalue()).decode("ascii"), "width": image.width, "height": image.height}

    @server.tool()
    def get_ui_tree(serial: Optional[str] = None) -> Dict[str, Any]:
        """Return the full normalized UI hierarchy (all elements, not just labeled ones)."""
        device = _get_or_connect(serial)
        tree = device.inspect()
        return tree_to_dict(tree)

    @server.tool()
    def get_current_activity(serial: Optional[str] = None) -> Dict[str, Any]:
        """Return the current foreground package/activity/pid."""
        device = _get_or_connect(serial)
        current = device.app.current()
        return {"package": current.package, "activity": current.activity, "pid": current.pid}

    @server.tool()
    def launch_app(package_name: str, activity: Optional[str] = None, serial: Optional[str] = None) -> Dict[str, Any]:
        """Launch an app by package name."""
        device = _get_or_connect(serial)
        device.launch_app(package_name, activity)
        return {"ok": True, "package": package_name}

    @server.tool()
    def stop_app(package_name: str, serial: Optional[str] = None) -> Dict[str, Any]:
        """Force-stop an app by package name."""
        device = _get_or_connect(serial)
        device.stop_app(package_name)
        return {"ok": True, "package": package_name}

    @server.tool()
    def install_app(path_or_url: str, serial: Optional[str] = None) -> Dict[str, Any]:
        """Install an APK from a local path or URL."""
        device = _get_or_connect(serial)
        device.app.install(path_or_url)
        return {"ok": True}

    if allow_shell:

        @server.tool()
        def run_script(shell_command: str, serial: Optional[str] = None) -> Dict[str, Any]:
            """Run a raw adb shell command. DANGEROUS - only registered when the
            server is started with allow_shell=True (opt-in, project spec section 52)."""
            device = _get_or_connect(serial)
            output = device.shell(shell_command)
            return {"output": output}

    return server


def serve(host: str = "127.0.0.1", port: int = 17921, allow_shell: bool = False, transport: str = "stdio") -> None:
    server = build_server(allow_shell=allow_shell)
    if transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(transport=transport, host=host, port=port)
