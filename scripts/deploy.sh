#!/bin/bash
# Deploy MARPLE to Raspberry Pi Pico 2
# Usage: ./scripts/deploy.sh

set -e

# Remove __pycache__ dirs before deploying
find src/marple -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

SRC=src/marple

echo "Cleaning Pico filesystem..."
mpremote rm -r :marple 2>/dev/null || true
mpremote rm :main.py 2>/dev/null || true

echo "Deploying marple to Pico 2..."
mpremote \
    mkdir :marple + \
    mkdir :marple/ports + \
    mkdir :marple/adapters + \
    mkdir :marple/stdlib + \
    mkdir :marple/stdlib/str + \
    cp $SRC/__init__.py :marple/__init__.py + \
    cp $SRC/arraymodel.py :marple/arraymodel.py + \
    cp $SRC/backend.py :marple/backend.py + \
    cp $SRC/cells.py :marple/cells.py + \
    cp $SRC/dfn_binding.py :marple/dfn_binding.py + \
    cp $SRC/dyadic_functions.py :marple/dyadic_functions.py + \
    cp $SRC/engine.py :marple/engine.py + \
    cp $SRC/environment.py :marple/environment.py + \
    cp $SRC/errors.py :marple/errors.py + \
    cp $SRC/executor.py :marple/executor.py + \
    cp $SRC/fmt.py :marple/fmt.py + \
    cp $SRC/formatting.py :marple/formatting.py + \
    cp $SRC/functions.py :marple/functions.py + \
    cp $SRC/glyphs.py :marple/glyphs.py + \
    cp $SRC/monadic_functions.py :marple/monadic_functions.py + \
    cp $SRC/namespace.py :marple/namespace.py + \
    cp $SRC/nodes.py :marple/nodes.py + \
    cp $SRC/operator_binding.py :marple/operator_binding.py + \
    cp $SRC/parser.py :marple/parser.py + \
    cp $SRC/repl.py :marple/repl.py + \
    cp $SRC/script.py :marple/script.py + \
    cp $SRC/structural.py :marple/structural.py + \
    cp $SRC/symbol_table.py :marple/symbol_table.py + \
    cp $SRC/terminal.py :marple/terminal.py + \
    cp $SRC/system_commands.py :marple/system_commands.py + \
    cp $SRC/tokenizer.py :marple/tokenizer.py + \
    cp $SRC/workspace.py :marple/workspace.py + \
    cp $SRC/ports/__init__.py :marple/ports/__init__.py + \
    cp $SRC/ports/config.py :marple/ports/config.py + \
    cp $SRC/ports/console.py :marple/ports/console.py + \
    cp $SRC/ports/filesystem.py :marple/ports/filesystem.py + \
    cp $SRC/ports/timer.py :marple/ports/timer.py + \
    cp $SRC/adapters/__init__.py :marple/adapters/__init__.py + \
    cp $SRC/adapters/default_config.py :marple/adapters/default_config.py + \
    cp $SRC/adapters/buffered_console.py :marple/adapters/buffered_console.py + \
    cp $SRC/adapters/pico_console.py :marple/adapters/pico_console.py + \
    cp $SRC/adapters/os_filesystem.py :marple/adapters/os_filesystem.py + \
    cp $SRC/adapters/pico_config.py :marple/adapters/pico_config.py + \
    cp $SRC/adapters/pico_timer.py :marple/adapters/pico_timer.py + \
    cp $SRC/adapters/desktop_timer.py :marple/adapters/desktop_timer.py + \
    cp $SRC/adapters/terminal_console.py :marple/adapters/terminal_console.py + \
    cp $SRC/adapters/presto_console.py :marple/adapters/presto_console.py + \
    cp $SRC/stdlib/__init__.py :marple/stdlib/__init__.py + \
    cp $SRC/stdlib/str_impl.py :marple/stdlib/str_impl.py + \
    cp $SRC/stdlib/str/lower.apl :marple/stdlib/str/lower.apl + \
    cp $SRC/stdlib/str/trim.apl :marple/stdlib/str/trim.apl + \
    cp $SRC/stdlib/str/upper.apl :marple/stdlib/str/upper.apl + \
    cp pico_stubs/abc.py :abc.py + \
    cp pico_stubs/typing.py :typing.py + \
    cp data/incoming/apl_font.py :apl_font.py + \
    cp scripts/presto_display.py :presto_display.py + \
    cp scripts/pico_eval.py :main.py + \
    cp scripts/marple_config.py :marple_config.py + \
    cp scripts/WIFI_CONFIG.py :WIFI_CONFIG.py

echo "Deploying workspaces..."
mpremote mkdir :workspaces 2>/dev/null || true

for ws_dir in workspaces/*/; do
    ws_name=$(basename "$ws_dir")
    echo "  Workspace: $ws_name"
    mpremote mkdir ":workspaces/$ws_name" 2>/dev/null || true
    for f in "$ws_dir"* "$ws_dir".*; do
        [ -f "$f" ] || continue
        fname=$(basename "$f")
        mpremote cp "$f" ":workspaces/$ws_name/$fname"
    done
done

mpremote reset
echo "Deployed. Pico will run eval loop on restart."
echo "Connect with: python scripts/pico_client.py"
