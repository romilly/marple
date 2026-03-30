# MARPLE Architecture

MARPLE uses hexagonal architecture with ports and adapters for testable I/O.

| Module | Purpose |
|--------|---------|
| `arraymodel.py` | `APLArray(shape, data)` — the core data structure |
| `backend.py` | Numpy/ulab detection with pure-Python fallback |
| `tokenizer.py` | Lexer for APL glyphs, numbers, strings, qualified names |
| `parser.py` | Iverson stack-based parser with operator binding precedence |
| `nodes.py` | AST node classes with execute methods |
| `executor.py` | Base evaluator with system function dispatch |
| `engine.py` | `Interpreter` class — parse and evaluate APL source |
| `dfn_binding.py` | Dfn/dop evaluation with tail call optimization |
| `environment.py` | Workspace state — variables, system settings, name table |
| `symbol_table.py` | Name class tracking (array/function/operator) |
| `functions.py` | Scalar functions with pervasion (numpy-accelerated) |
| `monadic_functions.py` | Monadic function dispatch |
| `dyadic_functions.py` | Dyadic function dispatch |
| `structural.py` | Shape-manipulating and indexing functions |
| `operator_binding.py` | Reduce, scan, replicate operators |
| `cells.py` | Cell decomposition and reassembly for the rank operator |
| `fmt.py` | Dyadic ⎕FMT format specification parser |
| `namespace.py` | Hierarchical namespace resolution and system workspace |
| `errors.py` | APL error classes with numeric codes |
| `ports/console.py` | Console port — abstract REPL I/O interface |
| `ports/filesystem.py` | FileSystem port — abstract file I/O interface |
| `adapters/terminal_console.py` | Real Console adapter (terminal + stdout) |
| `adapters/buffered_console.py` | Buffered Console adapter (scripts, Jupyter) |
| `adapters/pride_console.py` | Threaded Console adapter (PRIDE WebSocket I/O) |
| `adapters/os_filesystem.py` | Real FileSystem adapter (os module) |
| `repl.py` | Interactive read-eval-print loop (uses Console port) |
| `script.py` | Script runner with multi-line dfn support |
| `terminal.py` | Raw terminal input with live glyph translation (Linux) |
| `glyphs.py` | Backtick → APL character mapping |
| `workspace.py` | Directory-based workspace persistence |
| `config.py` | User configuration (~/.marple/config.ini) |
| `stdlib/` | Standard library: string functions |
| `system_commands.py` | Shared system command dispatcher |
| `web/server.py` | PRIDE web IDE server (aiohttp + WebSocket) |
| `jupyter/kernel.py` | Jupyter kernel (wraps Interpreter.execute) |
| `jupyter/html_render.py` | APLArray → HTML table conversion |
| `pico_stubs/` | MicroPython stub modules for abc and typing |
