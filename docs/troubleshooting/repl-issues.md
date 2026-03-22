# REPL Issues

## Glyph input not working

MARPLE's backtick input requires raw terminal mode. If glyphs are not appearing when you type backtick followed by a key:

- Ensure you are running in an interactive terminal, not a pipe or redirected input
- On Windows, use Windows Terminal or WSL, not the legacy Command Prompt
- Check that your terminal supports ANSI escape sequences
- Try running with `python -m marple` if the `marple` entry point has issues

## APL characters display as boxes or question marks

Your terminal font may not include APL glyphs. Use a font with good Unicode coverage:

- **DejaVu Sans Mono** (most Linux distributions)
- **Noto Sans Mono** (broad Unicode coverage)
- **APL385 Unicode** (purpose-built for APL)
- **JetBrains Mono** (good programming font with APL support)

## Terminal encoding

MARPLE requires UTF-8 encoding. If you see garbled output:

- On Linux/macOS, check that `LANG` or `LC_ALL` includes `.UTF-8` (e.g., `en_US.UTF-8`)
- On Windows, ensure your terminal is set to UTF-8: run `chcp 65001` in Command Prompt

## Workspace save/load problems

Workspaces are saved as directories under `workspaces/` (or the path in `MARPLE_WORKSPACES`). If saves fail:

- Check that you have write permission to the target directory
- Set a workspace ID with `)wsid name` before `)save`
- Check that the `MARPLE_WORKSPACES` path exists if you have set it

## REPL does not start

If `marple` does not launch:

- Check that MARPLE is installed: `pip show marple`
- Try running directly: `python -c "from marple.repl import main; main()"`
- Check for import errors: `python -c "import marple"`
