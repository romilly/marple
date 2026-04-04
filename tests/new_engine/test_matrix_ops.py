"""Matrix inverse and divide tests — new engine."""

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter


def _approx(actual: list[object], expected: list[float], tol: float = 1e-10) -> bool:
    if len(actual) != len(expected):
        return False
    for a, e in zip(actual, expected):
        if abs(float(a) - e) > tol:  # type: ignore[arg-type]
            return False
    return True


class TestMatrixInverse:
    def test_inverse_2x2(self) -> None:
        result = Interpreter(io=1).run("⌹2 2⍴1 0 0 1")
        assert result.shape == [2, 2]
        assert _approx(result.data, [1, 0, 0, 1])

    def test_inverse_simple(self) -> None:
        result = Interpreter(io=1).run("⌹2 2⍴2 0 0 2")
        assert result.shape == [2, 2]
        assert _approx(result.data, [0.5, 0, 0, 0.5])


class TestMatrixDivide:
    def test_solve_linear_system(self) -> None:
        i = Interpreter(io=1)
        i.run("A←2 2⍴1 0 0 1")
        result = i.run("3 4⌹A")
        assert _approx(result.data, [3, 4])
