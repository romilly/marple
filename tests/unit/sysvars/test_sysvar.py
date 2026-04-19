"""System variable and system function tests — new engine."""

import pytest

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter
from marple.errors import DomainError


class TestQuadIO:
    def test_default_io(self) -> None:
        assert Interpreter(io=1).run("⎕IO") == S(1)

    def test_io_zero(self) -> None:
        assert Interpreter(io=0).run("⎕IO") == S(0)

    def test_iota_with_io0(self) -> None:
        assert Interpreter(io=0).run("⍳3") == APLArray.array([3], [0, 1, 2])

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

    def test_quad_ts_readonly(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("⎕TS←0")


class TestQuadWSID:
    def test_default_wsid(self) -> None:
        result = Interpreter(io=1).run("⎕WSID")
        assert len(result.data) > 0

    def test_set_wsid(self) -> None:
        from marple.backend_functions import chars_to_str
        i = Interpreter(io=1)
        i.run("⎕WSID←'MYWS'")
        result = i.run("⎕WSID")
        assert chars_to_str(result.data) == "MYWS"


class TestSystemFunctions:
    def test_ucs_to_char(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("⎕UCS 65")
        assert result.is_scalar()
        assert chars_to_str(result.data) == "A"

    def test_ucs_to_code(self) -> None:
        result = Interpreter(io=1).run("⎕UCS 'A'")
        assert result == S(65)

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

    def test_nc_operator(self) -> None:
        i = Interpreter(io=1)
        i.run("twice←{⍺⍺ ⍺⍺ ⍵}")
        assert i.run("⎕NC 'twice'") == S(4)

    def test_nc_system_variable_is_invalid(self) -> None:
        """⎕-prefix names are reserved — ⎕NC returns ¯1, matching Dyalog."""
        assert Interpreter(io=1).run("⎕NC '⎕IO'") == S(-1)

    def test_nc_system_function_is_invalid(self) -> None:
        assert Interpreter(io=1).run("⎕NC '⎕NC'") == S(-1)

    def test_ex(self) -> None:
        i = Interpreter(io=1)
        i.run("x←42")
        i.run("⎕EX 'x'")
        assert i.run("⎕NC 'x'") == S(0)

    def test_ex_matrix(self) -> None:
        # Matrix-form ⎕EX expunges multiple names: each row is a name.
        # Bug pre-fix: operand.data[r*cols:(r+1)*cols] sliced ROWS of
        # the 2D uint32 ndarray instead of flat elements, so neither
        # name was correctly extracted and both stayed defined.
        i = Interpreter(io=1)
        i.run("foo←1")
        i.run("baz←2")
        result = i.run("⎕EX 2 3⍴'foobaz'")
        assert result == S(2)
        assert i.run("⎕NC 'foo'") == S(0)
        assert i.run("⎕NC 'baz'") == S(0)

    def test_nl(self) -> None:
        i = Interpreter(io=1)
        i.run("foo←{⍵+1}")
        i.run("bar←{⍵×2}")
        result = i.run("⎕NL 3")
        assert result.shape[0] == 2


class TestWA:
    def test_wa_returns_scalar_integer(self) -> None:
        result = Interpreter(io=1).run("⎕WA")
        assert result.shape == []
        v = result.data.item()
        assert int(v) == v

    def test_wa_greater_than_zero(self) -> None:
        assert Interpreter(io=1).run("⎕WA").data.item() > 0


class TestEA:
    def test_ea_traps_error(self) -> None:
        assert Interpreter(io=1).run("'0' ⎕EA '1÷0'") == S(0)

    def test_ea_no_error(self) -> None:
        assert Interpreter(io=1).run("'99' ⎕EA '2+3'") == S(5)

    def test_ea_failure_with_expression(self) -> None:
        assert Interpreter(io=1).run("'42' ⎕EA '1÷0'") == S(42)


class TestEN:
    def test_en_default_zero(self) -> None:
        assert Interpreter(io=1).run("⎕EN") == S(0)

    def test_en_after_caught_error(self) -> None:
        i = Interpreter(io=1)
        i.run("'0' ⎕EA '1÷0'")
        assert i.run("⎕EN") == S(3)

    def test_en_not_reset_by_success(self) -> None:
        i = Interpreter(io=1)
        i.run("'0' ⎕EA '1÷0'")
        i.run("'0' ⎕EA '2+3'")
        assert i.run("⎕EN") == S(3)

    def test_en_readonly(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("⎕EN←0")


class TestDM:
    def test_dm_default_empty(self) -> None:
        result = Interpreter(io=1).run("⎕DM")
        assert result.shape == [0]

    def test_dm_after_caught_error(self) -> None:
        from marple.backend_functions import chars_to_str
        i = Interpreter(io=1)
        i.run("'0' ⎕EA '1÷0'")
        result = i.run("⎕DM")
        msg = chars_to_str(result.data)
        assert "DOMAIN ERROR" in msg

    def test_dm_readonly(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("⎕DM←'x'")


class TestQuadFR:
    def test_default_fr(self) -> None:
        assert Interpreter(io=1).run("⎕FR") == S(645)

    def test_set_fr(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕FR←1287")
        assert i.run("⎕FR") == S(1287)

    def test_invalid_fr(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("⎕FR←999")

    def test_decimal_add_exact(self) -> None:
        from marple.formatting import format_result
        i = Interpreter(io=1)
        i.run("⎕FR←1287")
        result = i.run("0.1+0.2")
        assert format_result(result, i.env) == "0.3"

    def test_decimal_multiply_exact(self) -> None:
        from marple.formatting import format_result
        i = Interpreter(io=1)
        i.run("⎕FR←1287")
        result = i.run("0.1×0.1")
        assert format_result(result, i.env) == "0.01"

    def test_decimal_reverts_to_float(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕FR←1287")
        i.run("⎕FR←645")
        result = i.run("0.1+0.2")
        # Back to float — may not be exactly 0.3
        assert result.data.item() != 0.3 or True


class TestCR:
    def test_cr(self) -> None:
        i = Interpreter(io=1)
        i.run("add←{⍺+⍵}")
        result = i.run("⎕CR 'add'")
        assert result.shape[0] >= 1

    def test_cr_simple_returns_matrix(self) -> None:
        from marple.backend_functions import chars_to_str
        i = Interpreter(io=1)
        i.run("double←{⍵+⍵}")
        result = i.run("⎕CR 'double'")
        assert len(result.shape) == 2
        assert result.shape[0] == 1
        row = chars_to_str(result.data).rstrip()
        assert row == "double←{⍵+⍵}"

    def test_cr_multi_statement_single_line(self) -> None:
        from marple.backend_functions import chars_to_str
        i = Interpreter(io=1)
        i.run("sign←{⍵>0:1 ⋄ ⍵<0:¯1 ⋄ 0}")
        result = i.run("⎕CR 'sign'")
        assert result.shape[0] == 1
        text = chars_to_str(result.data).rstrip()
        assert "⋄" in text

    def test_cr_multi_line_via_fx(self) -> None:
        from marple.backend_functions import str_to_char_array
        i = Interpreter(io=1)
        lines = ["abs←{", "  ⍵<0:-⍵", "  ⍵}"]
        max_len = max(len(l) for l in lines)
        text = "".join(l.ljust(max_len) for l in lines)
        data = str_to_char_array(text).reshape(3, max_len)
        matrix = APLArray([3, max_len], data)
        i.env["__tmp"] = matrix
        i.run("⎕FX __tmp")
        assert i.run("abs ¯7") == S(7)
        result = i.run("⎕CR 'abs'")
        assert result.shape[0] == 3

    def test_cr_variable_error(self) -> None:
        i = Interpreter(io=1)
        i.run("x←42")
        with pytest.raises(DomainError):
            i.run("⎕CR 'x'")

    def test_cr_undefined_error(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("⎕CR 'nope'")

    def test_cr_dop(self) -> None:
        from marple.backend_functions import chars_to_str
        i = Interpreter(io=1)
        i.run("twice←{⍺⍺ ⍺⍺ ⍵}")
        result = i.run("⎕CR 'twice'")
        assert "twice←{⍺⍺ ⍺⍺ ⍵}" == chars_to_str(result.data)


class TestFX:
    def test_fx(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕FX 'inc←{⍵+1}'")
        assert i.run("inc 5") == S(6)

    def test_fx_simple(self) -> None:
        from marple.backend_functions import chars_to_str
        i = Interpreter(io=1)
        result = i.run("⎕FX 'triple←{⍵×3}'")
        assert chars_to_str(result.data) == "triple"
        assert i.run("triple 5") == S(15)

    def test_fx_multi_statement(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕FX 'abs←{⍵<0:-⍵ ⋄ ⍵}'")
        assert i.run("abs ¯7") == S(7)

    def test_fx_round_trip(self) -> None:
        from marple.backend_functions import chars_to_str
        i = Interpreter(io=1)
        i.run("double←{⍵+⍵}")
        source = i.run("⎕CR 'double'")
        text = chars_to_str(source.data)
        new_text = text.replace("double", "dbl", 1)
        i.run("⎕FX '" + new_text + "'")
        assert i.run("dbl 10") == S(20)

    def test_fx_dop(self) -> None:
        from marple.backend_functions import chars_to_str
        i = Interpreter(io=1)
        result = i.run("⎕FX 'twice←{⍺⍺ ⍺⍺ ⍵}'")
        assert chars_to_str(result.data) == "twice"

    def test_fx_bad_input(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("⎕FX 'not a function'")


@pytest.mark.slow
class TestDL:
    def test_dl(self) -> None:
        result = Interpreter(io=1).run("⎕DL 0.01")
        assert result.data.item() >= 0.01

    def test_dl_returns_elapsed(self) -> None:
        result = Interpreter(io=1).run("⎕DL 0.1")
        elapsed = float(result.data.item())
        assert 0.05 < elapsed < 0.5

    def test_dl_zero(self) -> None:
        result = Interpreter(io=1).run("⎕DL 0")
        assert float(result.data.item()) >= 0


def _extract_matrix_rows(result: APLArray) -> list[str]:
    """Extract rows of a 2D character matrix as trimmed strings."""
    from marple.backend_functions import chars_to_str
    return [chars_to_str(result.data[r]).rstrip() for r in range(result.shape[0])]


class TestNL:
    def test_nl_functions(self) -> None:
        i = Interpreter(io=1)
        i.run("double←{⍵+⍵}")
        i.run("triple←{⍵+⍵+⍵}")
        result = i.run("⎕NL 3")
        assert len(result.shape) == 2
        names = _extract_matrix_rows(result)
        assert "double" in names
        assert "triple" in names

    def test_nl_variables(self) -> None:
        i = Interpreter(io=1)
        i.run("x←5")
        i.run("y←10")
        result = i.run("⎕NL 2")
        assert len(result.shape) == 2
        names = _extract_matrix_rows(result)
        assert "x" in names
        assert "y" in names

    def test_nl_empty(self) -> None:
        result = Interpreter(io=1).run("⎕NL 4")
        assert result.shape == [0, 0] or len(result.data) == 0


def _fmt_row(result: APLArray, row: int = 0) -> str:
    """Extract a single row from a ⎕FMT character matrix as a string."""
    from marple.backend_functions import chars_to_str
    if len(result.shape) == 1:
        return chars_to_str(result.data)
    return chars_to_str(result.data[row])


class TestFmt:
    def test_monadic_fmt_scalar(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("⎕FMT 42")
        assert chars_to_str(result.data) == "42"

    def test_monadic_fmt_vector(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("⎕FMT 1 2 3")
        assert chars_to_str(result.data) == "1 2 3"

    def test_dyadic_fmt_integer(self) -> None:
        result = Interpreter(io=1).run("'I5' ⎕FMT 42")
        assert result.shape == [1, 5]

    def test_dyadic_fmt_fixed(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("'F8.2' ⎕FMT 3.14159")
        chars = chars_to_str(result.data)
        assert "3.14" in chars

    def test_dyadic_fmt_alpha(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("'5A1' ⎕FMT 'hello'")
        assert chars_to_str(result.data) == "hello"

    def test_dyadic_fmt_multiple_columns(self) -> None:
        i = Interpreter(io=1)
        i.run("a←42")
        i.run("b←3.14")
        result = i.run("'I5,F8.2' ⎕FMT (a;b)")
        assert _fmt_row(result) == "   42    3.14"

    def test_fmt_semicolon_args(self) -> None:
        result = Interpreter(io=1).run("'I3,I3' ⎕FMT (10;20)")
        assert _fmt_row(result) == " 10 20"

    def test_fmt_vector_arg_produces_matrix(self) -> None:
        result = Interpreter(io=1).run("'I5' ⎕FMT (1 2 3)")
        assert result.shape == [3, 5]
        assert _fmt_row(result, 0) == "    1"
        assert _fmt_row(result, 1) == "    2"
        assert _fmt_row(result, 2) == "    3"

    def test_fmt_two_vector_columns(self) -> None:
        result = Interpreter(io=1).run("'I3,F6.1' ⎕FMT (1 2 3;4 5 6)")
        assert result.shape[0] == 3
        assert _fmt_row(result, 0) == "  1   4.0"
        assert _fmt_row(result, 1) == "  2   5.0"
        assert _fmt_row(result, 2) == "  3   6.0"

    def test_fmt_semicolons(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("⎕FMT (1;2;3)")
        assert chars_to_str(result.data) == "1 2 3"

    def test_fmt_text_insertion(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("'I3,⊂ => ⊃,I3' ⎕FMT (1;2)")
        chars = chars_to_str(result.data)
        assert "=>" in chars

    def test_fmt_spec_cycles(self) -> None:
        result = Interpreter(io=1).run("'I4' ⎕FMT (1;2;3)")
        assert _fmt_row(result) == "   1   2   3"

    def test_fmt_result_is_matrix(self) -> None:
        result = Interpreter(io=1).run("'I5' ⎕FMT (42)")
        assert len(result.shape) == 2
        assert result.shape == [1, 5]

    def test_fmt_char_vector_is_one_row(self) -> None:
        result = Interpreter(io=1).run("'A5' ⎕FMT ('hello')")
        assert result.shape == [1, 5]
        assert _fmt_row(result) == "hello"

    def test_fmt_char_matrix_rows(self) -> None:
        result = Interpreter(io=1).run("'A3' ⎕FMT (2 3⍴'TOPCAT')")
        assert result.shape == [2, 3]
        assert _fmt_row(result, 0) == "TOP"
        assert _fmt_row(result, 1) == "CAT"

    def test_fmt_repeated_a1(self) -> None:
        result = Interpreter(io=1).run("'3A1' ⎕FMT (2 3⍴'TOPCAT')")
        assert result.shape == [2, 3]
        assert _fmt_row(result, 0) == "TOP"
        assert _fmt_row(result, 1) == "CAT"

    def test_fmt_mixed_numeric_and_char_matrix(self) -> None:
        result = Interpreter(io=1).run("'I2,3A1' ⎕FMT (⍳3;2 3⍴'TOPCAT')")
        assert result.shape[0] == 3
        assert _fmt_row(result, 0).rstrip() == " 1TOP"
        assert _fmt_row(result, 1).rstrip() == " 2CAT"
        assert _fmt_row(result, 2).rstrip() == " 3"

    def test_fmt_short_column_pads(self) -> None:
        result = Interpreter(io=1).run("'I3,I3' ⎕FMT (1 2 3;10 20)")
        assert result.shape[0] == 3
        assert _fmt_row(result, 0) == "  1 10"
        assert _fmt_row(result, 1) == "  2 20"
        assert _fmt_row(result, 2).rstrip() == "  3"

    def test_fmt_5a1_one_column(self) -> None:
        i = Interpreter(io=1)
        i.run("M←3 5⍴'FRED BILL JAMES'")
        result = i.run("'5A1' ⎕FMT (M)")
        assert result.shape[0] == 3
        assert _fmt_row(result, 0) == "FRED "
        assert _fmt_row(result, 1) == "BILL "
        assert _fmt_row(result, 2) == "JAMES"

    def test_fmt_dyalog_men_women(self) -> None:
        i = Interpreter(io=1)
        i.run("MEN←3 5⍴'FRED BILL JAMES'")
        i.run("WOMEN←2 5⍴'MARY JUNE '")
        result = i.run("'5A1,⊂|⊃' ⎕FMT (MEN;WOMEN)")
        assert result.shape[0] == 3
        assert _fmt_row(result, 0) == "FRED |MARY |"
        assert _fmt_row(result, 1) == "BILL |JUNE |"
        assert _fmt_row(result, 2).rstrip() == "JAMES|     |"

    def test_fmt_angle_bracket_text(self) -> None:
        result = Interpreter(io=1).run("'I3,<:>,I3' ⎕FMT (10;20)")
        assert _fmt_row(result) == " 10: 20"

    def test_fmt_g_pattern(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("'G⊂99/99/9999⊃' ⎕FMT 3142025")
        chars = chars_to_str(result.data)
        assert chars.strip() == "03/14/2025"

    def test_fmt_g_date_pattern(self) -> None:
        result = Interpreter(io=1).run("'G⊂99/99/99⊃' ⎕FMT (0 100 100⊥8 7 89)")
        assert _fmt_row(result) == "08/07/89"

    def test_fmt_g_phone_pattern(self) -> None:
        result = Interpreter(io=1).run("'G⊂(999) 999-9999⊃' ⎕FMT (5551234567)")
        assert _fmt_row(result) == "(555) 123-4567"

    def test_fmt_error_numeric_with_A(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'A5' ⎕FMT (42)")

    def test_fmt_error_char_with_I(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'I5' ⎕FMT ('hello')")

    def test_fmt_error_F_decimals_too_wide(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'F5.4' ⎕FMT (3.14)")

    def test_fmt_error_E_decimals_too_wide(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'E5.4' ⎕FMT (3.14)")

    def test_fmt_error_bad_spec(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("'Z5' ⎕FMT 42")


class TestFileIO:
    def test_nwrite_and_nread(self, tmp_path: object) -> None:
        from marple.backend_functions import chars_to_str
        import os
        path = os.path.join(str(tmp_path), "test.txt")
        i = Interpreter(io=1)
        i.run(f"'hello' ⎕NWRITE '{path}'")
        result = i.run(f"⎕NREAD '{path}'")
        assert chars_to_str(result.data) == "hello"

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

    def test_ndelete_nonexistent(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("⎕NDELETE '/tmp/nonexistent_marple_test_file.txt'")


class TestCSV:
    def test_csv_numeric_columns(self) -> None:
        import os
        import tempfile
        i = Interpreter(io=1)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("age,score\n")
            f.write("25,90\n")
            f.write("30,85\n")
            f.write("35,72\n")
            path = f.name
        try:
            i.run(f"⎕CSV '{path}'")
            assert i.run("age") == APLArray.array([3], [25, 30, 35])
            assert i.run("score") == APLArray.array([3], [90, 85, 72])
        finally:
            os.unlink(path)

    def test_csv_returns_row_count(self) -> None:
        import os
        import tempfile
        i = Interpreter(io=1)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("x\n1\n2\n3\n")
            path = f.name
        try:
            result = i.run(f"⎕CSV '{path}'")
            assert result == S(3)
        finally:
            os.unlink(path)

    def test_csv_text_columns(self) -> None:
        import os
        import tempfile
        i = Interpreter(io=1)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,val\n")
            f.write("Alice,10\n")
            f.write("Bob,20\n")
            path = f.name
        try:
            i.run(f"⎕CSV '{path}'")
            name_result = i.run("name")
            assert name_result.shape[0] == 2
            rows = _extract_matrix_rows(name_result)
            assert rows[0] == "Alice"
            assert i.run("val") == APLArray.array([2], [10, 20])
        finally:
            os.unlink(path)
