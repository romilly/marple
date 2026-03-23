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
