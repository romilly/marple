# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**marple** - Mini APL in Python Language Experiment. Uses APL arrays (shape + flat data) as the internal data model, inspired by Rodrigo Girão Serrão's RGSPL.

## Version Bumping

Bump the version after **every code change**, without being asked. Update **both** files:
- `pyproject.toml` — `version = "x.y.z"`
- `src/marple/__init__.py` — `__version__ = "x.y.z"`

These must stay in sync. The user needs distinct version numbers to verify which code is running when testing on PRIDE, Pico, and the terminal REPL.

## MicroPython Compatibility

MARPLE runs on the Raspberry Pi Pico 2 via MicroPython. Code in `src/marple/` must avoid:
- **`dataclasses`** — use plain classes with `__init__`
- **`importlib`** — use `__import__()` with `getattr` to walk dotted paths
- **`os.path`** — use `os.stat()` with try/except for existence checks, bit masks for is_file/is_dir
- **`os.makedirs`** — use `os.mkdir` in a loop

MicroPython **ignores type annotations** — they are not evaluated at runtime, so `str | None` etc. are safe.

The deploy script (`scripts/deploy.sh`) strips `from __future__ import annotations` from all `.py` files before copying to the Pico.

## Testing

### Test tiers

| Command | What it runs | Target time |
|---------|-------------|-------------|
| `pytest` | Fast tests (default) | ~1.2s |
| `pytest -m slow` | PRIDE, WebSocket, deep TCO, ⎕DL | ~1-8s |
| `pytest tests/web/test_pride_e2e.py -m slow` | Playwright E2E for PRIDE | ~8s |
| `pytest tests/pico/test_pico_e2e.py -m pico` | Pico hardware tests | ~40s |

The `--ignore=tests/web` in `pyproject.toml` `addopts` prevents slow imports (Playwright, aiohttp, PrideConsole threading) from affecting fast test times.

### E2E test quality

Playwright tests must verify **actual visible output**, not just DOM state. Check the text content that appears in the session transcript, not just that an element exists. Tests should use the same server configuration as the user (read `~/.marple/config.ini`).

### Pico compatibility tests

`tests/test_pico_compat.py` checks that deployed code doesn't use MicroPython-incompatible modules (dataclasses, importlib, os.path). Run these as part of the fast suite.

### Background processes

Never leave test processes running in the background. If a test hangs, kill it immediately — stuck processes can interfere with subsequent testing and the user's PRIDE server.

## Dependencies

**Always pin dependencies to exact versions** (`==`) in `pyproject.toml`, `requirements.txt`, and `requirements-test.txt`. Never use `>=` or `~=` ranges. This protects against supply-chain injection attacks where a compromised new release could be pulled in automatically.

When adding or upgrading a dependency, specify the exact version you have verified.

## Core Architecture

### Key Components
- **marple/** - Main package directory