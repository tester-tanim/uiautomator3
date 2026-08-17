from unittest.mock import MagicMock, patch

from uiautomator3.diagnostics.doctor import run_doctor


@patch("uiautomator3.diagnostics.doctor.adbutils")
@patch("uiautomator3.diagnostics.doctor.shutil.which", return_value="/usr/bin/adb")
def test_doctor_reports_ok_with_authorized_device(_mock_which, mock_adbutils):
    device = MagicMock()
    device.serial = "emulator-5554"
    device.get_state.return_value = "device"
    mock_adbutils.adb.device_list.return_value = [device]

    report = run_doctor()

    assert report.all_ok
    names = [c.name for c in report.checks]
    assert "Python version" in names
    assert "adb binary on PATH" in names
    assert any("Device authorization" in n for n in names)


@patch("uiautomator3.diagnostics.doctor.adbutils")
@patch("uiautomator3.diagnostics.doctor.shutil.which", return_value=None)
def test_doctor_fails_without_adb_binary(_mock_which, mock_adbutils):
    mock_adbutils.adb.device_list.return_value = []

    report = run_doctor()

    assert not report.all_ok


def test_format_includes_all_check_names():
    report = run_doctor()
    text = report.format()
    for check in report.checks:
        assert check.name in text
