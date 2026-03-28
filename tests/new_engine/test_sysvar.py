"""System variable and system function tests — new engine."""

import pytest

from marple.arraymodel import APLArray, S
from marple.engine import Interpreter
from marple.errors import DomainError


class TestQuadIO:
    def test_default_io(self) -> None:
        assert Interpreter(io=1).run("⎕IO") == S(1)

    def test_io_zero(self) -> None:
        assert Interpreter(io=0).run("⎕IO") == S(0)

    def test_iota_with_io0(self) -> None:
        assert Interpreter(io=0).run("⍳3") == APLArray([3], [0, 1, 2])

    def test_indexing_with_io0(self) -> None:
        i = Interpreter(io=0)
        i.run("v←10 20 30")
        assert i.run("v[0]") == S(10)


class TestQuadPP:
    def test_default_pp(self) -> None:
        assert Interpreter(io=1).run("⎕PP") == S(10)

    def test_set_pp(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕PP←5")
        assert i.run("⎕PP") == S(5)


class TestQuadA:
    def test_quad_a(self) -> None:
        result = Interpreter(io=1).run("⎕A")
        assert result.shape == [26]

    def test_quad_a_readonly(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("⎕A←1")


class TestQuadD:
    def test_quad_d(self) -> None:
        result = Interpreter(io=1).run("⎕D")
        assert result.shape == [10]

    def test_quad_d_readonly(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("⎕D←1")


class TestQuadTS:
    def test_quad_ts_shape(self) -> None:
        result = Interpreter(io=1).run("⎕TS")
        assert result.shape == [7]

    def test_quad_ts_year(self) -> None:
        result = Interpreter(io=1).run("⎕TS")
        assert result.data[0] >= 2024


class TestQuadWSID:
    def test_default_wsid(self) -> None:
        result = Interpreter(io=1).run("⎕WSID")
        assert len(result.data) > 0

    def test_set_wsid(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕WSID←'MYWS'")
        result = i.run("⎕WSID")
        assert "".join(str(c) for c in result.data) == "MYWS"


class TestSystemFunctions:
    def test_ucs_to_char(self) -> None:
        assert Interpreter(io=1).run("⎕UCS 65") == S("A")

    def test_ucs_to_code(self) -> None:
        result = Interpreter(io=1).run("⎕UCS 'A'")
        assert result == APLArray([1], [65])

    def test_dr_integer(self) -> None:
        assert Interpreter(io=1).run("⎕DR 42") == S(323)

    def test_dr_char(self) -> None:
        assert Interpreter(io=1).run("⎕DR 'hello'") == S(80)

    def test_signal(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("⎕SIGNAL 3")

    def test_nc_undefined(self) -> None:
        assert Interpreter(io=1).run("⎕NC 'xyz'") == S(0)

    def test_nc_variable(self) -> None:
        i = Interpreter(io=1)
        i.run("x←5")
        assert i.run("⎕NC 'x'") == S(2)

    def test_nc_function(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{⍵+1}")
        assert i.run("⎕NC 'f'") == S(3)

    def test_ex(self) -> None:
        i = Interpreter(io=1)
        i.run("x←42")
        i.run("⎕EX 'x'")
        assert i.run("⎕NC 'x'") == S(0)

    def test_nl(self) -> None:
        i = Interpreter(io=1)
        i.run("foo←{⍵+1}")
        i.run("bar←{⍵×2}")
        result = i.run("⎕NL 3")
        assert result.shape[0] == 2


class TestEA:
    def test_ea_traps_error(self) -> None:
        assert Interpreter(io=1).run("'0' ⎕EA '1÷0'") == S(0)

    def test_ea_no_error(self) -> None:
        assert Interpreter(io=1).run("'99' ⎕EA '2+3'") == S(5)


class TestDyadicDR:
    def test_dr_to_char(self) -> None:
        result = Interpreter(io=1).run("80 ⎕DR 65 66 67")
        assert list(result.data) == ["A", "B", "C"]


class TestCR:
    def test_cr(self) -> None:
        i = Interpreter(io=1)
        i.run("add←{⍺+⍵}")
        result = i.run("⎕CR 'add'")
        assert result.shape[0] >= 1


class TestFX:
    def test_fx(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕FX 'inc←{⍵+1}'")
        assert i.run("inc 5") == S(6)


class TestDL:
    def test_dl(self) -> None:
        result = Interpreter(io=1).run("⎕DL 0.01")
        assert result.data[0] >= 0.01


class TestFmt:
    def test_monadic_fmt_scalar(self) -> None:
        result = Interpreter(io=1).run("⎕FMT 42")
        assert list(result.data) == ["4", "2"]

    def test_monadic_fmt_vector(self) -> None:
        result = Interpreter(io=1).run("⎕FMT 1 2 3")
        assert "".join(str(c) for c in result.data) == "1 2 3"

    def test_dyadic_fmt_integer(self) -> None:
        result = Interpreter(io=1).run("'I5' ⎕FMT 42")
        assert result.shape == [1, 5]

    def test_dyadic_fmt_fixed(self) -> None:
        result = Interpreter(io=1).run("'F8.2' ⎕FMT 3.14159")
        chars = "".join(str(c) for c in result.data)
        assert "3.14" in chars

    def test_dyadic_fmt_alpha(self) -> None:
        result = Interpreter(io=1).run("'5A1' ⎕FMT 'hello'")
        assert "".join(str(c) for c in result.data) == "hello"

    def test_fmt_semicolons(self) -> None:
        result = Interpreter(io=1).run("⎕FMT (1;2;3)")
        assert "".join(str(c) for c in result.data) == "1 2 3"

    def test_fmt_text_insertion(self) -> None:
        result = Interpreter(io=1).run("'I3,⊂ => ⊃,I3' ⎕FMT (1;2)")
        chars = "".join(str(c) for c in result.data)
        assert "=>" in chars

    def test_fmt_g_pattern(self) -> None:
        result = Interpreter(io=1).run("'G⊂99/99/9999⊃' ⎕FMT 3142025")
        chars = "".join(str(c) for c in result.data)
        assert chars.strip() == "03/14/2025"

    def test_fmt_error_bad_spec(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'Z5' ⎕FMT 42")


class TestFileIO:
    def test_nwrite_and_nread(self, tmp_path: object) -> None:
        import os
        path = os.path.join(str(tmp_path), "test.txt")
        i = Interpreter(io=1)
        i.run(f"'hello' ⎕NWRITE '{path}'")
        result = i.run(f"⎕NREAD '{path}'")
        assert "".join(str(c) for c in result.data) == "hello"

    def test_nexists(self, tmp_path: object) -> None:
        import os
        path = os.path.join(str(tmp_path), "exists.txt")
        with open(path, "w") as f:
            f.write("x")
        assert Interpreter(io=1).run(f"⎕NEXISTS '{path}'") == S(1)
        assert Interpreter(io=1).run(f"⎕NEXISTS '{path}.nope'") == S(0)

    def test_ndelete(self, tmp_path: object) -> None:
        import os
        path = os.path.join(str(tmp_path), "del.txt")
        with open(path, "w") as f:
            f.write("x")
        Interpreter(io=1).run(f"⎕NDELETE '{path}'")
        assert not os.path.exists(path)
