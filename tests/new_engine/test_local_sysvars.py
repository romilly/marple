"""System variables should be local to dfns."""

from marple.numpy_array import S
from marple.engine import Interpreter


class TestLocalSysvars:
    def test_io_set_in_dfn_does_not_leak(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{⎕IO←0 ⋄ ⍳3}")
        i.run("f 0")
        assert i.run("⎕IO") == S(1)

    def test_pp_set_in_dfn_does_not_leak(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{⎕PP←3 ⋄ ⍵}")
        i.run("f 0")
        assert i.run("⎕PP") == S(10)
