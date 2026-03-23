# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**marple** - Mini APL in Python Language Experiment. Uses APL arrays (shape + flat data) as the internal data model, inspired by Rodrigo Girão Serrão's RGSPL.

## Version Bumping

When bumping the version, update **both** files:
- `pyproject.toml` — `version = "x.y.z"`
- `src/marple/__init__.py` — `__version__ = "x.y.z"`

These must stay in sync. `⎕VER` and the REPL banner both read from `__init__.py`.

## Core Architecture

### Key Components
- **marple/** - Main package directory