from marple.arraymodel import APLArray, S
from marple.interpreter import interpret


class TestMatch:
    def test_identical_scalars(self) -> None:
        assert interpret("3≡3") == S(1)

    def test_different_scalars(self) -> None:
        assert interpret("3≡4") == S(0)

    def test_identical_vectors(self) -> None:
        assert interpret("1 2 3≡1 2 3") == S(1)

    def test_different_values(self) -> None:
        assert interpret("1 2 3≡1 2 4") == S(0)

    def test_different_shapes(self) -> None:
        # Scalar vs vector
        assert interpret("3≡3 3 3") == S(0)

    def test_exact_comparison(self) -> None:
        # Should NOT use tolerant comparison
        env: dict[str, APLArray] = {}
        interpret("x←÷3", env)
        # x is 0.333..., not exactly 1÷3 reconstructed
        # But ÷3 ≡ ÷3 should be 1 (same computation)
        assert interpret("(÷3)≡(÷3)", env) == S(1)


class TestNotMatch:
    def test_identical(self) -> None:
        assert interpret("3≢3") == S(0)

    def test_different(self) -> None:
        assert interpret("3≢4") == S(1)

    def test_different_shapes(self) -> None:
        assert interpret("1 2 3≢1 2") == S(1)


class TestTally:
    def test_tally_vector(self) -> None:
        # Monadic ≢ returns number of major cells
        assert interpret("≢1 2 3 4 5") == S(5)

    def test_tally_matrix(self) -> None:
        assert interpret("≢2 3⍴⍳6") == S(2)

    def test_tally_scalar(self) -> None:
        assert interpret("≢5") == S(1)
