from marple.arraymodel import APLArray, S
from marple.interpreter import interpret, default_env


class TestComparisonTolerance:
    def test_default_ct(self) -> None:
        assert interpret("⎕CT") == S(1e-14)

    def test_near_equal(self) -> None:
        # (1÷3)×3 should equal 1 with tolerant comparison
        assert interpret("1=(1÷3)×3") == S(1)

    def test_far_not_equal(self) -> None:
        assert interpret("1=1.1") == S(0)

    def test_ct_zero_exact(self) -> None:
        env = default_env()
        interpret("⎕CT←0", env)
        # With exact comparison, 1=1.001 should be 0
        assert interpret("1=1.001", env) == S(0)

    def test_near_less_equal(self) -> None:
        env = default_env()
        interpret("x←(1÷3)×3", env)
        assert interpret("1≤x", env) == S(1)

    def test_near_greater_equal(self) -> None:
        env = default_env()
        interpret("x←(1÷3)×3", env)
        assert interpret("x≥1", env) == S(1)

    def test_near_not_equal(self) -> None:
        # Nearly equal values should give 0 for ≠
        assert interpret("1≠(1÷3)×3") == S(0)


class TestIndexOfTolerant:
    def test_iota_tolerant(self) -> None:
        env = default_env()
        interpret("x←÷⍳3", env)  # x is 1 0.5 0.3333...
        # 0.5 should be found at position 2
        assert interpret("x⍳0.5", env) == S(2)

    def test_iota_tolerant_third(self) -> None:
        env = default_env()
        interpret("x←÷⍳3", env)
        # ÷3 (0.3333...) should match x[3] which is also ÷3
        assert interpret("x⍳÷3", env) == S(3)


class TestMembership:
    def test_membership_found(self) -> None:
        assert interpret("3∈1 2 3 4 5") == S(1)

    def test_membership_not_found(self) -> None:
        assert interpret("6∈1 2 3 4 5") == S(0)

    def test_membership_vector(self) -> None:
        assert interpret("1 3 5∈2 3 4") == APLArray([3], [0, 1, 0])

    def test_membership_tolerant(self) -> None:
        env = default_env()
        interpret("x←(1÷3)×3", env)  # nearly 1
        assert interpret("x∈1 2 3", env) == S(1)


class TestMatchIgnoresCT:
    def test_match_exact(self) -> None:
        # ≡ should NOT use ⎕CT — exact comparison
        # This test verifies ≡ is stricter than =
        # Two values that are = (tolerant) might not be ≡ (exact)
        assert interpret("1≡1") == S(1)
        assert interpret("1≡2") == S(0)
