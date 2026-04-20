"""End-to-end tests for MARPLE running on a Raspberry Pi Pico 2.

Sends APL expressions over USB serial and verifies the responses. Runs
only against real hardware — the `pico` fixture auto-skips when no
Pico is attached.

Run: pytest tests/e2e/hardware/pico -m hardware [--pico-port /dev/ttyACM0]
"""

import pytest

from marple.adapters.pico_serial import PicoConnection

pytestmark = [pytest.mark.slow, pytest.mark.hardware]


class TestPicoArithmetic:
    def test_addition(self, pico: PicoConnection) -> None:
        assert pico.eval("2+3") == "5"

    def test_subtraction(self, pico: PicoConnection) -> None:
        assert pico.eval("10-4") == "6"

    def test_multiplication(self, pico: PicoConnection) -> None:
        assert pico.eval("3\u00d77") == "21"

    def test_division(self, pico: PicoConnection) -> None:
        assert pico.eval("15\u00f75") == "3"

    def test_high_minus(self, pico: PicoConnection) -> None:
        assert pico.eval("\u00af3+5") == "2"

    def test_right_to_left(self, pico: PicoConnection) -> None:
        assert pico.eval("1+2\u00d73") == "7"


class TestPicoVectors:
    def test_iota(self, pico: PicoConnection) -> None:
        assert pico.eval("\u23735") == "1 2 3 4 5"

    def test_vector_add(self, pico: PicoConnection) -> None:
        assert pico.eval("1 2 3+10 20 30") == "11 22 33"

    def test_scalar_extension(self, pico: PicoConnection) -> None:
        assert pico.eval("10\u00d7\u23735") == "10 20 30 40 50"

    def test_shape(self, pico: PicoConnection) -> None:
        assert pico.eval("\u2374 1 2 3 4 5") == "5"

    def test_reverse(self, pico: PicoConnection) -> None:
        assert pico.eval("\u233d 1 2 3 4 5") == "5 4 3 2 1"


class TestPicoReduce:
    def test_sum(self, pico: PicoConnection) -> None:
        assert pico.eval("+/\u2373100") == "5050"

    def test_product(self, pico: PicoConnection) -> None:
        assert pico.eval("\u00d7/\u23736") == "720"

    def test_scan(self, pico: PicoConnection) -> None:
        assert pico.eval("+\\1 2 3 4 5") == "1 3 6 10 15"


class TestPicoMatrices:
    def test_reshape(self, pico: PicoConnection) -> None:
        assert pico.eval("2 3\u2374\u23736") == "1 2 3\n4 5 6"

    def test_matrix_reduce(self, pico: PicoConnection) -> None:
        pico.eval_silent("M\u21902 3\u2374\u23736")
        assert pico.eval("+/M") == "6 15"

    def test_transpose(self, pico: PicoConnection) -> None:
        pico.eval_silent("M\u21902 3\u2374\u23736")
        assert pico.eval("\u2349M") == "1 4\n2 5\n3 6"


class TestPicoDfns:
    def test_simple_dfn(self, pico: PicoConnection) -> None:
        assert pico.eval("{\u2375+\u2375} 21") == "42"

    def test_named_dfn(self, pico: PicoConnection) -> None:
        pico.eval_silent("double\u2190{\u2375+\u2375}")
        assert pico.eval("double 7") == "14"

    def test_guard(self, pico: PicoConnection) -> None:
        pico.eval_silent(
            "sign\u2190{\u2375>0:1 \u22c4 \u2375<0:\u00af1 \u22c4 0}"
        )
        assert pico.eval("sign 42") == "1"
        assert pico.eval("sign \u00af7") == "\u00af1"
        assert pico.eval("sign 0") == "0"


class TestPicoSystemVars:
    def test_io(self, pico: PicoConnection) -> None:
        assert pico.eval("\u2395IO") == "1"

    def test_a(self, pico: PicoConnection) -> None:
        assert pico.eval("\u2395A") == "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def test_d(self, pico: PicoConnection) -> None:
        assert pico.eval("\u2395D") == "0123456789"

    def test_ts_has_seven_elements(self, pico: PicoConnection) -> None:
        assert pico.eval("\u2374\u2395TS") == "7"


class TestPicoErrorHandling:
    def test_domain_error(self, pico: PicoConnection) -> None:
        assert "DOMAIN ERROR" in pico.eval("1\u00f70")

    def test_length_error(self, pico: PicoConnection) -> None:
        assert "LENGTH ERROR" in pico.eval("1 2+1 2 3")
