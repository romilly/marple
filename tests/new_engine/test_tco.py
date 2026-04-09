"""Tail call optimization tests — new engine."""

import sys

import pytest

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter


class TestTailRecursiveFactorial:
    def test_factorial_small(self) -> None:
        i = Interpreter(io=1)
        i.run("fact←{⍺←1 ⋄ ⍵=0:⍺ ⋄ (⍺×⍵)∇ ⍵-1}")
        assert i.run("fact 5") == S(120)

    def test_factorial_large_no_stack_overflow(self) -> None:
        i = Interpreter(io=1)
        i.run("fact←{⍺←1 ⋄ ⍵=0:⍺ ⋄ (⍺×⍵)∇ ⍵-1}")
        # Should not hit Python's recursion limit
        result = i.run("fact 1000")
        assert result.data.item() > 0


class TestTailRecursiveGCD:
    def test_gcd(self) -> None:
        i = Interpreter(io=1)
        i.run("gcd←{⍵=0:⍺ ⋄ ⍵ ∇ ⍵|⍺}")
        assert i.run("12 gcd 8") == S(4)

    def test_gcd_coprime(self) -> None:
        i = Interpreter(io=1)
        i.run("gcd←{⍵=0:⍺ ⋄ ⍵ ∇ ⍵|⍺}")
        assert i.run("17 gcd 13") == S(1)


@pytest.mark.slow
class TestDeepTailRecursion:
    def test_countdown_deep(self) -> None:
        """Tail-recursive countdown from 10000 — must not overflow."""
        i = Interpreter(io=1)
        i.run("count←{⍵=0:0 ⋄ ∇ ⍵-1}")
        assert i.run("count 10000") == S(0)

    def test_accumulate_deep(self) -> None:
        """Tail-recursive sum from 10000 — must not overflow."""
        i = Interpreter(io=1)
        i.run("sum←{⍺←0 ⋄ ⍵=0:⍺ ⋄ (⍺+⍵)∇ ⍵-1}")
        assert i.run("sum 10000") == S(50005000)


class TestNonTailRecursionStillWorks:
    def test_non_tail_factorial(self) -> None:
        """Non-tail recursion uses the stack — should work for small inputs."""
        i = Interpreter(io=1)
        i.run("fact←{⍵≤1:1 ⋄ ⍵×∇ ⍵-1}")
        assert i.run("fact 10") == S(3628800)


class TestTailCallInGuards:
    def test_guard_tail_call(self) -> None:
        i = Interpreter(io=1)
        i.run("sign←{⍵>0:1 ⋄ ⍵<0:¯1 ⋄ 0}")
        assert i.run("sign 5") == S(1)
        assert i.run("sign ¯3") == S(-1)
        assert i.run("sign 0") == S(0)

    def test_multiple_guard_branches_with_tail_calls(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{⍵>100:⍵ ⋄ ⍵<0:∇ -⍵ ⋄ ∇ ⍵×2}")
        assert i.run("f 3") == S(192)
        assert i.run("f ¯5") == S(160)


class TestMonadicTailCall:
    def test_monadic_tail(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{⍵≥100:⍵ ⋄ ∇ ⍵+1}")
        assert i.run("f 0") == S(100)
