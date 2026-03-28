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

_NAME_CLASS: dict[type, int] = {
    APLArray: NC_ARRAY,
}


class _DfnBinding:
    """A dfn or dop bound to the environment in which it was defined."""

    def __init__(self, dfn: Dfn, env: dict[str, Any]) -> None:
        self.dfn = dfn
        self.env = env


_NAME_CLASS[_DfnBinding] = NC_FUNCTION  # type: ignore[index]


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


def _apl_chars_to_str(data: Any) -> str:
    """Convert an APLArray's character data to a Python string."""
    return "".join(str(c) for c in data)


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
        self._eval_dispatch: dict[type, Any] = {
            Num: self._eval_num,
            Str: self._eval_str,
            Vector: self._eval_vector,
            Var: self._eval_var,
            SysVar: self._eval_sysvar,
            MonadicFunc: self._eval_monadic_func,
            DyadicFunc: self._eval_dyadic_func,
            Assignment: self._eval_assignment,
            Dfn: self._eval_dfn,
            MonadicDfnCall: self._eval_monadic_dfn_call,
            DyadicDfnCall: self._eval_dyadic_dfn_call,
            Program: self._eval_program,
            Omega: self._eval_omega,
            Alpha: self._eval_alpha,
            AlphaAlpha: self._eval_alpha_alpha,
        }
        self._sysvar_dispatch: dict[str, Any] = {
            "⎕TS": self._sysvar_ts,
            "⎕VER": self._sysvar_ver,
        }
        self._sys_fn_dispatch: dict[str, Any] = {
            "⎕NC": self._sys_nc,
            "⎕EX": self._sys_ex,
            "⎕NL": self._sys_nl,
        }
        self._monadic_env_dispatch: dict[str, Any] = {
            "⍳": self._monadic_iota,
            "≢": self._monadic_tally,
        }

    def _get_io(self) -> int:
        return int(self.env["⎕IO"].data[0])

    def _get_ct(self) -> float:
        return float(self.env["⎕CT"].data[0])

    # ── Top-level run ──

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
        if isinstance(tree, Assignment):
            self._track_dfn_source(tree.name, source)
        if isinstance(result, _DfnBinding):
            return S(0)
        if isinstance(result, APLArray) and is_numeric_array(result.data):
            result = APLArray(list(result.shape), maybe_downcast(result.data, _DOWNCAST_CT))
        return result

    def _track_dfn_source(self, name: str, source: str) -> None:
        """Record source text for dfn/dop assignments (for workspace save)."""
        value = self.env.get(name)
        if not isinstance(value, _DfnBinding):
            return
        sources = self.env.setdefault("__sources__", {})
        sources[name] = source.strip()
        if "⍺⍺" not in source and "⍵⍵" not in source:
            return
        name_table = self.env.get("__name_table__", {})
        name_table[name] = NC_OPERATOR
        self.env["__name_table__"] = name_table
        op_ar = self.env.setdefault("__operator_arity__", {})
        op_ar[name] = 2 if "⍵⍵" in source else 1

    # ── Eval dispatch ──

    def _evaluate(self, node: object) -> APLArray:
        """Evaluate an AST node."""
        handler = self._eval_dispatch.get(type(node))
        if handler is not None:
            return handler(node)
        raise DomainError(f"Unknown AST node: {type(node)}")

    # ── Literal evaluators ──

    def _eval_num(self, node: Num) -> APLArray:
        value = node.value
        if isinstance(value, float) and int(self.env.get("⎕FR", S(645)).data[0]) == 1287:
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
        handler = self._sysvar_dispatch.get(node.name)
        if handler is not None:
            return handler()
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
        return _DfnBinding(node, self.env)  # type: ignore[return-value]

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
        return self._dispatch_monadic(node.function, operand)

    def _eval_dyadic_func(self, node: DyadicFunc) -> APLArray:
        right = self._evaluate(node.right)
        left = self._evaluate(node.left)
        return self._dispatch_dyadic(node.function, left, right)

    def _monadic_iota(self, operand: APLArray) -> APLArray:
        io = self._get_io()
        n = int(operand.data[0])
        return APLArray([n], list(range(io, n + io)))

    def _monadic_tally(self, operand: APLArray) -> APLArray:
        return S(1) if operand.is_scalar() else S(operand.shape[0])

    def _dispatch_monadic(self, glyph: str, operand: APLArray) -> APLArray:
        handler = self._monadic_env_dispatch.get(glyph)
        if handler is not None:
            return handler(operand)
        func = self._MONADIC_SIMPLE.get(glyph)
        if func is not None:
            return func(operand)  # type: ignore[operator]
        raise DomainError(f"Unknown monadic function: {glyph}")

    def _dispatch_dyadic(self, glyph: str, left: APLArray, right: APLArray) -> APLArray:
        func = self._DYADIC_SIMPLE.get(glyph)
        if func is not None:
            return func(left, right)  # type: ignore[operator]
        raise DomainError(f"Unknown dyadic function: {glyph}")

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
        """Store a value in the environment and update the name table."""
        name_table = self.env.get("__name_table__", {})
        name_table[name] = _NAME_CLASS.get(type(value), NC_UNKNOWN)
        self.env["__name_table__"] = name_table
        self.env[name] = value

    # ── Dfn / dop application ──

    def _eval_monadic_dfn_call(self, node: MonadicDfnCall) -> APLArray:
        if isinstance(node.dfn, SysVar):
            return self._dispatch_sys_monadic(node.dfn.name, node.operand)
        dfn_val = self._evaluate(node.dfn)
        operand = self._evaluate(node.operand)
        if isinstance(dfn_val, _DfnBinding):
            return self._apply_dfn(dfn_val, operand)
        raise DomainError(f"Expected dfn, got {type(dfn_val)}")

    def _eval_dyadic_dfn_call(self, node: DyadicDfnCall) -> APLArray:
        dfn_val = self._evaluate(node.dfn)
        right = self._evaluate(node.right)
        left = self._evaluate(node.left)
        if isinstance(dfn_val, _DfnBinding):
            return self._apply_dfn(dfn_val, right, alpha=left)
        raise DomainError(f"Expected dfn, got {type(dfn_val)}")

    def _eval_program(self, node: Program) -> APLArray:
        result: APLArray | _DfnBinding = S(0)
        for stmt in node.statements:
            result = self._evaluate(stmt)
        return result if isinstance(result, APLArray) else S(0)

    def _apply_dfn(
        self,
        binding: _DfnBinding,
        omega: APLArray,
        alpha: APLArray | None = None,
        alpha_alpha: object | None = None,
        omega_omega: object | None = None,
    ) -> APLArray:
        """Apply a dfn or dop binding to its arguments."""
        saved_env = self.env
        self.env = self._make_dfn_env(binding, omega, alpha, alpha_alpha, omega_omega)
        try:
            return self._execute_body(binding.dfn.body)
        finally:
            self.env = saved_env

    def _make_dfn_env(
        self,
        binding: _DfnBinding,
        omega: APLArray,
        alpha: APLArray | None,
        alpha_alpha: object | None,
        omega_omega: object | None,
    ) -> dict[str, Any]:
        """Build the local environment for a dfn/dop call."""
        local_env: dict[str, Any] = dict(binding.env)
        local_env["⍵"] = omega
        if alpha is not None:
            local_env["⍺"] = alpha
        if alpha_alpha is not None:
            local_env["⍺⍺"] = alpha_alpha
        if omega_omega is not None:
            local_env["⍵⍵"] = omega_omega
        local_env["∇"] = binding
        return local_env

    def _execute_body(self, statements: list[object]) -> APLArray:
        """Execute a sequence of dfn body statements."""
        result = S(0)
        for stmt in statements:
            if isinstance(stmt, AlphaDefault):
                if "⍺" not in self.env:
                    self.env["⍺"] = self._evaluate(stmt.default)
            elif isinstance(stmt, Guard):
                cond = self._evaluate(stmt.condition)
                if cond.data[0]:
                    return self._evaluate(stmt.body)
            else:
                result = self._evaluate(stmt)
        return result

    # ── System functions ──

    def _dispatch_sys_monadic(self, name: str, operand_node: object) -> APLArray:
        operand = self._evaluate(operand_node)
        handler = self._sys_fn_dispatch.get(name)
        if handler is not None:
            return handler(operand)
        raise DomainError(f"Unknown system function: {name}")

    def _sys_nc(self, operand: APLArray) -> APLArray:
        name_table = self.env.get("__name_table__", {})
        return S(name_table.get(_apl_chars_to_str(operand.data), 0))

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
        """Remove a single name from the environment and name table."""
        if name not in self.env:
            return S(0)
        del self.env[name]
        name_table = self.env.get("__name_table__", {})
        name_table.pop(name, None)
        return S(1)

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
