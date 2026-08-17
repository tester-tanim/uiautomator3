"""`u3` command-line entry point.

Phase 1: devices, doctor, version.
Phase 4 adds: inspect (launches the web inspector server), screenshot, dump
(see project spec section 41).
Phase 9 adds: codegen - reads a JSON-exported RecordingSession (e.g. from
the web inspector's recorder, or Device.start_recording()/stop_recording()
+ codegen.generate_json()) and emits automation code in the requested
format.
Phase 10 adds: mcp serve - launches the MCP server (project spec section
41: `u3 mcp serve`). Shell command execution is off unless --allow-shell
is passed (project spec section 52).
"""
import argparse
import json
import sys

from uiautomator3.adb.discovery import list_devices
from uiautomator3.diagnostics.doctor import run_doctor
from uiautomator3.version import __version__


def cmd_devices(_args: argparse.Namespace) -> int:
    devs = list_devices()
    if not devs:
        print("No devices attached")
        return 1
    for d in devs:
        print(d.serial)
    return 0


def cmd_doctor(_args: argparse.Namespace) -> int:
    report = run_doctor()
    print(report.format())
    return 0 if report.all_ok else 1


def cmd_version(_args: argparse.Namespace) -> int:
    print(__version__)
    return 0


def cmd_dump(args: argparse.Namespace) -> int:
    from uiautomator3.client.connect import connect

    d = connect(args.device)
    print(d.dump_hierarchy())
    return 0


def cmd_screenshot(args: argparse.Namespace) -> int:
    from uiautomator3.client.connect import connect

    d = connect(args.device)
    d.screenshot().save(args.output)
    print(f"Saved {args.output}")
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    try:
        from uiautomator3.inspector.server import serve
    except ImportError:
        print(
            "The inspector requires the 'web' extra. Install with:\n"
            "  pip install uiautomator3[web]"
        )
        return 1

    print(f"Starting inspector at http://{args.host}:{args.port}")
    serve(host=args.host, port=args.port, serial=args.device)
    return 0


def cmd_codegen(args: argparse.Namespace) -> int:
    import uiautomator3.codegen as codegen
    from uiautomator3.recording.session import RecordingSession

    generators = {
        "python": codegen.generate_python,
        "pytest": codegen.generate_pytest,
        "pom": codegen.generate_pom,
        "json": codegen.generate_json,
        "yaml": codegen.generate_yaml,
        "robot": codegen.generate_robot,
        "raw": codegen.generate_raw,
    }

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    session = RecordingSession.from_list(data)

    output = generators[args.format](session)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Wrote {args.output}")
    else:
        print(output)
    return 0


def cmd_mcp_serve(args: argparse.Namespace) -> int:
    try:
        from uiautomator3.mcp.server import serve
    except ImportError:
        print(
            "The MCP server requires the 'mcp' package. Install with:\n"
            "  pip install mcp"
        )
        return 1

    serve(host=args.host, port=args.port, allow_shell=args.allow_shell, transport=args.transport)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="u3", description="UIAutomator 3.0 CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("devices", help="List attached devices").set_defaults(func=cmd_devices)
    subparsers.add_parser("doctor", help="Run environment diagnostics").set_defaults(func=cmd_doctor)
    subparsers.add_parser("version", help="Print version").set_defaults(func=cmd_version)

    dump_parser = subparsers.add_parser("dump", help="Dump the current UI hierarchy as XML")
    dump_parser.add_argument("--device", default=None, help="Device serial")
    dump_parser.set_defaults(func=cmd_dump)

    shot_parser = subparsers.add_parser("screenshot", help="Capture a screenshot")
    shot_parser.add_argument("--device", default=None, help="Device serial")
    shot_parser.add_argument("-o", "--output", default="screenshot.png", help="Output file path")
    shot_parser.set_defaults(func=cmd_screenshot)

    inspect_parser = subparsers.add_parser("inspect", help="Launch the web inspector")
    inspect_parser.add_argument("--device", default=None, help="Device serial")
    inspect_parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: localhost only)")
    inspect_parser.add_argument("--port", type=int, default=17920, help="Bind port")
    inspect_parser.set_defaults(func=cmd_inspect)

    codegen_parser = subparsers.add_parser("codegen", help="Generate automation code from a recorded JSON session")
    codegen_parser.add_argument("input", help="Path to a JSON-exported RecordingSession")
    codegen_parser.add_argument(
        "--format",
        choices=["python", "pytest", "pom", "json", "yaml", "robot", "raw"],
        default="python",
        help="Output format (default: python)",
    )
    codegen_parser.add_argument("-o", "--output", default=None, help="Write to this file instead of stdout")
    codegen_parser.set_defaults(func=cmd_codegen)

    mcp_parser = subparsers.add_parser("mcp", help="MCP server commands")
    mcp_subparsers = mcp_parser.add_subparsers(dest="mcp_command")
    mcp_serve_parser = mcp_subparsers.add_parser("serve", help="Start the MCP server")
    mcp_serve_parser.add_argument(
        "--transport", choices=["stdio", "sse", "streamable-http"], default="stdio", help="MCP transport"
    )
    mcp_serve_parser.add_argument("--host", default="127.0.0.1", help="Bind host (non-stdio transports only)")
    mcp_serve_parser.add_argument("--port", type=int, default=17921, help="Bind port (non-stdio transports only)")
    mcp_serve_parser.add_argument(
        "--allow-shell", action="store_true", help="Register the run_script tool (DANGEROUS, opt-in)"
    )
    mcp_serve_parser.set_defaults(func=cmd_mcp_serve)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "command", None):
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
