from __future__ import annotations

from typing import Any

from marple.interpreter import interpret


def main() -> None:
    env: dict[str, Any] = {}
    print("MARPLE - Mini APL in Python")
    print("Type an APL expression, or 'quit' to exit.\n")
    while True:
        try:
            line = input("      ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        line = line.strip()
        if not line:
            continue
        if line.lower() == "quit":
            break
        try:
            result = interpret(line, env)
            # Display result
            if result.is_scalar():
                print(result.data[0])
            elif len(result.shape) == 1:
                print(" ".join(str(x) for x in result.data))
            elif len(result.shape) == 2:
                rows, cols = result.shape
                for r in range(rows):
                    row_data = result.data[r * cols : (r + 1) * cols]
                    print(" ".join(str(x) for x in row_data))
            else:
                print(result)
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
