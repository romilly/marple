"""Match and tally tests — new engine."""

from marple.ports.array import APLArray, S
from marple.engine import Interpreter


class TestMatch:
    def test_identical_scalars(self) -> None:
        assert Interpreter(io=1).run("3≡3") == S(1)

    def test_different_scalars(self) -> None:
        assert Interpreter(io=1).run("3≡4") == S(0)

    def test_identical_vectors(self) -> None:
        assert Interpreter(io=1).run("1 2 3≡1 2 3") == S(1)

    def test_different_values(self) -> None:
        assert Interpreter(io=1).run("1 2 3≡1 2 4") == S(0)

    def test_different_shapes(self) -> None:
        assert Interpreter(io=1).run("3≡3 3 3") == S(0)

    def test_exact_comparison(self) -> None:
        assert Interpreter(io=1).run("(÷3)≡(÷3)") == S(1)


class TestNotMatch:
    def test_identical(self) -> None:
        assert Interpreter(io=1).run("3≢3") == S(0)

    def test_different(self) -> None:
        assert Interpreter(io=1).run("3≢4") == S(1)

    def test_different_shapes(self) -> None:
        assert Interpreter(io=1).run("1 2 3≢1 2") == S(1)


class TestTally:
    def test_tally_vector(self) -> None:
        assert Interpreter(io=1).run("≢1 2 3 4 5") == S(5)

    def test_tally_matrix(self) -> None:
        assert Interpreter(io=1).run("≢2 3⍴⍳6") == S(2)

    def test_tally_scalar(self) -> None:
        assert Interpreter(io=1).run("≢5") == S(1)
