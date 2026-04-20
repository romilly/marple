"""Tests for function trains — atop (2-train) and fork (3-train).

    (g h) ω     ≡  g (h ω)                  2-train atop (monadic)
    α (g h) ω   ≡  g (α h ω)               2-train atop (dyadic)
    (f g h) ω   ≡  (f ω) g (h ω)           3-train fork (monadic)
    α (f g h) ω ≡  (α f ω) g (α h ω)      3-train fork (dyadic)
    (A g h) ω   ≡  A g (h ω)              Agh-fork (monadic)
"""

import pytest

from marple.engine import Interpreter
from marple.errors import SyntaxError_
from marple.ports.array import APLArray, S


class TestAtopMonadic:
    """2-train monadic: `(g h) ω ≡ g (h ω)`."""

    def test_reverse_iota(self) -> None:
        """`(⌽⍳) 5` — reverse of ⍳5 → 4 3 2 1 0."""
        result = Interpreter(io=0).run("(⌽⍳) 5")
        assert result == APLArray.array([5], [4, 3, 2, 1, 0])


class TestAtopDyadic:
    """2-train dyadic: `α (g h) ω ≡ g (α h ω)`."""

    def test_floor_of_plus(self) -> None:
        """`3 (⌊+) 7` — ⌊(3+7) → 10."""
        result = Interpreter(io=0).run("3 (⌊+) 7")
        assert result == S(10)


class TestForkMonadic:
    """3-train monadic fork: `(f g h) ω ≡ (f ω) g (h ω)`."""

    def test_negate_catenate_reciprocal(self) -> None:
        """`(-,÷) 5` — (-5),(÷5) → [-5, 0.2]."""
        result = Interpreter(io=0).run("(-,÷) 5")
        assert result == APLArray.array([2], [-5, 0.2])


class TestForkDyadic:
    """3-train dyadic fork: `α (f g h) ω ≡ (α f ω) g (α h ω)`."""

    def test_plus_catenate_times(self) -> None:
        """`2 (+,×) 3` — (2+3),(2×3) → [5, 6]."""
        result = Interpreter(io=0).run("2 (+,×) 3")
        assert result == APLArray.array([2], [5, 6])


class TestAghForkMonadic:
    """Agh-fork: `(A g h) ω ≡ A g (h ω)` — leftmost item is an array."""

    def test_ten_plus_negate(self) -> None:
        """`(10 + -) 3` — 10 + (-3) → 7."""
        result = Interpreter(io=0).run("(10 + -) 3")
        assert result == S(7)


class TestTrainWithBoundOperators:
    """Trains containing adverb/conjunction-bound items like +⌿ or ⌊/."""

    def test_mean(self) -> None:
        """`(+⌿÷≢) 1 2 3 4 5` — mean → 3."""
        result = Interpreter(io=0).run("(+⌿÷≢) 1 2 3 4 5")
        assert result == S(3)

    def test_min_max(self) -> None:
        """`(⌊/,⌈/) 3 1 4 1 5 9` — [min, max] → [1, 9]."""
        result = Interpreter(io=0).run("(⌊/,⌈/) 3 1 4 1 5 9")
        assert result == APLArray.array([2], [1, 9])


class TestUnparenthesisedAssignment:
    """Trains assigned without parentheses: `name←f g h`."""

    def test_negrec(self) -> None:
        """`negrec←-,÷ ⋄ negrec 5` → [-5, 0.2]."""
        i = Interpreter(io=0)
        result = i.run("negrec←-,÷ ⋄ negrec 5")
        assert result == APLArray.array([2], [-5, 0.2])

    def test_mean(self) -> None:
        """`mean←+⌿÷≢ ⋄ mean 1 2 3 4 5` → 3."""
        i = Interpreter(io=0)
        result = i.run("mean←+⌿÷≢ ⋄ mean 1 2 3 4 5")
        assert result == S(3)


class TestLongerTrains:
    """4+ item trains decompose right-to-left in groups of 3."""

    def test_four_train_atop_fork(self) -> None:
        """`g←⌽⌊/,⌈/ ⋄ g 3 1 4 1 5 9` → [9, 1].
        4-train: atop(⌽, fork(⌊/,,,⌈/))."""
        i = Interpreter(io=0)
        result = i.run("g←⌽⌊/,⌈/ ⋄ g 3 1 4 1 5 9")
        assert result == APLArray.array([2], [9, 1])

    def test_five_train_fork_fork(self) -> None:
        """`f←⌊,⌈,+ ⋄ f 3 1 4` → [3,1,4,3,1,4,3,1,4].
        5-train: fork(⌊, ,, fork(⌈, ,, +))."""
        i = Interpreter(io=0)
        result = i.run("f←⌊,⌈,+ ⋄ f 3 1 4")
        assert result == APLArray.array([9], [3, 1, 4, 3, 1, 4, 3, 1, 4])


class TestTrainErrors:
    """Error cases that must match Dyalog."""

    def test_array_in_four_train_is_syntax_error(self) -> None:
        """`(10 + - ÷) 3` — array at non-leftmost position in 4-train → SYNTAX ERROR."""
        with pytest.raises(SyntaxError_):
            Interpreter(io=0).run("(10 + - ÷) 3")


class TestNamedTrainComposition:
    """Trains stored in variables and composed with other trains."""

    def test_rev_of_min_max(self) -> None:
        """`rev_mm←⌽min_max` composes reverse with a stored fork.
        Separate run() calls needed: the parser classifies names at
        parse time, so min_max must be in the name table before
        `⌽min_max` is parsed as a 2-train (V V) rather than
        monadic application (V N)."""
        i = Interpreter(io=0)
        i.run("min_max←⌊/,⌈/")
        i.run("rev_mm←⌽min_max")
        result = i.run("rev_mm 3 1 4 1 5 9")
        assert result == APLArray.array([2], [9, 1])
