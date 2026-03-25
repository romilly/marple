"""Record a PRIDE demo video using Playwright.

Reads a .marple script and types each expression into PRIDE,
character by character with realistic delays. Records as WebM,
converts to MP4 with ffmpeg if available.

The server must be running: python -m marple.web.server

Usage:
    python scripts/pride_demo.py examples/01_primitives.marple
    python scripts/pride_demo.py examples/01_primitives.marple --output demos/demo1.mp4
    python scripts/pride_demo.py examples/01_primitives.marple --width 1280 --height 720
"""

import argparse
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


CHAR_DELAY = 40       # ms between characters
PAUSE_AFTER = 800     # ms to pause after each result
COMMENT_PAUSE = 1200  # ms to pause on comment lines
INITIAL_PAUSE = 1500  # ms to wait after page load
SERVER_URL = "http://localhost:8888"


def type_expression(page, expr: str) -> None:
    """Type an APL expression into the input, character by character.

    Uses direct JavaScript value assignment to avoid triggering
    browser autocomplete or other event-driven side effects.
    """
    import json as _json
    for i in range(len(expr)):
        partial = _json.dumps(expr[:i + 1])
        page.evaluate(f'document.getElementById("input").value = {partial}')
        page.wait_for_timeout(CHAR_DELAY)


def submit_and_wait(page) -> None:
    """Press Enter and wait for the result to appear."""
    count_before = page.locator(".entry").count()
    page.locator("#input").press("Enter")
    try:
        page.locator(f".entry:nth-child({count_before + 1})").wait_for(timeout=10000)
    except Exception:
        pass  # timeout — expression may have been silent
    page.wait_for_timeout(PAUSE_AFTER)


def record_demo(script_path: str, output_path: str,
                width: int = 1280, height: int = 720,
                url: str = SERVER_URL) -> str:
    """Record a demo video. Returns the path to the WebM file."""
    video_dir = Path(output_path).parent / ".pride_videos"
    video_dir.mkdir(parents=True, exist_ok=True)

    with open(script_path) as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": width, "height": height},
            record_video_dir=str(video_dir),
            record_video_size={"width": width, "height": height},
        )
        page = context.new_page()
        page.goto(url)
        page.wait_for_timeout(INITIAL_PAUSE)

        for i, line in enumerate(lines):
            print(f"[{i+1}/{len(lines)}] {line}", file=sys.stderr)
            # Check input is clear before typing
            current = page.locator("#input").input_value()
            if current:
                print(f"  WARNING: input not empty: {current!r}", file=sys.stderr)
                page.locator("#input").fill("")
            if line.lstrip().startswith("⍝"):
                # Comment — type it and submit, pause to read
                type_expression(page, line)
                submit_and_wait(page)
                page.wait_for_timeout(COMMENT_PAUSE)
            else:
                type_expression(page, line)
                submit_and_wait(page)

        # Final pause to see the last result
        page.wait_for_timeout(2000)

        context.close()
        webm_path = page.video.path()

    print(f"Recorded: {webm_path}")
    return str(webm_path)


def convert_to_mp4(webm_path: str, mp4_path: str) -> bool:
    """Convert WebM to MP4 using ffmpeg. Returns True on success."""
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", webm_path,
             "-c:v", "libx264", "-preset", "medium",
             "-crf", "23", "-c:a", "aac",
             mp4_path],
            check=True, capture_output=True,
        )
        print(f"Converted: {mp4_path}")
        return True
    except FileNotFoundError:
        print("ffmpeg not found — WebM file saved, convert manually")
        return False
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg error: {e.stderr.decode()}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Record a PRIDE demo video")
    parser.add_argument("script", help="Path to .marple demo script")
    parser.add_argument("--output", "-o", default=None,
                        help="Output MP4 path (default: demos/{script_name}.mp4)")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--url", default=SERVER_URL,
                        help="PRIDE server URL")
    parser.add_argument("--webm-only", action="store_true",
                        help="Skip MP4 conversion")
    args = parser.parse_args()

    script_name = Path(args.script).stem
    if args.output is None:
        output_dir = Path("demos")
        output_dir.mkdir(exist_ok=True)
        args.output = str(output_dir / f"{script_name}.mp4")

    webm_path = record_demo(args.script, args.output,
                            args.width, args.height, args.url)

    if not args.webm_only:
        convert_to_mp4(webm_path, args.output)


if __name__ == "__main__":
    main()
