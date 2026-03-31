#!/bin/bash
# Deploy MARPLE to Raspberry Pi Pico 2
# Usage: ./scripts/deploy.sh

set -e

# Remove __pycache__ dirs before deploying
find src/marple -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

echo "Preparing deployment copies..."
DEPLOY_TMP=$(mktemp -d)
cp -r src/marple "$DEPLOY_TMP/"
trap "rm -rf $DEPLOY_TMP" EXIT

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
    cp $DEPLOY_TMP/marple/__init__.py :marple/__init__.py + \
    cp $DEPLOY_TMP/marple/arraymodel.py :marple/arraymodel.py + \
    cp $DEPLOY_TMP/marple/backend.py :marple/backend.py + \
    cp $DEPLOY_TMP/marple/cells.py :marple/cells.py + \
    cp $DEPLOY_TMP/marple/dfn_binding.py :marple/dfn_binding.py + \
    cp $DEPLOY_TMP/marple/dyadic_functions.py :marple/dyadic_functions.py + \
    cp $DEPLOY_TMP/marple/engine.py :marple/engine.py + \
    cp $DEPLOY_TMP/marple/environment.py :marple/environment.py + \
    cp $DEPLOY_TMP/marple/errors.py :marple/errors.py + \
    cp $DEPLOY_TMP/marple/executor.py :marple/executor.py + \
    cp $DEPLOY_TMP/marple/fmt.py :marple/fmt.py + \
    cp $DEPLOY_TMP/marple/formatting.py :marple/formatting.py + \
    cp $DEPLOY_TMP/marple/functions.py :marple/functions.py + \
    cp $DEPLOY_TMP/marple/glyphs.py :marple/glyphs.py + \
    cp $DEPLOY_TMP/marple/monadic_functions.py :marple/monadic_functions.py + \
    cp $DEPLOY_TMP/marple/namespace.py :marple/namespace.py + \
    cp $DEPLOY_TMP/marple/nodes.py :marple/nodes.py + \
    cp $DEPLOY_TMP/marple/operator_binding.py :marple/operator_binding.py + \
    cp $DEPLOY_TMP/marple/parser.py :marple/parser.py + \
    cp $DEPLOY_TMP/marple/repl.py :marple/repl.py + \
    cp $DEPLOY_TMP/marple/script.py :marple/script.py + \
    cp $DEPLOY_TMP/marple/structural.py :marple/structural.py + \
    cp $DEPLOY_TMP/marple/symbol_table.py :marple/symbol_table.py + \
    cp $DEPLOY_TMP/marple/terminal.py :marple/terminal.py + \
    cp $DEPLOY_TMP/marple/system_commands.py :marple/system_commands.py + \
    cp $DEPLOY_TMP/marple/tokenizer.py :marple/tokenizer.py + \
    cp $DEPLOY_TMP/marple/workspace.py :marple/workspace.py + \
    cp $DEPLOY_TMP/marple/ports/__init__.py :marple/ports/__init__.py + \
    cp $DEPLOY_TMP/marple/ports/config.py :marple/ports/config.py + \
    cp $DEPLOY_TMP/marple/ports/console.py :marple/ports/console.py + \
    cp $DEPLOY_TMP/marple/ports/filesystem.py :marple/ports/filesystem.py + \
    cp $DEPLOY_TMP/marple/adapters/__init__.py :marple/adapters/__init__.py + \
    cp $DEPLOY_TMP/marple/adapters/default_config.py :marple/adapters/default_config.py + \
    cp $DEPLOY_TMP/marple/adapters/buffered_console.py :marple/adapters/buffered_console.py + \
    cp $DEPLOY_TMP/marple/adapters/pico_console.py :marple/adapters/pico_console.py + \
    cp $DEPLOY_TMP/marple/adapters/os_filesystem.py :marple/adapters/os_filesystem.py + \
    cp $DEPLOY_TMP/marple/adapters/pico_config.py :marple/adapters/pico_config.py + \
    cp $DEPLOY_TMP/marple/adapters/terminal_console.py :marple/adapters/terminal_console.py + \
    cp $DEPLOY_TMP/marple/stdlib/__init__.py :marple/stdlib/__init__.py + \
    cp $DEPLOY_TMP/marple/stdlib/str_impl.py :marple/stdlib/str_impl.py + \
    cp $DEPLOY_TMP/marple/stdlib/str/lower.apl :marple/stdlib/str/lower.apl + \
    cp $DEPLOY_TMP/marple/stdlib/str/trim.apl :marple/stdlib/str/trim.apl + \
    cp $DEPLOY_TMP/marple/stdlib/str/upper.apl :marple/stdlib/str/upper.apl + \
    cp pico_stubs/abc.py :abc.py + \
    cp pico_stubs/typing.py :typing.py + \
    cp data/incoming/apl_font.py :apl_font.py + \
    cp scripts/presto_display.py :presto_display.py + \
    cp scripts/pico_eval.py :main.py + \
    cp scripts/marple_config.py :marple_config.py + \
    cp scripts/WIFI_CONFIG.py :WIFI_CONFIG.py + \
    reset
echo "Deployed. Pico will run eval loop on restart."
echo "Connect with: python scripts/pico_client.py"
