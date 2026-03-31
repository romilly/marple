# Config Refactoring — Step by Step

## Goal

Replace the current `config.py` (which uses `ConfigParser` and `os.path` — CPython only) with an abstract `Config` class and platform-specific implementations. The Pico will gain the ability to be configured.

## Current State

`config.py` exports three functions:
- `get_default_io() -> int` — default `⎕IO` (1)
- `get_workspaces_dir() -> str` — workspace root ("workspaces")
- `get_sessions_dir() -> str` — session root ("sessions") **— never actually called anywhere**

Callers:
- `engine.py:38` — `get_default_io()` in `Interpreter.__init__`
- `system_commands.py:72,80,105` — `get_workspaces_dir()` in `)LIB`, `)SAVE`, `)LOAD`
- Nobody calls `get_sessions_dir()` (the web server hardcodes "sessions")

On MicroPython, `ConfigParser` import fails, `_config = None`, and all functions return hardcoded defaults. The Pico cannot be configured.

## Target State

```
Config (ABC)
├── DesktopConfig — reads ~/.marple/config.ini via ConfigParser
└── PicoConfig — reads /config.py as a Python dict
```

The interpreter receives a `Config` instance (like it receives `Console` and `FileSystem`). All config access goes through the abstract interface.

## Steps (TDD, baby steps)

### Step 1: Write the abstract Config class

**Test:** A test that imports `Config` and verifies it has the three abstract methods.

**Code:** Create `src/marple/ports/config.py` with:
```python
from abc import ABC, abstractmethod

class Config(ABC):
    @abstractmethod
    def get_default_io(self) -> int: ...
    @abstractmethod
    def get_workspaces_dir(self) -> str: ...
    @abstractmethod
    def get_sessions_dir(self) -> str: ...
```

**Files:** `src/marple/ports/config.py` (new), test file

### Step 2: Create DesktopConfig adapter

**Test:** Create a `DesktopConfig` with a temp config.ini, verify it reads `io`, `workspaces`, `sessions` correctly. Also test defaults when no config file exists.

**Code:** Create `src/marple/adapters/desktop_config.py` — move the current `ConfigParser` logic from `config.py` into this class.

**Files:** `src/marple/adapters/desktop_config.py` (new), test file

### Step 3: Create FakeConfig for testing

**Test:** Create a `FakeConfig` with specified values, verify they're returned.

**Code:** Create `tests/adapters/fake_config.py` — simple implementation that returns constructor arguments.

**Files:** `tests/adapters/fake_config.py` (new), test file

### Step 4: Create PicoConfig adapter

**Test:** Create a `PicoConfig` that reads from a Python dict, verify values. Test defaults when no dict provided.

**Code:** Create `src/marple/adapters/pico_config.py` — reads from a Python dict (on the Pico this would be an importable `/config.py` file).

**Files:** `src/marple/adapters/pico_config.py` (new), test file

### Step 5: Wire Config into Environment

**Test:** Create an `Interpreter` with a `FakeConfig(io=0)`, verify `⎕IO` is 0. Create with `FakeConfig(io=1)`, verify `⎕IO` is 1.

**Code:** Add `config` parameter to `Environment.__init__` and `Interpreter.__init__`, like we did with `console`. `Interpreter.__init__` uses `config.get_default_io()` instead of calling the module-level function.

**Files:** `src/marple/environment.py`, `src/marple/engine.py`, test file

### Step 6: Wire Config into system commands

**Test:** Use `FakeConfig(workspaces_dir=tmp_path)` and verify `)LIB`, `)SAVE`, `)LOAD` use the configured directory.

**Code:** `system_commands.py` gets the workspaces dir from the interpreter's config instead of calling the module-level function. The command handlers need access to config — either via the interpreter or passed explicitly.

**Files:** `src/marple/system_commands.py`, test file

### Step 7: Wire Config into web server sessions

**Test:** Create a web server with a `FakeConfig(sessions_dir=tmp_path)`, verify session save/load uses the configured directory.

**Code:** `WebSession` and `WSHandler` get sessions dir from config instead of hardcoded "sessions".

**Files:** `src/marple/web/server.py`, test file

### Step 8: Wire default Config creation into entry points

**Test:** Start the REPL (via `FakeConsole`), verify it uses `DesktopConfig` by default. Verify `pico_eval.py` would use `PicoConfig`.

**Code:** Update entry points:
- `repl.py:main()` — creates `DesktopConfig()`, passes to `Interpreter`
- `web/server.py:create_app()` — creates `DesktopConfig()`, passes to `WebSession`
- `scripts/pico_eval.py` — creates `PicoConfig()`, passes to `Interpreter`

**Files:** `src/marple/repl.py`, `src/marple/web/server.py`, `scripts/pico_eval.py`

### Step 9: Update deploy script and test on Pico

**Test:** Run pico compat tests on Linux. Deploy to Pico. Verify it starts, displays version, and `⎕IO` can be configured. Run Pico E2E tests.

**Code:**
- Add `pico_config.py` and `ports/config.py` to deploy script
- Create a default config dict file for the Pico with `io=1`
- Add pico compat checks to `tests/test_pico_compat.py`

**Files:** `scripts/deploy.sh`, Pico config file, `tests/test_pico_compat.py`

### Step 10: Remove old config.py

Only after the Pico is verified working with the new Config abstraction.

**Test:** Verify no imports of `marple.config` remain (except possibly a re-export for backward compatibility). Run full test suite. Deploy to Pico again and re-run Pico E2E tests.

**Code:** Delete `src/marple/config.py` or reduce it to a thin wrapper that creates `DesktopConfig()` for backward compatibility. Remove from deploy script if no longer needed on Pico.

**Files:** `src/marple/config.py` (delete or reduce), `scripts/deploy.sh`

## Verification

After all steps:
- `pytest` — fast tests pass in ~1.2s
- `pytest -m slow` — slow tests pass
- `pyright src/` — no new errors
- Deploy to Pico, verify it starts and `⎕IO` can be configured
- Run Pico E2E tests
- Only then remove old code

## Key Files

| File | Action |
|------|--------|
| `src/marple/ports/config.py` | New — abstract Config ABC |
| `src/marple/adapters/desktop_config.py` | New — ConfigParser implementation |
| `src/marple/adapters/pico_config.py` | New — Python dict implementation |
| `tests/adapters/fake_config.py` | New — test adapter |
| `src/marple/config.py` | Delete or reduce to wrapper |
| `src/marple/engine.py` | Add config parameter |
| `src/marple/environment.py` | Add config parameter |
| `src/marple/system_commands.py` | Use config for workspace dir |
| `src/marple/web/server.py` | Use config for session dir |
| `src/marple/repl.py` | Create DesktopConfig at entry point |
| `scripts/pico_eval.py` | Create PicoConfig at entry point |
| `scripts/deploy.sh` | Update for new files |
| `tests/test_pico_compat.py` | Add config checks |

## Notes

- Each step is a single TDD cycle: failing test → minimal code → refactor → commit
- Steps 1-4 add new code without touching existing code — safe
- Steps 5-8 wire in the new code, replacing old callers one at a time
- Step 9 removes old code only after all callers are migrated
- The `io` parameter on `Interpreter.__init__` should remain as an override (tests use it extensively)
