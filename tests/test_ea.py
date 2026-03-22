from marple.arraymodel import APLArray, S
from marple.interpreter import interpret


class TestDivisionByZero:
    def test_divide_by_zero_raises(self) -> None:
        from marple.errors import DomainError
        import pytest
        with pytest.raises(DomainError):
            interpret("1÷0")


class TestEA:
    def test_success_returns_result(self) -> None:
        env: dict[str, object] = {}
        interpret("#import $::error::ea as ea", env)
        result = interpret("'0' ea '2+3'", env)
        assert result == S(5)

    def test_failure_returns_alternate(self) -> None:
        env: dict[str, object] = {}
        interpret("#import $::error::ea as ea", env)
        result = interpret("'0' ea '1÷0'", env)
        assert result == S(0)

    def test_failure_with_expression_alternate(self) -> None:
        env: dict[str, object] = {}
        interpret("#import $::error::ea as ea", env)
        result = interpret("'42' ea '1÷0'", env)
        assert result == S(42)


class TestEN:
    def test_fresh_session(self) -> None:
        env: dict[str, object] = {}
        interpret("#import $::error::en as en", env)
        result = interpret("en 0", env)
        assert result == S(0)

    def test_after_error(self) -> None:
        env: dict[str, object] = {}
        interpret("#import $::error::ea as ea", env)
        interpret("#import $::error::en as en", env)
        interpret("'0' ea '1÷0'", env)
        result = interpret("en 0", env)
        assert result == S(3)  # DomainError code

    def test_not_reset_by_success(self) -> None:
        env: dict[str, object] = {}
        interpret("#import $::error::ea as ea", env)
        interpret("#import $::error::en as en", env)
        interpret("'0' ea '1÷0'", env)
        interpret("'0' ea '2+3'", env)  # success
        result = interpret("en 0", env)
        assert result == S(3)  # still the last error

    def test_index_error_code(self) -> None:
        env: dict[str, object] = {}
        interpret("#import $::error::ea as ea", env)
        interpret("#import $::error::en as en", env)
        interpret("'0' ea '10⌷⍳5'", env)
        result = interpret("en 0", env)
        assert result == S(6)  # IndexError_ code

    def test_length_error_code(self) -> None:
        env: dict[str, object] = {}
        interpret("#import $::error::ea as ea", env)
        interpret("#import $::error::en as en", env)
        interpret("'0' ea '1 2+1 2 3'", env)
        result = interpret("en 0", env)
        assert result == S(4)  # LengthError code

    def test_en_via_ea(self) -> None:
        env: dict[str, object] = {}
        interpret("#import $::error::ea as ea", env)
        interpret("#import $::error::en as en", env)
        # 'en 0' ea '1÷0' → evaluates en 0 which returns error code
        result = interpret("'en 0' ea '1÷0'", env)
        assert result == S(3)
