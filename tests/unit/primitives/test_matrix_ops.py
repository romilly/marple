"""Matrix inverse and divide tests — new engine."""

import numpy as np

from marple.ports.array import APLArray, S
from marple.engine import Interpreter


class TestMatrixInverse:
    def test_inverse_2x2(self) -> None:
        result = Interpreter(io=1).run("⌹2 2⍴1 0 0 1")
        assert result.shape == [2, 2]
        assert np.allclose(result.data, np.array([[1, 0], [0, 1]]))

    def test_inverse_simple(self) -> None:
        result = Interpreter(io=1).run("⌹2 2⍴2 0 0 2")
        assert result.shape == [2, 2]
        assert np.allclose(result.data, np.array([[0.5, 0], [0, 0.5]]))


class TestMatrixDivide:
    def test_solve_linear_system(self) -> None:
        i = Interpreter(io=1)
        i.run("A←2 2⍴1 0 0 1")
        result = i.run("3 4⌹A")
        assert np.allclose(result.data, np.array([3, 4]))
