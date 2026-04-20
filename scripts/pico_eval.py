"""Pico-side eval loop. Deploy to Pico as main.py.

Uses the standard REPL loop with PicoConsole for serial I/O.
PicoConsole handles hex decoding and sentinel framing. The Interpreter
is constructed with array_cls=UlabAPLArray so numeric operations go
through the ulab-compatible hooks (uint16 chars, no-op errstate, no
float64 upcast).
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

# Register UlabAPLArray as the active backend BEFORE importing engine. Engine
# pulls in environment.py which builds _QUAD_DEFAULTS at module load using
# str_to_char_array(""); on the Pico we need that to resolve via uint16
# (NumpyAPLArray's default uint32 is not representable in ulab).
from marple.backend_functions import set_backend_class
from marple.ulab_aplarray import UlabAPLArray
set_backend_class(UlabAPLArray)

from marple.adapters.pico_config import PicoConfig
from marple.adapters.pico_console import PicoConsole
from marple.adapters.pico_timer import PicoTimer
from marple.engine import Interpreter
from marple.repl import run_repl

try:
    from marple_config import settings as _pico_settings  # type: ignore[import-not-found]
except ImportError:
    _pico_settings = {}

console = PicoConsole()

interp = Interpreter(
    config=PicoConfig(_pico_settings),
    console=console,
    timer=PicoTimer(),
    array_cls=UlabAPLArray,
)
run_repl(interp, console, banner=False)
