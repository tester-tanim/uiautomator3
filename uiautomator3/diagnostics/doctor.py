"""`u3 doctor` — environment sanity checks.

Phase 1 scope: python, adb availability, connected devices, device
authorization. Later phases add checks for the device-side agent,
port availability, OCR/CV optional dependencies (see project spec section
42).
"""
import shutil
import sys
from dataclasses import dataclass, field
from typing import List

import adbutils

from uiautomator3.logging_config import get_logger

logger = get_logger("diagnostics.doctor")


@dataclass
class CheckResult:
    name: str
    ok: bool
    message: str = ""


@dataclass
class DoctorReport:
    checks: List[CheckResult] = field(default_factory=list)

    @property
    def all_ok(self) -> bool:
        return all(c.ok for c in self.checks)

    def format(self) -> str:
        lines = ["UIAutomator 3.0 Doctor Report", "=" * 32]
        for c in self.checks:
            status = "OK" if c.ok else "FAIL"
            lines.append(f"[{status}] {c.name}" + (f" - {c.message}" if c.message else ""))
        return "\n".join(lines)


def run_doctor() -> DoctorReport:
    report = DoctorReport()

    report.checks.append(
        CheckResult(
            "Python version",
            sys.version_info >= (3, 8),
            f"{sys.version.split()[0]} (requires >= 3.8)",
        )
    )

    adb_path = shutil.which("adb")
    report.checks.append(
        CheckResult("adb binary on PATH", adb_path is not None, adb_path or "adb not found on PATH")
    )

    try:
        device_list = list(adbutils.adb.device_list())
        report.checks.append(
            CheckResult(
                "ADB server reachable",
                True,
                f"{len(device_list)} device(s) found",
            )
        )
    except Exception as e:
        report.checks.append(CheckResult("ADB server reachable", False, str(e)))
        device_list = []

    if not device_list:
        report.checks.append(CheckResult("Device authorization", False, "no devices attached"))
    else:
        for d in device_list:
            try:
                state = d.get_state()
                ok = state == "device"
                msg = f"{d.serial}: {state}"
            except Exception as e:
                ok = False
                msg = f"{d.serial}: {e}"
            report.checks.append(CheckResult(f"Device authorization ({d.serial})", ok, msg))

    return report
