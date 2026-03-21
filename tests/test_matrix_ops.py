from marple.arraymodel import APLArray, S
from marple.interpreter import interpret


class TestMatrixInverse:
    def test_inverse_2x2(self) -> None:
        # ⌹2 2⍴1 0 0 1 → identity (inverse of identity is identity)
        result = interpret("⌹2 2⍴1 0 0 1")
        assert result.shape == [2, 2]
        assert _approx(result.data, [1, 0, 0, 1])

    def test_inverse_simple(self) -> None:
        # ⌹2 2⍴2 0 0 2 → 0.5 0 0 0.5
        result = interpret("⌹2 2⍴2 0 0 2")
        assert result.shape == [2, 2]
        assert _approx(result.data, [0.5, 0, 0, 0.5])


class TestMatrixDivide:
    def test_solve_linear_system(self) -> None:
        # Solve Ax=b: b⌹A
        # A = 2 2⍴1 0 0 1, b = 3 4 → x = 3 4
        env: dict[str, APLArray] = {}
        interpret("A←2 2⍴1 0 0 1", env)
        result = interpret("3 4⌹A", env)
        assert _approx(result.data, [3, 4])


def _approx(actual: list[object], expected: list[float], tol: float = 1e-10) -> bool:
    if len(actual) != len(expected):
        return False
    for a, e in zip(actual, expected):
        if abs(float(a) - e) > tol:  # type: ignore[arg-type]
            return False
    return True
