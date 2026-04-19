# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**marple** - Mini APL in Python Language Experiment. Uses APL arrays (shape + flat data) as the internal data model, inspired by Rodrigo Girão Serrão's RGSPL.

## Version Bumping

Bump the version after **every code change**, without being asked. Update **both** files:
- `pyproject.toml` — `version = "x.y.z"`
- `src/marple/__init__.py` — `__version__ = "x.y.z"`

These must stay in sync. The user needs distinct version numbers to verify which code is running when testing on PRIDE and the terminal REPL.

## Testing

### Test tiers

| Command | What it runs | Target time |
|---------|-------------|-------------|
| `pytest` | Fast tests (default) | ~1.2s |
| `pytest -m slow` | PRIDE, WebSocket, deep TCO, ⎕DL | ~1-8s |
| `pytest tests/e2e/web/test_pride_e2e.py -m slow` | Playwright E2E for PRIDE | ~8s |

The `--ignore=tests/e2e/web` in `pyproject.toml` `addopts` prevents slow imports (Playwright, aiohttp, PrideConsole threading) from affecting fast test times.

### E2E test quality

Playwright tests must verify **actual visible output**, not just DOM state. Check the text content that appears in the session transcript, not just that an element exists. Tests should use the same server configuration as the user (read `~/.marple/config.ini`).

### Background processes

Never leave test processes running in the background. If a test hangs, kill it immediately — stuck processes can interfere with subsequent testing and the user's PRIDE server.

## Problem Handling

**Never move on from a problem without the user's explicit approval.** When you discover a bug, unexpected behaviour, or upstream issue, stop and discuss it. Do not defer it, work around it, or continue to the next task. The user decides when to move on.

## Bulk Changes

**Always commit before bulk replacements** (sed, find-and-replace across files, etc.). Mistakes in bulk operations are hard to spot and easy to make. A commit gives you a clean state to revert to.

## Dependencies

**Always pin dependencies to exact versions** (`==`) in `pyproject.toml`, `requirements.txt`, and `requirements-test.txt`. Never use `>=` or `~=` ranges. This protects against supply-chain injection attacks where a compromised new release could be pulled in automatically.

When adding or upgrading a dependency, specify the exact version you have verified.

## Core Architecture

### Key Components
- **marple/** - Main package directory