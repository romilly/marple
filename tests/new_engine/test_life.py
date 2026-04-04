"""Conway's Game of Life tests — flat array with outer product shifts."""

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter


class TestLifeWithRank:
    def test_rotate_rank_0_2(self) -> None:
        """(⌽⍤0 2) applies scalar rotations to full matrix."""
        i = Interpreter(io=1)
        i.run("G←3 3⍴0 1 0 0 0 1 1 1 1")
        result = i.run("¯1 0 1(⌽⍤0 2)G")
        # 3 rotations of G stacked: shape 3×3×3
        assert result.shape == [3, 3, 3]
        # First slice: ¯1⌽G (rotate right)
        assert list(result.data[:9]) == list(i.run("¯1⌽G").data)
        # Second slice: 0⌽G (unchanged)
        assert list(result.data[9:18]) == list(i.run("G").data)
        # Third slice: 1⌽G (rotate left)
        assert list(result.data[18:27]) == list(i.run("1⌽G").data)


class TestLifeShiftDfn:
    def test_shift_pair(self) -> None:
        """A dfn that applies vertical and horizontal shift from a pair."""
        i = Interpreter(io=1)
        i.run("G←3 3⍴0 1 0 0 0 1 1 1 1")
        i.run("shift←{(1↑⍺)⊖(1↓⍺)⌽⍵}")
        # 1 ¯1 shift: 1⊖¯1⌽G
        result = i.run("1 ¯1 shift G")
        expected = i.run("1⊖¯1⌽G")
        assert result == expected

    def test_shift_with_rank_all_neighbours(self) -> None:
        """Apply shift to all 8 neighbour pairs using rank, then sum."""
        i = Interpreter(io=1)
        i.run("G←6 6⍴0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1 0 0 0 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0")
        i.run("shift←{(1↑⍺)⊖(1↓⍺)⌽⍵}")
        i.run("S←4 2⍴¯1 0 1 0 0 ¯1 0 1")
        i.run("D←4 2⍴¯1 ¯1 ¯1 1 1 ¯1 1 1")
        # Each row of S/D is a shift pair; apply with rank 1 2
        # Then sum along first axis to get neighbour count
        i.run("N←(+⌿S(shift⍤1 2)G)+(+⌿D(shift⍤1 2)G)")
        i.run("R←(N=3)∨G∧N=2")
        result = i.run("R")
        # Compare with explicit version
        i.run("life←{N←(1⊖⍵)+(¯1⊖⍵)+(1⌽⍵)+(¯1⌽⍵)+(1⊖1⌽⍵)+(1⊖¯1⌽⍵)+(¯1⊖1⌽⍵)+(¯1⊖¯1⌽⍵) ⋄ (N=3)∨⍵∧N=2}")
        expected = i.run("life G")
        assert result == expected


class TestLifeCompact:
    def test_all_8_in_one_matrix(self) -> None:
        """All 8 neighbour shifts in one 8×2 matrix, summed with +⌿."""
        i = Interpreter(io=1)
        i.run("G←6 6⍴0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1 0 0 0 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0")
        i.run("shift←{(1↑⍺)⊖(1↓⍺)⌽⍵}")
        i.run("P←8 2⍴¯1 0 1 0 0 ¯1 0 1 ¯1 ¯1 ¯1 1 1 ¯1 1 1")
        i.run("life←{N←+⌿P(shift⍤1 2)⍵ ⋄ (N=3)∨⍵∧N=2}")
        result = i.run("life G")
        i.run("life2←{N←(1⊖⍵)+(¯1⊖⍵)+(1⌽⍵)+(¯1⌽⍵)+(1⊖1⌽⍵)+(1⊖¯1⌽⍵)+(¯1⊖1⌽⍵)+(¯1⊖¯1⌽⍵) ⋄ (N=3)∨⍵∧N=2}")
        expected = i.run("life2 G")
        assert result == expected


class TestLifeGenerated:
    def test_generate_offsets(self) -> None:
        """Generate all 9 shift pairs from encode and iota."""
        i = Interpreter(io=1)
        result = i.run("(⍉3 3⊤(⍳9)-1)-1")
        assert result.shape == [9, 2]
        pairs = [(int(result.data[r*2]), int(result.data[r*2+1])) for r in range(9)]
        assert (0, 0) in pairs
        assert (-1, -1) in pairs
        assert (1, 1) in pairs

    def test_generated_life_matches(self) -> None:
        """Life using generated P matches hardcoded version."""
        i = Interpreter(io=1)
        i.run("G←6 6⍴0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1 0 0 0 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0")
        i.run("shift←{(1↑⍺)⊖(1↓⍺)⌽⍵}")
        i.run("P←(⍉3 3⊤(⍳9)-1)-1")
        i.run("life←{N←(+⌿P(shift⍤1 2)⍵)-⍵ ⋄ (N=3)∨⍵∧N=2}")
        result = i.run("(life⍣4) G")
        expected = APLArray.array([6, 6], [
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 1, 0, 0,
            0, 0, 0, 0, 1, 0,
            0, 0, 1, 1, 1, 0,
            0, 0, 0, 0, 0, 0,
        ])
        assert result == expected


class TestLifeSelfContained:
    def test_self_contained_life(self) -> None:
        """Life as a single self-contained dfn."""
        i = Interpreter(io=1)
        i.run("G←6 6⍴0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1 0 0 0 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0")
        i.run("life←{s←{(1↑⍺)⊖(1↓⍺)⌽⍵} ⋄ P←(⍉3 3⊤(⍳9)-1)-1 ⋄ N←(+⌿P(s⍤1 2)⍵)-⍵ ⋄ (N=3)∨⍵∧N=2}")
        result = i.run("(life⍣4) G")
        expected = APLArray.array([6, 6], [
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 1, 0, 0,
            0, 0, 0, 0, 1, 0,
            0, 0, 1, 1, 1, 0,
            0, 0, 0, 0, 0, 0,
        ])
        assert result == expected


class TestLifeGlider:
    def test_glider_one_step(self) -> None:
        i = Interpreter(io=1)
        i.run("G←6 6⍴0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1 0 0 0 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0")
        i.run("life←{s←{(1↑⍺)⊖(1↓⍺)⌽⍵} ⋄ P←(⍉3 3⊤(⍳9)-1)-1 ⋄ N←(+⌿P(s⍤1 2)⍵)-⍵ ⋄ (N=3)∨⍵∧N=2}")
        result = i.run("life G")
        expected = APLArray.array([6, 6], [
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
            0, 1, 0, 1, 0, 0,
            0, 0, 1, 1, 0, 0,
            0, 0, 1, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
        ])
        assert result == expected

    def test_glider_four_steps_with_power(self) -> None:
        """After 4 steps the glider moves down-right by 1."""
        i = Interpreter(io=1)
        i.run("G←6 6⍴0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1 0 0 0 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0")
        i.run("life←{s←{(1↑⍺)⊖(1↓⍺)⌽⍵} ⋄ P←(⍉3 3⊤(⍳9)-1)-1 ⋄ N←(+⌿P(s⍤1 2)⍵)-⍵ ⋄ (N=3)∨⍵∧N=2}")
        result = i.run("(life⍣4) G")
        expected = APLArray.array([6, 6], [
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 1, 0, 0,
            0, 0, 0, 0, 1, 0,
            0, 0, 1, 1, 1, 0,
            0, 0, 0, 0, 0, 0,
        ])
        assert result == expected
