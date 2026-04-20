"""Life with ⎕IO←0 inside the dfn."""

from marple.ports.array import APLArray, S
from marple.engine import Interpreter


class TestLifeIO0:
    def test_life_with_local_io0(self) -> None:
        i = Interpreter(io=1)
        i.run("G←6 6⍴0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1 0 0 0 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0")
        i.run("life←{⎕IO←0 ⋄ s←{(1↑⍺)⊖(1↓⍺)⌽⍵} ⋄ P←(⍉3 3⊤⍳9)-1 ⋄ N←(+⌿P(s⍤1 2)⍵)-⍵ ⋄ (N=3)∨⍵∧N=2}")
        result = i.run("(life⍣4) G")
        expected = APLArray.array([6, 6], [
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 1, 1, 1, 0],
            [0, 0, 0, 0, 0, 0],
        ])
        assert result == expected

    def test_io_not_leaked(self) -> None:
        """⎕IO←0 inside dfn should not affect caller."""
        i = Interpreter(io=1)
        i.run("life←{⎕IO←0 ⋄ s←{(1↑⍺)⊖(1↓⍺)⌽⍵} ⋄ P←(⍉3 3⊤⍳9)-1 ⋄ N←(+⌿P(s⍤1 2)⍵)-⍵ ⋄ (N=3)∨⍵∧N=2}")
        i.run("G←6 6⍴0")
        i.run("life G")
        assert i.run("⎕IO") == S(1)
