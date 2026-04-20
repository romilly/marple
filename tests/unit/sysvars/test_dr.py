"""⎕DR tests via the Interpreter — monadic, dyadic, and comparison-returns-boolean checks."""

import numpy

from marple.ports.array import S
from marple.engine import Interpreter


class TestMonadicDRViaInterpreter:
    def test_dr_integer(self) -> None:
        result = Interpreter(io=1).run("⎕DR 42")
        assert result in (S(323), S(643))

    def test_dr_float(self) -> None:
        assert Interpreter(io=1).run("⎕DR 3.14") == S(645)

    def test_dr_char(self) -> None:
        assert Interpreter(io=1).run("⎕DR 'hello'") == S(320)

    def test_dr_boolean_vector(self) -> None:
        assert Interpreter(io=1).run("⎕DR 1 2 3=1 3 3") == S(81)


class TestScalarComparisonReturnsBoolean:
    def test_equal(self) -> None:
        assert Interpreter(io=1).run("⎕DR 1=1") == S(81)

    def test_less_than(self) -> None:
        assert Interpreter(io=1).run("⎕DR 1<2") == S(81)

    def test_less_equal(self) -> None:
        assert Interpreter(io=1).run("⎕DR 1≤2") == S(81)

    def test_greater_equal(self) -> None:
        assert Interpreter(io=1).run("⎕DR 2≥1") == S(81)

    def test_greater_than(self) -> None:
        assert Interpreter(io=1).run("⎕DR 2>1") == S(81)

    def test_not_equal(self) -> None:
        assert Interpreter(io=1).run("⎕DR 1≠2") == S(81)


class TestVectorComparisonReturnsBoolean:
    def test_equal(self) -> None:
        assert Interpreter(io=1).run("⎕DR 1 2 3=1 3 3") == S(81)

    def test_less_than(self) -> None:
        assert Interpreter(io=1).run("⎕DR 1 2 3<2 2 2") == S(81)

    def test_less_equal(self) -> None:
        assert Interpreter(io=1).run("⎕DR 1 2 3≤2 2 2") == S(81)

    def test_greater_equal(self) -> None:
        assert Interpreter(io=1).run("⎕DR 1 2 3≥2 2 2") == S(81)

    def test_greater_than(self) -> None:
        assert Interpreter(io=1).run("⎕DR 1 2 3>2 2 2") == S(81)

    def test_not_equal(self) -> None:
        assert Interpreter(io=1).run("⎕DR 1 2 3≠1 3 3") == S(81)


class TestDyadicDRViaInterpreter:
    def test_dr_to_char(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("320 ⎕DR 65 66 67")
        assert chars_to_str(result.data) == "ABC"

    def test_dr_to_float(self) -> None:
        result = Interpreter(io=1).run("645 ⎕DR 42")
        assert result == S(42)

    def test_dr_to_int(self) -> None:
        result = Interpreter(io=1).run("323 ⎕DR 3.0")
        assert result == S(3)
        assert numpy.issubdtype(result.data.dtype, numpy.integer)

    def test_dr_to_boolean(self) -> None:
        result = Interpreter(io=1).run("81 ⎕DR 1 0 1")
        assert Interpreter(io=1).run("⎕DR 81 ⎕DR 1 0 1") == S(81)
