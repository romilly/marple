"""Class-based APL interpreter for MARPLE."""

import time
from typing import Any

from marple.arraymodel import APLArray, S
from marple.backend import (
    _DOWNCAST_CT, is_numeric_array, maybe_downcast,
)
from marple.errors import DomainError, ValueError_
from marple.functions import (
    add,
    negate,
    reciprocal,
    ceiling,
    floor,
    exponential,
    natural_log,
    absolute_value,
    logical_not,
    pi_times,
    subtract,
    multiply,
    divide,
    maximum,
    minimum,
    power,
    logarithm,
    residue,
    logical_and,
    logical_or,
    circular,
)
from marple.structural import (
    catenate,
    drop,
    encode,
    decode,
    expand,
    iota,
    ravel,
    replicate,
    replicate_first,
    reshape,
    reverse,
    rotate,
    shape,
    take,
    transpose,
    matrix_inverse,
    matrix_divide,
)
from marple.parser import (
    Alpha,
    AlphaAlpha,
    AlphaDefault,
    Assignment,
    Dfn,
    DyadicDfnCall,
    DyadicFunc,
    Guard,
    MonadicDfnCall,
    MonadicFunc,
    Num,
    Omega,
    Program,
    Str,
    SysVar,
    Var,
    Vector,
    parse,
)


# Name classes (following Dyalog ⎕NC convention)
NC_UNKNOWN = 0
NC_ARRAY = 2
NC_FUNCTION = 3
NC_OPERATOR = 4

_READONLY_QUADS = frozenset({"⎕A", "⎕D", "⎕TS", "⎕EN", "⎕DM"})

_SYSTEM_DEFAULTS: dict[str, Any] = {
    "⎕IO": S(1),
    "⎕CT": S(1e-14),
    "⎕PP": S(10),
    "⎕EN": S(0),
    "⎕DM": APLArray([0], []),
    "⎕A": APLArray([26], list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")),
    "⎕D": APLArray([10], list("0123456789")),
    "⎕WSID": APLArray([8], list("CLEAR WS")),
    "⎕RL": S(1),
    "⎕FR": S(645),
}

_SYS_FUNCTION_NAMES = (
    "⎕EA", "⎕UCS", "⎕NC", "⎕EX", "⎕SIGNAL", "⎕DR",
    "⎕NREAD", "⎕NWRITE", "⎕NEXISTS", "⎕NDELETE",
    "⎕CR", "⎕FX",
)


class _DfnBinding:
    """A dfn paired with its defining environment."""

    def __init__(self, dfn: Dfn, env: dict[str, Any]) -> None:
        self.dfn = dfn
        self.env = env


class _GuardTriggered(Exception):
    """Raised when a guard condition is true to return its value."""

    def __init__(self, value: APLArray) -> None:
        self.value = value


def _ljust(s: str, width: int) -> str:
    return s + " " * max(0, width - len(s))


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


class Interpreter:

    # ── Monadic primitives (no env needed) ──
    _MONADIC_SIMPLE: dict[str, object] = {
        "+": lambda omega: omega,
        "-": negate,
        "×": lambda omega: S((-1 if omega.data[0] < 0 else 1 if omega.data[0] > 0 else 0)),
        "÷": reciprocal,
        "⌈": ceiling,
        "⌊": floor,
        "*": exponential,
        "⍟": natural_log,
        "|": absolute_value,
        "~": logical_not,
        "⍴": shape,
        ",": ravel,
        "⌽": reverse,
        "⍉": transpose,
        "⌹": matrix_inverse,
        "○": pi_times,
    }

    # ── Dyadic primitives (no env needed) ──
    _DYADIC_SIMPLE: dict[str, object] = {
        "+": add,
        "-": subtract,
        "×": multiply,
        "÷": divide,
        "⌈": maximum,
        "⌊": minimum,
        "*": power,
        "⍟": logarithm,
        "|": residue,
        "∧": logical_and,
        "∨": logical_or,
        "⍴": reshape,
        ",": catenate,
        "↑": take,
        "↓": drop,
        "⌽": rotate,
        "⊤": encode,
        "⊥": decode,
        "/": replicate,
        "⌿": replicate_first,
        "\\": expand,
        "⌹": matrix_divide,
        "○": circular,
    }

    def __init__(self, io: int | None = None) -> None:
        from marple.config import get_default_io
        effective_io = io if io is not None else get_default_io()
        self.env: dict[str, Any] = dict(_SYSTEM_DEFAULTS)
        self.env["⎕IO"] = S(effective_io)

    def _get_io(self) -> int:
        return int(self.env["⎕IO"].data[0])

    def _get_ct(self) -> float:
        return float(self.env["⎕CT"].data[0])

    def run(self, source: str) -> APLArray:
        """Parse and evaluate APL source code."""
        name_table = self.env.get("__name_table__", {})
        for qfn in _SYS_FUNCTION_NAMES:
            name_table[qfn] = NC_FUNCTION
        self.env["__name_table__"] = name_table
        op_arity = self.env.get("__operator_arity__", {})
        source = _newlines_to_diamonds(source)
        tree = parse(source, name_table, op_arity)
        result = self._evaluate(tree)
        # Track source for dfn assignments
        if isinstance(tree, Assignment):
            value = self.env.get(tree.name)
            if isinstance(value, _DfnBinding):
                if "__sources__" not in self.env:
                    self.env["__sources__"] = {}
                self.env["__sources__"][tree.name] = source.strip()
                if "⍺⍺" in source or "⍵⍵" in source:
                    name_table = self.env.get("__name_table__", {})
                    name_table[tree.name] = NC_OPERATOR
                    self.env["__name_table__"] = name_table
                    arity = 2 if "⍵⍵" in source else 1
                    op_ar = self.env.get("__operator_arity__", {})
                    op_ar[tree.name] = arity
                    self.env["__operator_arity__"] = op_ar
        if isinstance(result, _DfnBinding):
            return S(0)
        if isinstance(result, APLArray) and is_numeric_array(result.data):
            result = APLArray(list(result.shape), maybe_downcast(result.data, _DOWNCAST_CT))
        return result

    def _evaluate(self, node: object) -> APLArray:
        """Evaluate an AST node."""
        if isinstance(node, Num):
            return self._eval_num(node)
        if isinstance(node, Str):
            return self._eval_str(node)
        if isinstance(node, Vector):
            return self._eval_vector(node)
        if isinstance(node, Var):
            return self._eval_var(node)
        if isinstance(node, SysVar):
            return self._eval_sysvar(node)
        if isinstance(node, MonadicFunc):
            return self._eval_monadic_func(node)
        if isinstance(node, DyadicFunc):
            return self._eval_dyadic_func(node)
        if isinstance(node, Assignment):
            return self._eval_assignment(node)
        if isinstance(node, Dfn):
            return _DfnBinding(node, self.env)  # type: ignore[return-value]
        if isinstance(node, MonadicDfnCall):
            return self._eval_monadic_dfn_call(node)
        if isinstance(node, DyadicDfnCall):
            return self._eval_dyadic_dfn_call(node)
        if isinstance(node, Program):
            return self._eval_program(node)
        if isinstance(node, Omega):
            if "⍵" not in self.env:
                raise ValueError_("⍵ used outside of dfn")
            return self.env["⍵"]
        if isinstance(node, Alpha):
            if "⍺" not in self.env:
                raise ValueError_("⍺ used outside of dfn")
            return self.env["⍺"]
        if isinstance(node, AlphaAlpha):
            if "⍺⍺" not in self.env:
                raise ValueError_("⍺⍺ used outside of dop")
            return self.env["⍺⍺"]  # type: ignore[return-value]
        raise DomainError(f"Unknown AST node: {type(node)}")

    def _eval_num(self, node: Num) -> APLArray:
        value = node.value
        if isinstance(value, float) and int(self.env.get("⎕FR", S(645)).data[0]) == 1287:
            from decimal import Decimal
            value = Decimal(str(node.value))
        return S(value)

    def _eval_str(self, node: Str) -> APLArray:
        chars = list(node.value)
        return APLArray([len(chars)], chars)

    def _eval_vector(self, node: Vector) -> APLArray:
        values = [el.value for el in node.elements]
        return APLArray([len(values)], list(values))

    def _eval_var(self, node: Var) -> APLArray:
        if node.name not in self.env:
            raise ValueError_(f"Undefined variable: {node.name}")
        return self.env[node.name]  # type: ignore[return-value]

    def _eval_sysvar(self, node: SysVar) -> APLArray:
        if node.name == "⎕TS":
            now = time.time()
            t = time.localtime(now)
            frac = now % 1
            if frac == 0 and hasattr(time, "ticks_ms"):
                ms = time.ticks_ms() % 1000  # type: ignore[attr-defined]
            else:
                ms = int(frac * 1000)
            return APLArray([7], [t[0], t[1], t[2], t[3], t[4], t[5], ms])
        if node.name == "⎕VER":
            from marple import __version__
            import sys
            s = "MARPLE v" + __version__ + " on " + sys.platform
            return APLArray([len(s)], list(s))
        if node.name not in self.env:
            raise ValueError_(f"Undefined system variable: {node.name}")
        return self.env[node.name]

    def _eval_monadic_func(self, node: MonadicFunc) -> APLArray:
        operand = self._evaluate(node.operand)
        return self._dispatch_monadic(node.function, operand)

    def _eval_dyadic_func(self, node: DyadicFunc) -> APLArray:
        right = self._evaluate(node.right)
        left = self._evaluate(node.left)
        return self._dispatch_dyadic(node.function, left, right)

    def _dispatch_monadic(self, glyph: str, operand: APLArray) -> APLArray:
        """Dispatch a monadic primitive function."""
        # Env-dependent monadic functions
        if glyph == "⍳":
            io = self._get_io()
            n = int(operand.data[0])
            return APLArray([n], list(range(io, n + io)))
        if glyph == "≢":
            return S(1) if operand.is_scalar() else S(operand.shape[0])
        func = self._MONADIC_SIMPLE.get(glyph)
        if func is not None:
            return func(operand)  # type: ignore[operator]
        raise DomainError(f"Unknown monadic function: {glyph}")

    def _dispatch_dyadic(self, glyph: str, left: APLArray, right: APLArray) -> APLArray:
        """Dispatch a dyadic primitive function."""
        func = self._DYADIC_SIMPLE.get(glyph)
        if func is not None:
            return func(left, right)  # type: ignore[operator]
        raise DomainError(f"Unknown dyadic function: {glyph}")

    def _eval_assignment(self, node: Assignment) -> APLArray:
        if node.name in _READONLY_QUADS:
            raise DomainError(f"Cannot assign to read-only system variable {node.name}")
        value = self._evaluate(node.value)
        if isinstance(value, APLArray) and is_numeric_array(value.data):
            value = APLArray(list(value.shape), maybe_downcast(value.data, _DOWNCAST_CT))
        name_table = self.env.get("__name_table__", {})
        if isinstance(value, _DfnBinding):
            new_class = NC_FUNCTION
        elif isinstance(value, APLArray):
            new_class = NC_ARRAY
        else:
            new_class = NC_UNKNOWN
        name_table[node.name] = new_class
        self.env["__name_table__"] = name_table
        self.env[node.name] = value
        return value if isinstance(value, APLArray) else S(0)

    def _eval_monadic_dfn_call(self, node: MonadicDfnCall) -> APLArray:
        # System function dispatch
        if isinstance(node.dfn, SysVar):
            return self._call_sys_monadic(node.dfn.name, node.operand)
        dfn_val = self._evaluate(node.dfn)
        operand = self._evaluate(node.operand)
        if isinstance(dfn_val, _DfnBinding):
            return self._call_dfn(dfn_val, operand)
        raise DomainError(f"Expected dfn, got {type(dfn_val)}")

    def _eval_dyadic_dfn_call(self, node: DyadicDfnCall) -> APLArray:
        dfn_val = self._evaluate(node.dfn)
        right = self._evaluate(node.right)
        left = self._evaluate(node.left)
        if isinstance(dfn_val, _DfnBinding):
            return self._call_dfn(dfn_val, right, alpha=left)
        raise DomainError(f"Expected dfn, got {type(dfn_val)}")

    def _eval_program(self, node: Program) -> APLArray:
        result: APLArray | _DfnBinding = S(0)
        for stmt in node.statements:
            result = self._evaluate(stmt)
        return result if isinstance(result, APLArray) else S(0)

    def _call_dfn(
        self,
        closure: _DfnBinding,
        omega: APLArray,
        alpha: APLArray | None = None,
        alpha_alpha: object | None = None,
        omega_omega: object | None = None,
    ) -> APLArray:
        """Execute a dfn with the given arguments."""
        saved_env = self.env
        local_env: dict[str, Any] = dict(closure.env)
        local_env["⍵"] = omega
        if alpha is not None:
            local_env["⍺"] = alpha
        if alpha_alpha is not None:
            local_env["⍺⍺"] = alpha_alpha
        if omega_omega is not None:
            local_env["⍵⍵"] = omega_omega
        local_env["∇"] = closure
        self.env = local_env
        result = S(0)
        try:
            for stmt in closure.dfn.body:
                if isinstance(stmt, AlphaDefault):
                    if "⍺" not in self.env:
                        self.env["⍺"] = self._evaluate(stmt.default)
                elif isinstance(stmt, Guard):
                    cond = self._evaluate(stmt.condition)
                    if cond.data[0]:
                        raise _GuardTriggered(self._evaluate(stmt.body))
                else:
                    result = self._evaluate(stmt)
        except _GuardTriggered as g:
            return g.value
        finally:
            self.env = saved_env
        return result

    def _call_sys_monadic(self, name: str, operand_node: object) -> APLArray:
        """Dispatch a monadic system function call."""
        operand = self._evaluate(operand_node)
        if name == "⎕NC":
            nc_name = "".join(str(c) for c in operand.data)
            name_table = self.env.get("__name_table__", {})
            return S(name_table.get(nc_name, 0))
        if name == "⎕EX":
            return self._sys_ex(operand)
        if name == "⎕NL":
            return self._sys_nl(operand)
        raise DomainError(f"Unknown system function: {name}")

    def _sys_ex(self, operand: APLArray) -> APLArray:
        name_table = self.env.get("__name_table__", {})
        if len(operand.shape) == 2:
            rows, cols = operand.shape
            count = 0
            for r in range(rows):
                name = "".join(str(c) for c in operand.data[r * cols:(r + 1) * cols]).rstrip()
                if name in self.env:
                    del self.env[name]
                    if name in name_table:
                        del name_table[name]
                    count += 1
            return S(count)
        ex_name = "".join(str(c) for c in operand.data).rstrip()
        if ex_name in self.env:
            del self.env[ex_name]
            if ex_name in name_table:
                del name_table[ex_name]
            return S(1)
        return S(0)

    def _sys_nl(self, operand: APLArray) -> APLArray:
        nc = int(operand.data[0])
        name_table = self.env.get("__name_table__", {})
        names = sorted(n for n, c in name_table.items()
                       if c == nc and not n.startswith("⎕") and not n.startswith("__"))
        if not names:
            return APLArray([0, 0], [])
        max_len = max(len(n) for n in names)
        chars: list[object] = []
        for n in names:
            chars.extend(list(_ljust(n, max_len)))
        return APLArray([len(names), max_len], chars)
