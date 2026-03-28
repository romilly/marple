"""Executor: shared AST evaluation logic for the MARPLE interpreter."""

from __future__ import annotations

import time
from typing import Any, TYPE_CHECKING

from marple.arraymodel import APLArray, S
from marple.backend import (
    _DOWNCAST_CT, is_numeric_array, maybe_downcast,
)
from marple.cells import clamp_rank, decompose, reassemble, resolve_rank_spec
from marple.errors import DomainError, ValueError_
from marple.dyadic_functions import DyadicFunctionBinding
from marple.monadic_functions import MonadicFunctionBinding
from marple.operator_binding import DerivedFunctionBinding
from marple.parser import (
    BoundOperator,
    Dfn,
    FunctionRef,
    Node,
    RankDerived,
    ReduceOp,
    ScanOp,
)
from marple.symbol_table import NC_ARRAY, NC_FUNCTION, NC_OPERATOR, NC_UNKNOWN

if TYPE_CHECKING:
    from marple.environment import Environment

_READONLY_QUADS = frozenset({"⎕A", "⎕D", "⎕TS", "⎕EN", "⎕DM"})


def _newlines_to_diamonds(source: str) -> str:
    """Convert newlines to ⋄ (statement separator), preserving strings."""
    result: list[str] = []
    in_string = False
    for ch in source:
        if ch == "'" and not in_string:
            in_string = True
            result.append(ch)
        elif ch == "'" and in_string:
            in_string = False
            result.append(ch)
        elif ch == "\n" and not in_string:
            result.append("⋄")
        else:
            result.append(ch)
    return "".join(result)


def _ljust(s: str, width: int) -> str:
    return s + " " * max(0, width - len(s))


def _apl_chars_to_str(data: Any) -> str:
    """Convert an APLArray's character data to a Python string."""
    return "".join(str(c) for c in data)


def _name_class(value: object) -> int:
    """Return the APL name class for a value."""
    from marple.dfn_binding import DfnBinding
    if isinstance(value, DfnBinding):
        return NC_FUNCTION
    if isinstance(value, APLArray):
        return NC_ARRAY
    return NC_UNKNOWN


class Executor:
    """Base class providing AST evaluation, shared by Interpreter and DfnBinding."""

    env: Environment

    # ── String-keyed dispatch tables (class-level, shared) ──

    _SYSVAR_DISPATCH: dict[str, str] = {
        "⎕TS": "_sysvar_ts",
        "⎕VER": "_sysvar_ver",
    }

    _SYS_FN_DISPATCH: dict[str, str] = {
        "⎕NC": "_sys_nc",
        "⎕EX": "_sys_ex",
        "⎕NL": "_sys_nl",
    }

    # ── Core evaluation ──

    def evaluate(self, node: Node | object) -> APLArray:
        """Evaluate an AST node by calling its execute method."""
        if isinstance(node, Node):
            return node.execute(self)  # type: ignore[return-value]
        raise DomainError(f"Unknown AST node: {type(node)}")

    # ── Callback methods for node execute() ──

    def dispatch_monadic(self, glyph: str, operand: APLArray) -> APLArray:
        return MonadicFunctionBinding(self.env).apply(glyph, operand)

    def dispatch_dyadic(self, glyph: str, left: APLArray, right: APLArray) -> APLArray:
        return DyadicFunctionBinding(self.env).apply(glyph, left, right)

    def apply_derived(self, operator: str, function: object, operand: APLArray) -> APLArray:
        return DerivedFunctionBinding().apply(operator, function, operand)

    def assign(self, name: str, value_node: object) -> APLArray:
        if name in _READONLY_QUADS:
            raise DomainError(f"Cannot assign to read-only system variable {name}")
        value = self.evaluate(value_node)
        if isinstance(value, APLArray) and is_numeric_array(value.data):
            value = APLArray(list(value.shape), maybe_downcast(value.data, _DOWNCAST_CT))
        self.env.bind_name(name, value, _name_class(value))
        return value if isinstance(value, APLArray) else S(0)

    def create_binding(self, dfn_node: Dfn) -> object:
        from marple.dfn_binding import DfnBinding
        # Store a reference to env, not a copy — names added later
        # (e.g. forward references) are visible at call time when
        # DfnBinding._make_env copies the env.
        return DfnBinding(dfn_node, self.env)

    def eval_sysvar(self, name: str) -> APLArray:
        method_name = self._SYSVAR_DISPATCH.get(name)
        if method_name is not None:
            return getattr(self, method_name)()
        if name not in self.env:
            raise ValueError_(f"Undefined system variable: {name}")
        return self.env[name]

    # ── System variables ──

    def _sysvar_ts(self) -> APLArray:
        now = time.time()
        t = time.localtime(now)
        frac = now % 1
        if frac == 0 and hasattr(time, "ticks_ms"):
            ms = time.ticks_ms() % 1000  # type: ignore[attr-defined]
        else:
            ms = int(frac * 1000)
        return APLArray([7], [t[0], t[1], t[2], t[3], t[4], t[5], ms])

    def _sysvar_ver(self) -> APLArray:
        from marple import __version__
        import sys
        s = "MARPLE v" + __version__ + " on " + sys.platform
        return APLArray([len(s)], list(s))

    # ── Rank operator ──

    def apply_rank_monadic(self, rank_node: RankDerived, operand_node: object) -> APLArray:
        omega = self.evaluate(operand_node)
        rank_spec_val = self.evaluate(rank_node.rank_spec)
        a, _, _ = resolve_rank_spec(rank_spec_val)
        k = clamp_rank(a, len(omega.shape))
        frame_shape, cells = decompose(omega, k)
        results = [self.apply_func_monadic(rank_node.function, cell) for cell in cells]
        return reassemble(frame_shape, results)

    def apply_func_monadic(self, func: object, omega: APLArray) -> APLArray:
        """Apply a function monadically. Used by rank operator."""
        if isinstance(func, str):
            return MonadicFunctionBinding(self.env).apply(func, omega)
        if isinstance(func, FunctionRef):
            return MonadicFunctionBinding(self.env).apply(func.glyph, omega)
        if isinstance(func, ReduceOp):
            return DerivedFunctionBinding().apply("/", func.function, omega)
        if isinstance(func, ScanOp):
            return DerivedFunctionBinding().apply("\\", func.function, omega)
        if isinstance(func, BoundOperator) and isinstance(func.operator, str):
            return DerivedFunctionBinding().apply(
                func.operator, func.left_operand, omega)
        raise DomainError(f"Expected function for rank, got {type(func)}")

    # ── System functions ──

    def dispatch_sys_monadic(self, name: str, operand_node: object) -> APLArray:
        operand = self.evaluate(operand_node)
        method_name = self._SYS_FN_DISPATCH.get(name)
        if method_name is not None:
            return getattr(self, method_name)(operand)
        raise DomainError(f"Unknown system function: {name}")

    def _sys_nc(self, operand: APLArray) -> APLArray:
        return S(self.env.name_class(_apl_chars_to_str(operand.data)))

    def _sys_ex(self, operand: APLArray) -> APLArray:
        if len(operand.shape) == 2:
            return self._sys_ex_matrix(operand)
        return self._expunge_name(_apl_chars_to_str(operand.data).rstrip())

    def _sys_ex_matrix(self, operand: APLArray) -> APLArray:
        rows, cols = operand.shape
        count = 0
        for r in range(rows):
            start = r * cols
            name = _apl_chars_to_str(operand.data[start:start + cols]).rstrip()
            result = self._expunge_name(name)
            count += int(result.data[0])
        return S(count)

    def _expunge_name(self, name: str) -> APLArray:
        """Remove a single name from the symbol table."""
        return S(1) if self.env.delete_name(name) else S(0)

    def _sys_nl(self, operand: APLArray) -> APLArray:
        nc = int(operand.data[0])
        names = self.env.names_of_class(nc)
        if not names:
            return APLArray([0, 0], [])
        max_len = max(len(n) for n in names)
        chars: list[object] = []
        for n in names:
            chars.extend(list(_ljust(n, max_len)))
        return APLArray([len(names), max_len], chars)
