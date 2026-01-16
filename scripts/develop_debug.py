#!/usr/bin/env python3

"""
Start Home Assistant in debug mode with debugpy using an automatically chosen free port.
"""

import os
import signal
import socket
import subprocess
import sys
from pathlib import Path

# -------------------------
# Move to workspace root
# -------------------------
os.chdir(Path(__file__).parent.parent)

# -------------------------
# Set PYTHONPATH for custom_components
# -------------------------
custom_components = Path.cwd() / "custom_components"
os.environ["PYTHONPATH"] = f"{os.environ.get('PYTHONPATH', '')}:{custom_components}"

# -------------------------
# Ensure config directory exists
# -------------------------
config_dir = Path.cwd() / "config"
config_dir.mkdir(parents=True, exist_ok=True)

# Ensure Home Assistant config is initialized
subprocess.run(
    ["hass", "--config", str(config_dir), "--script", "ensure_config"], check=True
)


# -------------------------
# Cleanup old Home Assistant processes
# -------------------------
def cleanup_old_ha() -> None:
    """Kill old HA processes to free resources."""
    for pattern in ["hass", "homeassistant"]:
        subprocess.run(["pkill", "-f", pattern], check=False, stderr=subprocess.DEVNULL)


cleanup_old_ha()


# -------------------------
# Function to launch HA safely
# -------------------------
def launch_ha(cmd: list[str]) -> None:
    """Launch HA in a new process group and handle stop signals from VS Code."""
    ha_process = subprocess.Popen(
        cmd, preexec_fn=os.setsid, stdout=sys.stdout, stderr=sys.stderr
    )

    def handle_stop(signum, frame) -> None:
        try:
            os.killpg(os.getpgid(ha_process.pid), signal.SIGTERM)
        except Exception:
            pass

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    ha_process.wait()


# -------------------------
# Start HA with debugpy
# -------------------------
try:
    import debugpy
except ImportError:
    print("Please install debugpy in your .venv: pip install debugpy")
    sys.exit(1)

# Find a free port automatically
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(("", 0))
    DEBUG_PORT = s.getsockname()[1]

debugpy.listen(DEBUG_PORT)
print(f"DEBUG MODE: Waiting for debugger on port {DEBUG_PORT}...")
debugpy.wait_for_client()
print("Debugger attached. Starting Home Assistant...")

launch_ha(
    [sys.executable, "-m", "homeassistant", "--config", str(config_dir), "--debug"]
)
