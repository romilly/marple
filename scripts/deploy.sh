#!/bin/bash
# Deploy MARPLE to Raspberry Pi Pico 2
# Usage: ./scripts/deploy.sh

set -e

# Remove __pycache__ dirs before deploying
find src/marple -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

echo "Cleaning Pico filesystem..."
mpremote rm -r :marple 2>/dev/null || true
mpremote rm :main.py 2>/dev/null || true

echo "Deploying marple to Pico 2..."
mpremote \
    mkdir :marple + \
    mkdir :marple/stdlib + \
    mkdir :marple/stdlib/io + \
    mkdir :marple/stdlib/str + \
    cp src/marple/__init__.py :marple/__init__.py + \
    cp src/marple/arraymodel.py :marple/arraymodel.py + \
    cp src/marple/backend.py :marple/backend.py + \
    cp src/marple/cells.py :marple/cells.py + \
    cp src/marple/errors.py :marple/errors.py + \
    cp src/marple/functions.py :marple/functions.py + \
    cp src/marple/glyphs.py :marple/glyphs.py + \
    cp src/marple/interpreter.py :marple/interpreter.py + \
    cp src/marple/parser.py :marple/parser.py + \
    cp src/marple/repl.py :marple/repl.py + \
    cp src/marple/structural.py :marple/structural.py + \
    cp src/marple/terminal.py :marple/terminal.py + \
    cp src/marple/tokenizer.py :marple/tokenizer.py + \
    cp src/marple/namespace.py :marple/namespace.py + \
    cp src/marple/stdlib/__init__.py :marple/stdlib/__init__.py + \
    cp src/marple/stdlib/io_impl.py :marple/stdlib/io_impl.py + \
    cp src/marple/stdlib/str_impl.py :marple/stdlib/str_impl.py + \
    cp src/marple/stdlib/io/nread.apl :marple/stdlib/io/nread.apl + \
    cp src/marple/stdlib/io/nwrite.apl :marple/stdlib/io/nwrite.apl + \
    cp src/marple/stdlib/str/lower.apl :marple/stdlib/str/lower.apl + \
    cp src/marple/stdlib/str/trim.apl :marple/stdlib/str/trim.apl + \
    cp src/marple/stdlib/str/upper.apl :marple/stdlib/str/upper.apl + \
    cp scripts/pico_eval.py :main.py
echo "Deployed. Pico will run eval loop on restart."
echo "Connect with: python scripts/pico_client.py"
