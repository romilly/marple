# Changelog

The full changelog is maintained in [CHANGELOG.md](https://github.com/romilly/marple/blob/main/CHANGELOG.md) at the project root.

## Current version: 0.3.6

### Highlights

- **Web REPL** — browser-based REPL with Bootstrap layout, language bar, workspace panel, session history, and multi-line input
- **Published to PyPI** as `marple-lang` — install with `uv pip install marple-lang`
- **12 system variables and functions** — `⎕PP`, `⎕A`, `⎕D`, `⎕TS`, `⎕WSID`, `⎕RL`, `⎕EN`, `⎕DM`, `⎕EA`, `⎕UCS`, `⎕NC`, `⎕EX`, `⎕SIGNAL`
- **Roll and deal** (`?`) with `⎕RL` for deterministic random
- **Numpy optimisations** — outer product 380x faster, inner product correct for any rank
- **Symbol table-aware parser** — named functions work without parentheses
- **448 tests** (412 interpreter + 36 Playwright)

See the [full changelog](https://github.com/romilly/marple/blob/main/CHANGELOG.md) for complete version history.
