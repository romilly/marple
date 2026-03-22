import os
import tempfile

from marple.script import run_script


class TestRunScript:
    def test_simple_script(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".marple", delete=False) as f:
            f.write("x←5\n")
            f.write("+x\n")
            path = f.name
        try:
            output = run_script(path)
            assert output == ["5"]
        finally:
            os.unlink(path)

    def test_script_with_comments(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".marple", delete=False) as f:
            f.write("⍝ this is a comment\n")
            f.write("2+3\n")
            path = f.name
        try:
            output = run_script(path)
            assert output == ["5"]
        finally:
            os.unlink(path)

    def test_script_error_stops(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".marple", delete=False) as f:
            f.write("x←5\n")
            f.write("y←x+unknown\n")
            f.write("z←10\n")
            path = f.name
        try:
            output = run_script(path)
            # Should have error message, not reach line 3
            assert any("ERROR" in line for line in output)
            assert any("2" in line for line in output)  # line number
        finally:
            os.unlink(path)

    def test_script_blank_lines_skipped(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".marple", delete=False) as f:
            f.write("x←3\n")
            f.write("\n")
            f.write("x+1\n")
            path = f.name
        try:
            output = run_script(path)
            assert output == ["4"]
        finally:
            os.unlink(path)

    def test_script_assignment_silent(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".marple", delete=False) as f:
            f.write("x←1\n")
            f.write("y←2\n")
            f.write("x+y\n")
            path = f.name
        try:
            output = run_script(path)
            assert output == ["3"]
        finally:
            os.unlink(path)
