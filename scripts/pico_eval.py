"""Pico-side eval loop. Deploy to Pico as main.py.

Uses the standard REPL loop with PicoConsole for serial I/O.
PicoConsole handles hex decoding and sentinel framing.

If running on a Pimoroni Presto, wraps the console with
PrestoConsole to mirror the session to the 480x480 LCD.
"""
import sys
import time
sys.path.insert(0, "")

# Sync RTC via NTP if WiFi config is available (Pico W only)
try:
    import network  # type: ignore[import-not-found]
    import ntptime  # type: ignore[import-not-found]
    import WIFI_CONFIG  # type: ignore[import-not-found]
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_CONFIG.SSID, WIFI_CONFIG.PASSWORD)
    for _ in range(20):
        if wlan.isconnected():
            break
        time.sleep(1)
    if wlan.isconnected():
        ntptime.settime()
except (ImportError, OSError):
    pass  # No WiFi — RTC will be unset

from marple.adapters.pico_config import PicoConfig
from marple.adapters.pico_console import PicoConsole
from marple.engine import Interpreter
from marple.repl import run_repl
import marple

try:
    from marple_config import settings as _pico_settings  # type: ignore[import-not-found]
except ImportError:
    _pico_settings = {}

console = PicoConsole()

# Optional Presto LCD display — wrap console if available
try:
    from presto_display import PrestoDisplay  # type: ignore[import-not-found]
    from marple.adapters.presto_console import PrestoConsole  # type: ignore[import-not-found]
    lcd = PrestoDisplay()
    lcd.show_banner("MARPLE v" + marple.__version__)
    lcd.show_banner("CLEAR WS")
    console = PrestoConsole(console, lcd)
except ImportError:
    pass

interp = Interpreter(config=PicoConfig(_pico_settings), console=console)
run_repl(interp, console, banner=False)
