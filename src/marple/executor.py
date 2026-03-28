"""Executor: shared AST evaluation logic for the MARPLE interpreter."""

from __future__ import annotations

import time
from typing import Any, TYPE_CHECKING

from marple.arraymodel import APLArray, S
from marple.backend import (
    _DOWNCAST_CT, is_numeric_array, maybe_downcast,
)
from marple.errors import DomainError, ValueError_
from marple.dyadic_functions import DyadicFunctionBinding
from marple.monadic_functions import MonadicFunctionBinding
from marple.operator_binding import DerivedFunctionBinding
from marple.symbol_table import NC_ARRAY, NC_FUNCTION, NC_OPERATOR, NC_UNKNOWN
from marple.cells import clamp_rank, decompose, reassemble, resolve_rank_spec
from marple.parser import (
    Alpha,
    AlphaAlpha,
    Assignment,
    BoundOperator,
    DerivedFunc,
    Dfn,
    DyadicDfnCall,
    DyadicFunc,
    FunctionRef,
    MonadicDfnCall,
    MonadicFunc,
    Num,
    Omega,
    Program,
    RankDerived,
    ReduceOp,
    ScanOp,
    Str,
    SysVar,
    Var,
    Vector,
)

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

    # ── Type-keyed eval dispatch (class-level, shared) ──

    _EVAL_DISPATCH: dict[type, str] = {
        Num: "_eval_num",
        Str: "_eval_str",
        Vector: "_eval_vector",
        Var: "_eval_var",
        SysVar: "_eval_sysvar",
        MonadicFunc: "_eval_monadic_func",
        DyadicFunc: "_eval_dyadic_func",
        Assignment: "_eval_assignment",
        DerivedFunc: "_eval_derived_func",
        Dfn: "_eval_dfn",
        MonadicDfnCall: "_eval_monadic_dfn_call",
        DyadicDfnCall: "_eval_dyadic_dfn_call",
        Program: "_eval_program",
        Omega: "_eval_omega",
        Alpha: "_eval_alpha",
        AlphaAlpha: "_eval_alpha_alpha",
    }

    # ── Core evaluation ──

    def _evaluate(self, node: object) -> APLArray:
        method_name = self._EVAL_DISPATCH.get(type(node))
        if method_name is not None:
            return getattr(self, method_name)(node)
        raise DomainError(f"Unknown AST node: {type(node)}")

    # ── Literal evaluators ──

    def _eval_num(self, node: Num) -> APLArray:
        value = node.value
        if isinstance(value, float) and self.env.fr == 1287:
            from decimal import Decimal
            value = Decimal(str(node.value))
        return S(value)

    def _eval_str(self, node: Str) -> APLArray:
        return APLArray([len(node.value)], list(node.value))

    def _eval_vector(self, node: Vector) -> APLArray:
        values = [el.value for el in node.elements]
        return APLArray([len(values)], list(values))

    # ── Variable evaluators ──

    def _eval_var(self, node: Var) -> APLArray:
        if node.name not in self.env:
            raise ValueError_(f"Undefined variable: {node.name}")
        return self.env[node.name]  # type: ignore[return-value]

    def _eval_sysvar(self, node: SysVar) -> APLArray:
        method_name = self._SYSVAR_DISPATCH.get(node.name)
        if method_name is not None:
            return getattr(self, method_name)()
        if node.name not in self.env:
            raise ValueError_(f"Undefined system variable: {node.name}")
        return self.env[node.name]

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

    def _eval_dfn(self, node: Dfn) -> APLArray:
        from marple.dfn_binding import DfnBinding
        # Store a reference to env, not a copy — names added later
        # (e.g. forward references) are visible at call time when
        # DfnBinding._make_env copies the env.
        return DfnBinding(node, self.env)  # type: ignore[return-value]

    def _eval_omega(self, node: Omega) -> APLArray:
        if "⍵" not in self.env:
            raise ValueError_("⍵ used outside of dfn")
        return self.env["⍵"]

    def _eval_alpha(self, node: Alpha) -> APLArray:
        if "⍺" not in self.env:
            raise ValueError_("⍺ used outside of dfn")
        return self.env["⍺"]

    def _eval_alpha_alpha(self, node: AlphaAlpha) -> APLArray:
        if "⍺⍺" not in self.env:
            raise ValueError_("⍺⍺ used outside of dop")
        return self.env["⍺⍺"]  # type: ignore[return-value]

    # ── Primitive function dispatch ──

    def _eval_monadic_func(self, node: MonadicFunc) -> APLArray:
        operand = self._evaluate(node.operand)
        return MonadicFunctionBinding(self.env).apply(node.function, operand)

    def _eval_dyadic_func(self, node: DyadicFunc) -> APLArray:
        right = self._evaluate(node.right)
        left = self._evaluate(node.left)
        return DyadicFunctionBinding(self.env).apply(node.function, left, right)

    def _eval_derived_func(self, node: DerivedFunc) -> APLArray:
        operand = self._evaluate(node.operand)
        return DerivedFunctionBinding().apply(node.operator, node.function, operand)

    # ── Assignment ──

    def _eval_assignment(self, node: Assignment) -> APLArray:
        if node.name in _READONLY_QUADS:
            raise DomainError(f"Cannot assign to read-only system variable {node.name}")
        value = self._evaluate(node.value)
        if isinstance(value, APLArray) and is_numeric_array(value.data):
            value = APLArray(list(value.shape), maybe_downcast(value.data, _DOWNCAST_CT))
        self._bind_name(node.name, value)
        return value if isinstance(value, APLArray) else S(0)

    def _bind_name(self, name: str, value: object) -> None:
        """Store a value in the symbol table with its name class."""
        self.env.bind_name(name, value, _name_class(value))

    # ── Dfn / dop calls ──

    def _eval_monadic_dfn_call(self, node: MonadicDfnCall) -> APLArray:
        from marple.dfn_binding import DfnBinding
        if isinstance(node.dfn, SysVar):
            return self._dispatch_sys_monadic(node.dfn.name, node.operand)
        if isinstance(node.dfn, RankDerived):
            return self._apply_rank_monadic(node.dfn, node.operand)
        dfn_val = self._evaluate(node.dfn)
        operand = self._evaluate(node.operand)
        if isinstance(dfn_val, DfnBinding):
            return dfn_val.apply(operand)
        raise DomainError(f"Expected dfn, got {type(dfn_val)}")

    def _eval_dyadic_dfn_call(self, node: DyadicDfnCall) -> APLArray:
        from marple.dfn_binding import DfnBinding
        dfn_val = self._evaluate(node.dfn)
        right = self._evaluate(node.right)
        left = self._evaluate(node.left)
        if isinstance(dfn_val, DfnBinding):
            return dfn_val.apply(right, alpha=left)
        raise DomainError(f"Expected dfn, got {type(dfn_val)}")

    def _eval_program(self, node: Program) -> APLArray:
        from marple.dfn_binding import DfnBinding
        result: APLArray | DfnBinding = S(0)
        for stmt in node.statements:
            result = self._evaluate(stmt)
        return result if isinstance(result, APLArray) else S(0)

    # ── Rank operator ──

    def _apply_rank_monadic(self, rank_node: RankDerived, operand_node: object) -> APLArray:
        omega = self._evaluate(operand_node)
        rank_spec_val = self._evaluate(rank_node.rank_spec)
        a, _, _ = resolve_rank_spec(rank_spec_val)
        k = clamp_rank(a, len(omega.shape))
        frame_shape, cells = decompose(omega, k)
        results = [self._apply_func_monadic(rank_node.function, cell) for cell in cells]
        return reassemble(frame_shape, results)

    def _apply_func_monadic(self, func: object, omega: APLArray) -> APLArray:
        """Apply a function monadically. Used by rank operator."""
        if isinstance(func, str):
            return MonadicFunctionBinding(self.env).apply(func, omega)
        if isinstance(func, FunctionRef):
            return MonadicFunctionBinding(self.env).apply(func.glyph, omega)
        if isinstance(func, ReduceOp):
            return DerivedFunctionBinding().apply("/", func.function, omega)
        if isinstance(func, ScanOp):
            return DerivedFunctionBinding().apply("\\", func.function, omega)
        if isinstance(func, BoundOperator):
            return DerivedFunctionBinding().apply(
                func.operator, func.left_operand, omega)
        raise DomainError(f"Expected function for rank, got {type(func)}")

    # ── System functions ──

    def _dispatch_sys_monadic(self, name: str, operand_node: object) -> APLArray:
        operand = self._evaluate(operand_node)
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
