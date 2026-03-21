from marple.arraymodel import APLArray, S
from marple.interpreter import interpret


class TestReduce:
    def test_sum(self) -> None:
        # +/1 2 3 4 → 10
        assert interpret("+/1 2 3 4") == S(10)

    def test_product(self) -> None:
        # ×/1 2 3 4 → 24
        assert interpret("×/1 2 3 4") == S(24)

    def test_right_to_left(self) -> None:
        # -/1 2 3 → 1-(2-3) → 2
        assert interpret("-/1 2 3") == S(2)

    def test_maximum_reduce(self) -> None:
        # ⌈/3 1 4 1 5 → 5
        assert interpret("⌈/3 1 4 1 5") == S(5)

    def test_single_element(self) -> None:
        # +/5 → 5
        assert interpret("+/5") == S(5)


class TestScan:
    def test_running_sum(self) -> None:
        # +\1 2 3 → 1 3 6
        result = interpret(r"+\1 2 3")
        assert result == APLArray([3], [1, 3, 6])

    def test_running_product(self) -> None:
        # ×\1 2 3 4 → 1 2 6 24
        result = interpret(r"×\1 2 3 4")
        assert result == APLArray([4], [1, 2, 6, 24])

    def test_running_max(self) -> None:
        # ⌈\3 1 4 1 5 → 3 3 4 4 5
        result = interpret(r"⌈\3 1 4 1 5")
        assert result == APLArray([5], [3, 3, 4, 4, 5])
