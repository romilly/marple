"""Monadic primitive function dispatch for MARPLE."""


from marple.arraymodel import APLArray, S


from marple.environment import Environment
from marple.errors import DomainError
import random as _random



class MonadicFunctionBinding:
    """Dispatches and applies monadic primitive functions."""

    _SIMPLE: dict[str, object] = {
        "+": lambda omega: omega.conjugate(),
        "-": lambda omega: omega.negate(),
        "×": lambda omega: omega.signum(),
        "÷": lambda omega: omega.reciprocal(),
        "⌈": lambda omega: omega.ceiling(),
        "⌊": lambda omega: omega.floor(),
        "*": lambda omega: omega.exponential(),
        "⍟": lambda omega: omega.natural_log(),
        "|": lambda omega: omega.absolute_value(),
        "~": lambda omega: omega.logical_not(),
        "⍴": lambda omega: omega.shape_of(),
        ",": lambda omega: omega.ravel(),
        "⌽": lambda omega: omega.reverse(),
        "⊖": lambda omega: omega.reverse_first(),
        "⍉": lambda omega: omega.transpose(),
        "⌹": lambda omega: omega.matrix_inverse(),
        "○": lambda omega: omega.pi_times(),
        "!": lambda omega: omega.factorial(),
        "≢": lambda omega: omega.tally(),
    }

    _ENV_DEPENDENT: dict[str, str] = {
        "⍳": "_iota",
        "⍋": "_grade_up",
        "⍒": "_grade_down",
        "?": "_roll",
        "⍕": "_format",
    }

    def __init__(self, env: Environment) -> None:
        self._env = env

    def apply(self, glyph: str, operand: APLArray) -> APLArray:
        """Apply a monadic primitive function to an operand."""
        method_name = self._ENV_DEPENDENT.get(glyph)
        if method_name is not None:
            return getattr(self, method_name)(operand)
        func = self._SIMPLE.get(glyph)
        if func is not None:
            return func(operand)  # type: ignore[operator]
        raise DomainError(f"Unknown monadic function: {glyph}")

    def _iota(self, operand: APLArray) -> APLArray:
        return operand.iota(io=self._env.io)

    def _tally(self, operand: APLArray) -> APLArray:
        return S(1) if operand.is_scalar() else S(operand.shape[0])

    def _grade_up(self, operand: APLArray) -> APLArray:
        return operand.grade_up(io=self._env.io)

    def _grade_down(self, operand: APLArray) -> APLArray:
        return operand.grade_down(io=self._env.io)

    def _roll(self, operand: APLArray) -> APLArray:
        """Monadic ?: roll. ?N → random int ⎕IO..N, ?0 → random float [0,1)."""
        io = self._env.io
        def roll_one(v: object) -> object:
            n = int(v)  # type: ignore[arg-type]
            return _random.random() if n == 0 else _random.randint(io, n - 1 + io)
        if operand.is_scalar():
            return S(roll_one(operand.data[0]))
        return APLArray.array(list(operand.shape), [roll_one(v) for v in operand.data])

    def _format(self, operand: APLArray) -> APLArray:
        from marple.formatting import format_num
        if operand.is_scalar():
            s = format_num(operand.data[0])
        else:
            parts = [format_num(val) for val in operand.data]
            s = " ".join(parts)
        return APLArray.array([len(s)], list(s))
