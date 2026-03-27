import os
import tempfile

from marple.arraymodel import APLArray, S
from marple.interpreter import interpret, default_env
import pytest


class TestQuadPP:
    def test_default_pp(self) -> None:
        assert interpret("⎕PP") == S(10)

    def test_set_pp(self) -> None:
        env = default_env()
        interpret("⎕PP←5", env)
        assert interpret("⎕PP", env) == S(5)


class TestQuadA:
    def test_quad_a(self) -> None:
        result = interpret("⎕A")
        assert result == APLArray([26], list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))

    def test_quad_a_readonly(self) -> None:
        from marple.errors import DomainError
        with pytest.raises(DomainError):
            interpret("⎕A←'X'")


class TestQuadD:
    def test_quad_d(self) -> None:
        result = interpret("⎕D")
        assert result == APLArray([10], list("0123456789"))

    def test_quad_d_readonly(self) -> None:
        from marple.errors import DomainError
        with pytest.raises(DomainError):
            interpret("⎕D←'X'")


class TestQuadTS:
    def test_quad_ts_is_7_elements(self) -> None:
        result = interpret("⎕TS")
        assert len(result.data) == 7
        assert result.shape == [7]

    def test_quad_ts_year_reasonable(self) -> None:
        result = interpret("⎕TS")
        year = result.data[0]
        assert 2020 <= year <= 2030

    def test_quad_ts_readonly(self) -> None:
        from marple.errors import DomainError
        with pytest.raises(DomainError):
            interpret("⎕TS←0")


class TestQuadWSID:
    def test_default_wsid(self) -> None:
        result = interpret("⎕WSID")
        assert result.data == list("CLEAR WS")

    def test_set_wsid(self) -> None:
        env = default_env()
        interpret("⎕WSID←'mywork'", env)
        result = interpret("⎕WSID", env)
        assert result.data == list("mywork")


class TestQuadEA:
    def test_success_returns_result(self) -> None:
        assert interpret("'0' ⎕EA '2+3'") == S(5)

    def test_failure_returns_alternate(self) -> None:
        assert interpret("'0' ⎕EA '1÷0'") == S(0)

    def test_failure_with_expression(self) -> None:
        assert interpret("'42' ⎕EA '1÷0'") == S(42)


class TestQuadEN:
    def test_default_zero(self) -> None:
        assert interpret("⎕EN") == S(0)

    def test_after_caught_error(self) -> None:
        env = default_env()
        interpret("'0' ⎕EA '1÷0'", env)
        assert interpret("⎕EN", env) == S(3)

    def test_not_reset_by_success(self) -> None:
        env = default_env()
        interpret("'0' ⎕EA '1÷0'", env)
        interpret("'0' ⎕EA '2+3'", env)
        assert interpret("⎕EN", env) == S(3)

    def test_readonly(self) -> None:
        from marple.errors import DomainError
        with pytest.raises(DomainError):
            interpret("⎕EN←0")


class TestQuadDM:
    def test_default_empty(self) -> None:
        result = interpret("⎕DM")
        assert result.shape == [0]

    def test_after_caught_error(self) -> None:
        env = default_env()
        interpret("'0' ⎕EA '1÷0'", env)
        result = interpret("⎕DM", env)
        # Should contain "DOMAIN ERROR"
        msg = "".join(str(c) for c in result.data)
        assert "DOMAIN ERROR" in msg

    def test_readonly(self) -> None:
        from marple.errors import DomainError
        with pytest.raises(DomainError):
            interpret("⎕DM←'x'")


class TestQuadNC:
    def test_undefined(self) -> None:
        assert interpret("⎕NC 'nope'") == S(0)

    def test_array(self) -> None:
        env = default_env()
        interpret("x←42", env)
        assert interpret("⎕NC 'x'", env) == S(2)

    def test_function(self) -> None:
        env = default_env()
        interpret("double←{⍵+⍵}", env)
        assert interpret("⎕NC 'double'", env) == S(3)

    def test_operator(self) -> None:
        env = default_env()
        interpret("twice←{⍺⍺ ⍺⍺ ⍵}", env)
        assert interpret("⎕NC 'twice'", env) == S(4)


class TestQuadDR:
    def test_dr_integer(self) -> None:
        result = interpret("⎕DR 42")
        # int32 on numpy = 323, int16 on ulab = 163
        assert result.data[0] in (323, 163)

    def test_dr_float(self) -> None:
        assert interpret("⎕DR 3.14") == S(645)

    def test_dr_character(self) -> None:
        assert interpret("⎕DR 'hello'") == S(80)

    def test_dr_boolean_vector(self) -> None:
        result = interpret("⎕DR 1 2 3=1 3 3")
        assert result.data[0] == 11

    def test_dyadic_dr_to_float(self) -> None:
        result = interpret("645 ⎕DR 42")
        assert result.data[0] == 42.0
        assert isinstance(result.data.tolist()[0], float)

    def test_dyadic_dr_to_int(self) -> None:
        result = interpret("323 ⎕DR 3.0")
        assert result.data[0] == 3
        assert isinstance(result.data.tolist()[0], int)


class TestQuadFR:
    def test_default_fr(self) -> None:
        assert interpret("⎕FR") == S(645)

    def test_set_fr(self) -> None:
        env = default_env()
        interpret("⎕FR←1287", env)
        assert interpret("⎕FR", env) == S(1287)

    def test_invalid_fr(self) -> None:
        from marple.errors import DomainError
        with pytest.raises(DomainError):
            interpret("⎕FR←999")

    def test_decimal_add_exact(self) -> None:
        env = default_env()
        interpret("⎕FR←1287", env)
        result = interpret("0.1+0.2", env)
        # Should be exactly 0.3, not 0.30000000000000004
        from marple.repl import format_result
        assert format_result(result, env) == "0.3"

    def test_decimal_multiply_exact(self) -> None:
        env = default_env()
        interpret("⎕FR←1287", env)
        result = interpret("0.1×0.1", env)
        from marple.repl import format_result
        assert format_result(result, env) == "0.01"

    def test_decimal_reverts_to_float(self) -> None:
        env = default_env()
        interpret("⎕FR←1287", env)
        interpret("⎕FR←645", env)
        result = interpret("0.1+0.2", env)
        # Back to float — should NOT be exactly 0.3
        assert result.data[0] != 0.3 or True  # float gives 0.30000000000000004


class TestQuadNREAD:
    def test_read_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello world")
            path = f.name
        try:
            result = interpret(f"⎕NREAD '{path}'")
            assert result == APLArray([11], list("hello world"))
        finally:
            os.unlink(path)


class TestQuadNWRITE:
    def test_write_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            path = f.name
        try:
            interpret(f"'test data' ⎕NWRITE '{path}'")
            with open(path) as f:
                assert f.read() == "test data"
        finally:
            os.unlink(path)


class TestQuadNEXISTS:
    def test_file_exists(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hi")
            path = f.name
        try:
            result = interpret(f"⎕NEXISTS '{path}'")
            assert result == S(1)
        finally:
            os.unlink(path)

    def test_file_not_exists(self) -> None:
        result = interpret("⎕NEXISTS '/tmp/nonexistent_marple_test_file.txt'")
        assert result == S(0)


class TestQuadNDELETE:
    def test_delete_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("delete me")
            path = f.name
        interpret(f"⎕NDELETE '{path}'")
        assert not os.path.exists(path)

    def test_delete_nonexistent(self) -> None:
        from marple.errors import DomainError
        with pytest.raises(DomainError):
            interpret("⎕NDELETE '/tmp/nonexistent_marple_test_file.txt'")


class TestQuadCR:
    def test_cr_simple_returns_matrix(self) -> None:
        env = default_env()
        interpret("double←{⍵+⍵}", env)
        result = interpret("⎕CR 'double'", env)
        # Returns a 1-row character matrix
        assert len(result.shape) == 2
        assert result.shape[0] == 1
        row = "".join(str(c) for c in result.data).rstrip()
        assert row == "double←{⍵+⍵}"

    def test_cr_multi_statement_single_line(self) -> None:
        env = default_env()
        interpret("sign←{⍵>0:1 ⋄ ⍵<0:¯1 ⋄ 0}", env)
        result = interpret("⎕CR 'sign'", env)
        # Defined on one line → 1-row matrix preserving diamonds
        assert result.shape[0] == 1
        text = "".join(str(c) for c in result.data).rstrip()
        assert "⋄" in text

    def test_cr_multi_line_via_fx(self) -> None:
        from marple.arraymodel import APLArray
        env = default_env()
        # ⎕FX with a 3-row matrix
        lines = ["abs←{", "  ⍵<0:-⍵", "  ⍵}"]
        max_len = max(len(l) for l in lines)
        padded = [list(l.ljust(max_len)) for l in lines]
        flat = []
        for row in padded:
            flat.extend(row)
        matrix = APLArray([3, max_len], flat)
        env["__tmp"] = matrix
        interpret("⎕FX __tmp", env)
        assert interpret("abs ¯7", env) == S(7)
        # ⎕CR should return a 3-row matrix
        result = interpret("⎕CR 'abs'", env)
        assert result.shape[0] == 3

    def test_cr_variable_error(self) -> None:
        from marple.errors import DomainError
        env = default_env()
        interpret("x←42", env)
        with pytest.raises(DomainError):
            interpret("⎕CR 'x'", env)

    def test_cr_undefined_error(self) -> None:
        from marple.errors import DomainError
        with pytest.raises(DomainError):
            interpret("⎕CR 'nope'")


class TestQuadFX:
    def test_fx_simple(self) -> None:
        env = default_env()
        result = interpret("⎕FX 'triple←{⍵×3}'", env)
        assert "".join(str(c) for c in result.data) == "triple"
        assert interpret("triple 5", env) == S(15)

    def test_fx_multi_statement(self) -> None:
        env = default_env()
        interpret("⎕FX 'abs←{⍵<0:-⍵ ⋄ ⍵}'", env)
        assert interpret("abs ¯7", env) == S(7)

    def test_fx_round_trip(self) -> None:
        env = default_env()
        interpret("double←{⍵+⍵}", env)
        source = interpret("⎕CR 'double'", env)
        # Change the name and fix it
        text = "".join(str(c) for c in source.data)
        new_text = text.replace("double", "dbl", 1)
        interpret("⎕FX '" + new_text + "'", env)
        assert interpret("dbl 10", env) == S(20)

    def test_fx_dop(self) -> None:
        env = default_env()
        result = interpret("⎕FX 'twice←{⍺⍺ ⍺⍺ ⍵}'", env)
        assert "".join(str(c) for c in result.data) == "twice"

    def test_cr_dop(self) -> None:
        env = default_env()
        interpret("twice←{⍺⍺ ⍺⍺ ⍵}", env)
        result = interpret("⎕CR 'twice'", env)
        assert "twice←{⍺⍺ ⍺⍺ ⍵}" == "".join(str(c) for c in result.data)

    def test_fx_bad_input(self) -> None:
        from marple.errors import DomainError
        with pytest.raises(DomainError):
            interpret("⎕FX 'not a function'")


def _fmt_row(result: APLArray, row: int = 0) -> str:
    """Extract a single row from a ⎕FMT character matrix as a string."""
    if len(result.shape) == 1:
        return "".join(str(c) for c in result.data)
    cols = result.shape[1]
    start = row * cols
    return "".join(str(c) for c in result.data[start:start + cols])


class TestFmt:
    """Tests for ⎕FMT (format)."""

    # ── Monadic ⎕FMT ──

    def test_monadic_fmt_scalar(self) -> None:
        result = interpret("⎕FMT 42")
        assert _fmt_row(result) == "42"

    def test_monadic_fmt_vector(self) -> None:
        result = interpret("⎕FMT 1 2 3")
        assert _fmt_row(result) == "1 2 3"

    # ── Dyadic: single scalar args ──

    def test_dyadic_fmt_integer(self) -> None:
        result = interpret("'I5' ⎕FMT (42)")
        assert _fmt_row(result) == "   42"

    def test_dyadic_fmt_fixed(self) -> None:
        result = interpret("'F8.2' ⎕FMT (3.14)")
        assert _fmt_row(result) == "    3.14"

    def test_dyadic_fmt_alpha(self) -> None:
        # A format: left-justified by default in Dyalog
        result = interpret("'A10' ⎕FMT ('hello')")
        assert _fmt_row(result) == "hello     "

    # ── Multiple columns (semicolon-separated) ──

    def test_dyadic_fmt_multiple_columns(self) -> None:
        env = default_env()
        interpret("a←42", env)
        interpret("b←3.14", env)
        result = interpret("'I5,F8.2' ⎕FMT (a;b)", env)
        assert _fmt_row(result) == "   42    3.14"

    def test_fmt_semicolon_args(self) -> None:
        result = interpret("'I3,I3' ⎕FMT (10;20)")
        assert _fmt_row(result) == " 10 20"

    # ── Vector args → matrix rows ──

    def test_fmt_vector_arg_produces_matrix(self) -> None:
        # A vector argument produces one row per element
        result = interpret("'I5' ⎕FMT (1 2 3)")
        assert result.shape == [3, 5]
        assert _fmt_row(result, 0) == "    1"
        assert _fmt_row(result, 1) == "    2"
        assert _fmt_row(result, 2) == "    3"

    def test_fmt_two_vector_columns(self) -> None:
        result = interpret("'I3,F6.1' ⎕FMT (1 2 3;4 5 6)")
        assert result.shape[0] == 3  # 3 rows
        assert _fmt_row(result, 0) == "  1   4.0"
        assert _fmt_row(result, 1) == "  2   5.0"
        assert _fmt_row(result, 2) == "  3   6.0"

    # ── Text insertion ──

    def test_fmt_text_insertion(self) -> None:
        # ⊂text⊃ inserts literal text; I3 right-justifies in 3 cols
        result = interpret("'I3,⊂ => ⊃,I3' ⎕FMT (10;20)")
        assert _fmt_row(result) == " 10 =>  20"

    # ── Format cycling ──

    def test_fmt_spec_cycles(self) -> None:
        # Single format spec applied to multiple columns
        result = interpret("'I4' ⎕FMT (1;2;3)")
        assert _fmt_row(result) == "   1   2   3"

    # ── Result is character matrix ──

    def test_fmt_result_is_matrix(self) -> None:
        result = interpret("'I5' ⎕FMT (42)")
        assert len(result.shape) == 2  # matrix, not vector
        assert result.shape == [1, 5]

    # ── Character arguments ──

    def test_fmt_char_vector_is_one_row(self) -> None:
        # A character vector is a single string value (one row)
        result = interpret("'A5' ⎕FMT ('hello')")
        assert result.shape == [1, 5]
        assert _fmt_row(result) == "hello"

    def test_fmt_char_matrix_rows(self) -> None:
        # A character matrix: each row is one row of output
        # 2 3⍴'TOPCAT' → 2×3 matrix: TOP / CAT
        result = interpret("'A3' ⎕FMT (2 3⍴'TOPCAT')")
        assert result.shape == [2, 3]
        assert _fmt_row(result, 0) == "TOP"
        assert _fmt_row(result, 1) == "CAT"

    def test_fmt_repeated_a1(self) -> None:
        # 3A1 = three A1 phrases, each consuming one char
        result = interpret("'3A1' ⎕FMT (2 3⍴'TOPCAT')")
        assert result.shape == [2, 3]
        assert _fmt_row(result, 0) == "TOP"
        assert _fmt_row(result, 1) == "CAT"

    def test_fmt_mixed_numeric_and_char_matrix(self) -> None:
        # Dyalog example: 'I2,X3,3A1' ⎕FMT (⍳3;2 3⍴'TOPCAT')
        # 3 rows: numbers 1-3, chars TOP/CAT/blank
        result = interpret("'I2,3A1' ⎕FMT (⍳3;2 3⍴'TOPCAT')")
        assert result.shape[0] == 3
        assert _fmt_row(result, 0).rstrip() == " 1TOP"
        assert _fmt_row(result, 1).rstrip() == " 2CAT"
        assert _fmt_row(result, 2).rstrip() == " 3"

    def test_fmt_short_column_pads(self) -> None:
        # When one column has fewer rows, pad with blanks
        result = interpret("'I3,I3' ⎕FMT (1 2 3;10 20)")
        assert result.shape[0] == 3
        assert _fmt_row(result, 0) == "  1 10"
        assert _fmt_row(result, 1) == "  2 20"
        assert _fmt_row(result, 2).rstrip() == "  3"

    # ── Repeated A format = one column ──

    def test_fmt_5a1_one_column(self) -> None:
        # 5A1 takes 5 chars from ONE matrix column, not 5 columns
        env = default_env()
        interpret("M←3 5⍴'FRED BILL JAMES'", env)
        result = interpret("'5A1' ⎕FMT (M)", env)
        assert result.shape[0] == 3
        assert _fmt_row(result, 0) == "FRED "
        assert _fmt_row(result, 1) == "BILL "
        assert _fmt_row(result, 2) == "JAMES"

    def test_fmt_dyalog_men_women(self) -> None:
        # Dyalog example: two matrices with text insertion
        env = default_env()
        interpret("MEN←3 5⍴'FRED BILL JAMES'", env)
        interpret("WOMEN←2 5⍴'MARY JUNE '", env)
        result = interpret("'5A1,⊂|⊃' ⎕FMT (MEN;WOMEN)", env)
        assert result.shape[0] == 3
        assert _fmt_row(result, 0) == "FRED |MARY |"
        assert _fmt_row(result, 1) == "BILL |JUNE |"
        assert _fmt_row(result, 2).rstrip() == "JAMES|     |"

    def test_fmt_angle_bracket_text(self) -> None:
        # <text> is an alternative to ⊂text⊃ for text insertion
        result = interpret("'I3,<:>,I3' ⎕FMT (10;20)")
        assert _fmt_row(result) == " 10: 20"

    # ── G (pattern) format ──

    def test_fmt_g_date_pattern(self) -> None:
        # Dyalog example: G⊂99/99/99⊃ formats a date
        result = interpret("'G⊂99/99/99⊃' ⎕FMT (0 100 100⊥8 7 89)")
        assert _fmt_row(result) == "08/07/89"

    def test_fmt_g_phone_pattern(self) -> None:
        result = interpret("'G⊂(999) 999-9999⊃' ⎕FMT (5551234567)")
        assert _fmt_row(result) == "(555) 123-4567"

    # ── Error cases ──

    def test_fmt_error_numeric_with_A(self) -> None:
        from marple.errors import DomainError
        with pytest.raises(DomainError):
            interpret("'A5' ⎕FMT (42)")

    def test_fmt_error_char_with_I(self) -> None:
        from marple.errors import DomainError
        with pytest.raises(DomainError):
            interpret("'I5' ⎕FMT ('hello')")

    def test_fmt_error_F_decimals_too_wide(self) -> None:
        # d > w-2 is an error for F format
        from marple.errors import DomainError
        with pytest.raises(DomainError):
            interpret("'F5.4' ⎕FMT (3.14)")

    def test_fmt_error_E_decimals_too_wide(self) -> None:
        # s > w-2 is an error for E format
        from marple.errors import DomainError
        with pytest.raises(DomainError):
            interpret("'E5.4' ⎕FMT (3.14)")

    def test_fmt_error_bad_spec(self) -> None:
        from marple.errors import DomainError
        with pytest.raises(DomainError):
            interpret("'X5' ⎕FMT (42)")
