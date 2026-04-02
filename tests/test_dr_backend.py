"""Tests for ⎕DR type detection and conversion — numpy backend."""

import numpy

from marple.arraymodel import S
from marple.backend import data_type_code
from marple.engine import Interpreter


class TestDataTypeCode:
    def test_boolean(self) -> None:
        data = numpy.array([1, 0, 1], dtype=numpy.uint8)
        assert data_type_code(data) == 81

    def test_int8(self) -> None:
        data = numpy.array([1, 2, 3], dtype=numpy.int8)
        assert data_type_code(data) == 83

    def test_int16(self) -> None:
        data = numpy.array([1, 2, 3], dtype=numpy.int16)
        assert data_type_code(data) == 163

    def test_int32(self) -> None:
        data = numpy.array([1, 2, 3], dtype=numpy.int32)
        assert data_type_code(data) == 323

    def test_int64(self) -> None:
        data = numpy.array([1, 2, 3], dtype=numpy.int64)
        assert data_type_code(data) == 643

    def test_float64(self) -> None:
        data = numpy.array([1.5, 2.5], dtype=numpy.float64)
        assert data_type_code(data) == 645

    def test_character(self) -> None:
        data = ['h', 'e', 'l', 'l', 'o']
        assert data_type_code(data) == 320


class TestMonadicDRViaInterpreter:
    def test_dr_integer(self) -> None:
        assert Interpreter(io=1).run("⎕DR 42") == S(323)

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
        result = Interpreter(io=1).run("320 ⎕DR 65 66 67")
        assert list(result.data) == ["A", "B", "C"]

    def test_dr_to_float(self) -> None:
        result = Interpreter(io=1).run("645 ⎕DR 42")
        assert result == S(42)

    def test_dr_to_int(self) -> None:
        result = Interpreter(io=1).run("323 ⎕DR 3.0")
        assert result.data[0] == 3
        assert isinstance(result.data.tolist()[0], int)

    def test_dr_to_boolean(self) -> None:
        result = Interpreter(io=1).run("81 ⎕DR 1 0 1")
        assert Interpreter(io=1).run("⎕DR 81 ⎕DR 1 0 1") == S(81)
