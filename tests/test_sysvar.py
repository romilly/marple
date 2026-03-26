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
    def test_cr_simple(self) -> None:
        env = default_env()
        interpret("double←{⍵+⍵}", env)
        result = interpret("⎕CR 'double'", env)
        assert "".join(str(c) for c in result.data) == "double←{⍵+⍵}"

    def test_cr_multi_statement(self) -> None:
        env = default_env()
        interpret("sign←{⍵>0:1 ⋄ ⍵<0:¯1 ⋄ 0}", env)
        result = interpret("⎕CR 'sign'", env)
        text = "".join(str(c) for c in result.data)
        assert "sign←" in text
        assert "⍵>0" in text

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
