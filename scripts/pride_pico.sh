#!/bin/bash
# Start PRIDE web IDE with Pico evaluation
PORT="${1:-/dev/ttyACM0}"
python -m marple.web.server --pico-port "$PORT"
