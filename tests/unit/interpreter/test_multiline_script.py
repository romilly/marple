"""Multi-line dfn support in script runner."""

from marple.script import run_script
from tests.adapters.fake_filesystem import FakeFileSystem


class TestMultiLineDfn:
    def test_multiline_dfn_in_script(self) -> None:
        fs = FakeFileSystem({"/test.apl": "f←{⍵>0:1\n⍵<0:¯1\n0}\nf 5\n"})
        output = run_script("/test.apl", fs=fs)
        assert any("1" == line.strip() for line in output)

    def test_single_line_still_works(self) -> None:
        fs = FakeFileSystem({"/test.apl": "2+3\n"})
        output = run_script("/test.apl", fs=fs)
        assert any("5" in line for line in output)
