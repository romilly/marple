"""Tests for data_type_code — backend dtype-to-⎕DR-code mapping."""

import numpy

from marple.ports.array import str_to_char_array, data_type_code


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
        data = str_to_char_array("hello")
        assert data_type_code(data) == 320
