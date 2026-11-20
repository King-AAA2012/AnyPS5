"""Regression test for the pad-command file being held open while writing.

Windows lets a process open a file for reading with a shared lock; a plain
rename/replace onto that path fails with WinError 5 until the handle is
released. The pad_input/pad_timeline writers must queue input even while the
command file is held open by another process, then have it appear once the
handle is released (the runtime re-opens the path on every call).
"""
import ctypes
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
PYTHON = sys.executable


def _wfopen(path, mode):
    ucrt = ctypes.CDLL("ucrtbase")
    ucrt._wfopen.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
    ucrt._wfopen.restype = ctypes.c_void_p
    ucrt.fclose.argtypes = [ctypes.c_void_p]
    handle = ucrt._wfopen(str(path), mode)
    return handle, ucrt


def _write(tool, command, extra=None):
    args = [PYTHON, str(TOOLS / tool)] + (list(extra) if extra else []) + [str(command)]
    return subprocess.run(args, capture_output=True, text=True)


def _run(tool, command, timeline=None):
    if timeline is not None:
        return _write(tool, command, [str(timeline)])
    return _write(tool, command, ["cross"])


def test_tool_holds_read_handle(tool, command, timeline=None):
    with tempfile.TemporaryDirectory(dir=TOOLS) as folder:
        directory = Path(folder)
        command = directory / "input.cmd"
        timeline = timeline or (directory / "timeline.json")
        if timeline is not None:
            timeline.write_text(
                json.dumps(
                    {"version": 1, "events": [{"at_ms": 0, "hold_ms": 300, "buttons": ["cross"]}]}
                ),
                encoding="utf-8",
            )
        command.write_bytes(b"1 0 50\n")
        original = command.read_bytes()
        handle, ucrt = _wfopen(command, "rb")          # hold a read handle open
        first = _run(tool, command, timeline)          # first write while held -> may fail
        ucrt.fclose(handle)                            # release the handle
        second = _run(tool, command, timeline)         # re-run after release -> must succeed
        if first.returncode != 0 and second.returncode != 0:
            return False, second.returncode, second.stderr.strip().splitlines()[-1]
        if second.returncode != 0 or command.read_bytes() != original:
            return False, second.returncode, second.stderr.strip().splitlines()[-1]
        return True, 0, ""


def main():
    ok = True
    with tempfile.TemporaryDirectory(dir=TOOLS) as folder:
        directory = Path(folder)
        command = directory / "input.cmd"
        timeline = directory / "timeline.json"
        timeline.write_text(
            json.dumps(
                {"version": 1, "events": [{"at_ms": 0, "hold_ms": 300, "buttons": ["cross"]}]}
            ),
            encoding="utf-8",
        )
        command.write_bytes(b"1 0 50\n")
        for tool in ("pad_input.py", "pad_timeline.py"):
            passed, code, detail = test_tool_holds_read_handle(tool, command, timeline)
            status = "PASS" if passed else "FAIL"
            print(f"{tool}: {status} (rc={code}) {detail}")
            ok = ok and passed
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
