from marple.arraymodel import APLArray, S
from marple.interpreter import interpret


class TestStatementSeparator:
    def test_two_statements_returns_last(self) -> None:
        assert interpret("3⋄5") == S(5)

    def test_assignment_then_use(self) -> None:
        assert interpret("x←3⋄x+1") == S(4)

    def test_multiple_assignments(self) -> None:
        assert interpret("x←2⋄y←3⋄x+y") == S(5)
