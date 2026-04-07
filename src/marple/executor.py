"""Executor: shared AST evaluation logic for the MARPLE interpreter."""


from typing import Any

from marple.numpy_array import APLArray, S
from marple.formatting import format_num, format_result
from marple.backend_functions import (
    _DOWNCAST_CT, chars_to_str, is_char_array, is_numeric_array, maybe_downcast,
)
from marple.cells import clamp_rank, decompose, reassemble, resolve_rank_spec
from marple.errors import DomainError, SyntaxError_, ValueError_
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

from marple.environment import Environment
from marple.ports.filesystem import FileSystem

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
    return chars_to_str(data)


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

    @property
    def fs(self) -> 'FileSystem':
        return self.env.fs

    # ── String-keyed dispatch tables (class-level, shared) ──

    _SYSVAR_DISPATCH: dict[str, str] = {
        "⎕TS": "_sysvar_ts",
        "⎕AI": "_sysvar_ai",
        "⎕VER": "_sysvar_ver",
        "⎕WA": "_sysvar_wa",
        "⍞": "_sysvar_quote_quad",
        "⎕": "_sysvar_quad",
    }

    _SYS_FN_DISPATCH: dict[str, str] = {
        "⎕NC": "_sys_nc",
        "⎕EX": "_sys_ex",
        "⎕NL": "_sys_nl",
        "⎕UCS": "_sys_ucs",
        "⎕DR": "_sys_dr",
        "⎕SIGNAL": "_sys_signal",
        "⎕NREAD": "_sys_nread",
        "⎕NEXISTS": "_sys_nexists",
        "⎕NDELETE": "_sys_ndelete",
        "⎕CR": "_sys_cr",
        "⎕FX": "_sys_fx",
        "⎕DL": "_sys_dl",
        "⎕CSV": "_sys_csv",
    }

    # ── Core evaluation ──

    def evaluate(self, node: Node | object) -> APLArray:
        """Evaluate an AST node by calling its execute method."""
        if isinstance(node, Node):
            return node.execute(self)  # type: ignore[return-value]
        raise DomainError(f"Unknown AST node: {type(node)}")

    # ── Callback methods for node execute() ──

    def dispatch_monadic(self, glyph: str, operand: APLArray) -> APLArray:
        if glyph == "⍎":
            return self._execute_string(operand)
        return MonadicFunctionBinding(self.env).apply(glyph, operand)

    def _execute_string(self, operand: APLArray) -> APLArray:
        from marple.parser import parse
        source = chars_to_str(operand.data)
        tree = parse(source, self.env.class_dict())
        return self.evaluate(tree)

    def dispatch_dyadic(self, glyph: str, left: APLArray, right: APLArray) -> APLArray:
        return DyadicFunctionBinding(self.env).apply(glyph, left, right)

    def resolve_dyadic(self, fn: object) -> object:
        """Resolve a function reference to a dyadic callable."""
        from marple.parser import FunctionRef
        glyph = fn.glyph if isinstance(fn, FunctionRef) else fn
        if not isinstance(glyph, str):
            raise DomainError(f"Expected function for operator, got {type(fn)}")
        binding = DyadicFunctionBinding(self.env)
        return binding.resolve_with_env(glyph)

    def call_ibeam(self, path: str, operand: APLArray) -> APLArray:
        """Call a Python function via i-beam."""
        parts = path.rsplit(".", 1)
        if len(parts) != 2:
            raise DomainError(f"Invalid i-beam path: {path}")
        module_name, func_name = parts
        try:
            mod = __import__(module_name)
            for part in module_name.split(".")[1:]:
                mod = getattr(mod, part)
        except ImportError:
            raise DomainError(f"Cannot import module: {module_name}")
        func = getattr(mod, func_name, None)
        if func is None:
            raise DomainError(f"Function not found: {path}")
        result = func(operand)
        if not isinstance(result, APLArray):
            raise DomainError(f"I-beam function must return APLArray: {path}")
        return result

    def resolve_qualified(self, parts: list[str]) -> object:
        from marple.namespace import Namespace, load_system_workspace
        if parts[0] == "$":
            import marple.stdlib
            f = marple.stdlib.__file__
            stdlib_path = f[:f.rfind("/")] if "/" in f else f[:f.rfind("\\")]
            sys_ws = load_system_workspace(stdlib_path)
            result = sys_ws.resolve(parts[1:])
            if result is None:
                raise DomainError("Undefined: " + "::".join(parts))
            return result
        raise DomainError(f"Undefined namespace: {parts[0]}")

    def apply_derived(self, operator: str, function: object, operand: APLArray) -> APLArray:
        # If function is an AST node (e.g. Dfn), evaluate it first
        from marple.dfn_binding import DfnBinding
        from marple.parser import Node as ParserNode
        if isinstance(function, ParserNode):
            val = self.evaluate(function)
            if isinstance(val, DfnBinding):
                function = lambda a, o, _b=val: _b.apply(o, alpha=a)
            elif isinstance(val, FunctionRef):
                function = val.glyph
        return DerivedFunctionBinding().apply(operator, function, operand)

    def assign(self, name: str, value_node: object) -> APLArray:
        if name in _READONLY_QUADS:
            raise DomainError(f"Cannot assign to read-only system variable {name}")
        value = self.evaluate(value_node)
        if name in ("⎕", "⍞"):
            return self._io_assign(name, value)
        if isinstance(value, APLArray) and is_numeric_array(value.data):
            value = APLArray.array(list(value.shape), maybe_downcast(value.data, _DOWNCAST_CT))
        if name.startswith("⎕"):
            if name == "⎕FR" and isinstance(value, APLArray):
                fr_val = int(value.data[0])
                if fr_val not in (645, 1287):
                    raise DomainError(f"⎕FR must be 645 or 1287, got {fr_val}")
            if name == "⎕RL" and isinstance(value, APLArray):
                import random as _random
                _random.seed(int(value.data[0]))
            self.env[name] = value
        else:
            new_class = _name_class(value)
            old_class = self.env.name_class(name)
            if old_class != 0 and new_class != 0 and old_class != new_class:
                from marple.errors import ClassError
                raise ClassError(f"Cannot change class of '{name}' from {old_class} to {new_class}")
            self.env.bind_name(name, value, new_class)
        return value if isinstance(value, APLArray) else S(0)

    def _io_assign(self, name: str, value: APLArray) -> APLArray:
        """Handle ⎕← (output with newline) and ⍞← (prompt, read, return prompt+response)."""
        if self.env.console is None:
            raise DomainError("Console not available for I/O")
        text = format_result(value, self.env)
        if name == "⎕":
            self.env.console.writeln(text)
            return value
        # ⍞← : display prompt, read input, return response only (Dyalog style)
        line = self.env.console.read_line(text)
        if line is None:
            raise DomainError("⍞ input not available — use the terminal REPL for interactive input")
        self.env.console.writeln(text + line)
        response_chars: list[object] = list(line)
        return APLArray.array([len(response_chars)], response_chars)

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
            if name in self._SYS_FN_DISPATCH or name in self._DYADIC_SYS_FN_DISPATCH:
                raise SyntaxError_(f"{name} is a system function — it requires an argument")
            raise ValueError_(f"Undefined system variable: {name}")
        return self.env[name]

    # ── System variables ──

    def _sysvar_ts(self) -> APLArray:
        ts = self.env.timer.timestamp()
        return APLArray.array([7], ts)

    def _sysvar_ai(self) -> APLArray:
        timer = self.env.timer
        return APLArray.array([4], [timer.user_id(), timer.cpu_ms(), timer.elapsed_ms(), 0])

    def _sysvar_ver(self) -> APLArray:
        from marple import __version__
        import sys
        s = "MARPLE v" + __version__ + " on " + sys.platform
        return APLArray.array([len(s)], list(s))

    def _sysvar_wa(self) -> APLArray:
        """⎕WA — workspace available (free memory in bytes)."""
        import sys
        if sys.implementation.name == "micropython":
            import gc  # type: ignore[import-not-found]
            gc.collect()
            return APLArray.array([], [gc.mem_free()])
        return APLArray.array([], [2**31 - 1])

    def _sysvar_quad(self) -> APLArray:
        """⎕ — prompt, read, parse, and evaluate input as APL."""
        if self.env.console is None:
            raise DomainError("Console not available for I/O")
        line = self.env.console.read_line("⎕:")
        if line is None:
            raise DomainError("⎕ input not available — use the terminal REPL for interactive input")
        self.env.console.writeln("⎕:" + line)
        from marple.parser import parse
        tree = parse(line, self.env.class_dict())
        return self.evaluate(tree)

    def _sysvar_quote_quad(self) -> APLArray:
        """⍞ — read a line of character input (no prompt)."""
        if self.env.console is None:
            raise DomainError("Console not available for I/O")
        line = self.env.console.read_line("")
        if line is None:
            raise DomainError("⍞ input not available — use the terminal REPL for interactive input")
        self.env.console.writeln(line)
        return APLArray.array([len(line)], list(line))

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
        # AST node (Var, Dfn, etc.) — evaluate to get the function value, then apply
        from marple.dfn_binding import DfnBinding
        from marple.parser import Node
        if isinstance(func, Node):
            val = self.evaluate(func)
            if isinstance(val, DfnBinding):
                return val.apply(omega)
            if isinstance(val, FunctionRef):
                return MonadicFunctionBinding(self.env).apply(val.glyph, omega)
            if hasattr(val, 'dfn') and hasattr(val, 'env'):
                binding = DfnBinding(getattr(val, 'dfn'), self.env)
                return binding.apply(omega)
        raise DomainError(f"Expected function for rank, got {type(func)}")

    def apply_rank_dyadic(self, rank_node: object, left_node: object, right_node: object) -> APLArray:
        from marple.errors import LengthError
        from marple.parser import RankDerived
        assert isinstance(rank_node, RankDerived)
        alpha = self.evaluate(left_node)
        omega = self.evaluate(right_node)
        rank_spec_val = self.evaluate(rank_node.rank_spec)
        _, b_rank, c_rank = resolve_rank_spec(rank_spec_val)
        b = clamp_rank(b_rank, len(alpha.shape))
        c = clamp_rank(c_rank, len(omega.shape))
        left_frame, left_cells = decompose(alpha, b)
        right_frame, right_cells = decompose(omega, c)
        if left_frame == right_frame:
            pairs = list(zip(left_cells, right_cells))
            frame = left_frame
        elif left_frame == []:
            pairs = [(left_cells[0], rc) for rc in right_cells]
            frame = right_frame
        elif right_frame == []:
            pairs = [(lc, right_cells[0]) for lc in left_cells]
            frame = left_frame
        else:
            raise LengthError(f"Frame mismatch: {left_frame} vs {right_frame}")
        results = [self._apply_func_dyadic(rank_node.function, lc, rc) for lc, rc in pairs]
        return reassemble(frame, results)

    def _apply_func_dyadic(self, func: object, alpha: APLArray, omega: APLArray) -> APLArray:
        """Apply a function dyadically. Used by dyadic rank operator."""
        from marple.parser import FunctionRef
        if isinstance(func, str):
            return DyadicFunctionBinding(self.env).apply(func, alpha, omega)
        if isinstance(func, FunctionRef):
            return DyadicFunctionBinding(self.env).apply(func.glyph, alpha, omega)
        from marple.dfn_binding import DfnBinding
        from marple.parser import Node
        if isinstance(func, Node):
            val = self.evaluate(func)
            if isinstance(val, DfnBinding):
                return val.apply(omega, alpha=alpha)
            if isinstance(val, FunctionRef):
                return DyadicFunctionBinding(self.env).apply(val.glyph, alpha, omega)
        raise DomainError(f"Expected function for rank, got {type(func)}")

    # ── Power operator ──

    def apply_power_monadic(self, power_node: object, operand_node: object) -> APLArray:
        from marple.dfn_binding import DfnBinding
        from marple.parser import PowerDerived
        assert isinstance(power_node, PowerDerived)
        omega = self.evaluate(operand_node)
        right_op = power_node.right_operand
        right_val = self._resolve_power_operand(right_op)
        if isinstance(right_val, APLArray) and right_val.is_scalar():
            n = int(right_val.data[0])
            if n < 0:
                raise DomainError("DOMAIN ERROR: inverse (⍣ with negative) not supported")
            result = omega
            for _ in range(n):
                result = self.apply_func_monadic(power_node.function, result)
            return result
        if isinstance(right_val, (DfnBinding, FunctionRef)):
            prev = omega
            while True:
                curr = self.apply_func_monadic(power_node.function, prev)
                test = self._apply_func_dyadic_or_match(right_val, curr, prev)
                if test.data[0]:
                    return curr
                prev = curr
        raise DomainError("⍣ right operand must be integer or function")

    def apply_power_dyadic(self, power_node: object, left_node: object,
                           right_node: object) -> APLArray:
        from marple.dfn_binding import DfnBinding
        from marple.parser import PowerDerived
        assert isinstance(power_node, PowerDerived)
        alpha = self.evaluate(left_node)
        omega = self.evaluate(right_node)
        right_op = power_node.right_operand
        right_val = self._resolve_power_operand(right_op)
        if isinstance(right_val, APLArray) and right_val.is_scalar():
            n = int(right_val.data[0])
            if n < 0:
                raise DomainError("DOMAIN ERROR: inverse (⍣ with negative) not supported")
            result = omega
            for _ in range(n):
                result = self._apply_func_dyadic(power_node.function, alpha, result)
            return result
        if isinstance(right_val, (DfnBinding, FunctionRef)):
            prev = omega
            while True:
                curr = self._apply_func_dyadic(power_node.function, alpha, prev)
                test = self._apply_func_dyadic_or_match(right_val, curr, prev)
                if test.data[0]:
                    return curr
                prev = curr
        raise DomainError("⍣ right operand must be integer or function")

    def _resolve_power_operand(self, right_op: object) -> object:
        """Resolve the right operand of ⍣ — may be a glyph string, AST node, or value."""
        from marple.dfn_binding import DfnBinding
        if isinstance(right_op, str):
            # Primitive glyph like ≡ or =
            return FunctionRef(right_op)
        if isinstance(right_op, FunctionRef):
            return right_op
        result = self.evaluate(right_op)
        if isinstance(result, (DfnBinding, FunctionRef)):
            return result
        return result

    def _apply_func_dyadic_or_match(self, func: object, left: APLArray,
                                     right: APLArray) -> APLArray:
        """Apply a dyadic function for convergence test. Handles FunctionRef for ≡ and =."""
        from marple.dfn_binding import DfnBinding
        if isinstance(func, FunctionRef):
            if func.glyph == "≡":
                return S(1 if left == right else 0)
            if func.glyph == "=":
                return S(1 if left.data[0] == right.data[0] else 0)
            return DyadicFunctionBinding(self.env).apply(func.glyph, left, right)
        if isinstance(func, DfnBinding):
            return func.apply(right, alpha=left)
        raise DomainError("⍣ convergence function must be a function")

    # ── System functions ──

    _DYADIC_SYS_FN_DISPATCH: dict[str, str] = {
        "⎕EA": "_sys_ea",
        "⎕DR": "_sys_dr_dyadic",
        "⎕NWRITE": "_sys_nwrite",
    }

    def dispatch_sys_monadic(self, name: str, operand_node: object) -> APLArray:
        if name == "⎕FMT":
            return self._sys_fmt_monadic(operand_node)
        operand = self.evaluate(operand_node)
        method_name = self._SYS_FN_DISPATCH.get(name)
        if method_name is not None:
            return getattr(self, method_name)(operand)
        raise DomainError(f"Unknown system function: {name}")

    def dispatch_sys_dyadic(self, name: str, left_node: object, right_node: object) -> APLArray:
        if name == "⎕FMT":
            return self._sys_fmt_dyadic(left_node, right_node)
        method_name = self._DYADIC_SYS_FN_DISPATCH.get(name)
        if method_name is not None:
            left = self.evaluate(left_node)
            right = self.evaluate(right_node)
            return getattr(self, method_name)(left, right)
        raise DomainError(f"Unknown dyadic system function: {name}")

    def _sys_nc(self, operand: APLArray) -> APLArray:
        return S(self.env.name_class(_apl_chars_to_str(operand.data)))

    def _sys_ex(self, operand: APLArray) -> APLArray:
        if len(operand.shape) == 2:
            return self._sys_ex_matrix(operand)
        return self._expunge_name(_apl_chars_to_str(operand.data).rstrip())

    def _sys_ex_matrix(self, operand: APLArray) -> APLArray:
        rows, cols = operand.shape
        # Flatten first: 2D uint32 char data otherwise slices rows.
        flat = operand.data.flatten() if hasattr(operand.data, 'flatten') else operand.data
        count = 0
        for r in range(rows):
            start = r * cols
            name = _apl_chars_to_str(flat[start:start + cols]).rstrip()
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
            return APLArray.array([0, 0], [])
        max_len = max(len(n) for n in names)
        chars: list[object] = []
        for n in names:
            chars.extend(list(_ljust(n, max_len)))
        return APLArray.array([len(names), max_len], chars)

    def _sys_ucs(self, operand: APLArray) -> APLArray:
        from marple.backend_functions import is_ndarray, str_to_char_array, to_list
        from marple.get_numpy import np
        if is_char_array(operand.data):
            # uint32 ndarray: already codepoints, just retype.
            # list[str]: ord() each element.
            if is_ndarray(operand.data):
                return APLArray(list(operand.shape), operand.data.astype(np.int64))
            return APLArray.array(list(operand.shape), [ord(c) for c in operand.data])
        # Numeric → character: build a uint32 char array.
        data = to_list(operand.data)
        text = ''.join(chr(int(x)) for x in data)
        return APLArray(list(operand.shape), str_to_char_array(text))

    def _sys_dr(self, operand: APLArray) -> APLArray:
        from marple.backend_functions import data_type_code
        return S(data_type_code(operand.data))

    def _sys_signal(self, operand: APLArray) -> APLArray:
        from marple.errors import (
            SyntaxError_, ValueError_, LengthError,
            RankError, IndexError_, LimitError, SecurityError,
        )
        code = int(operand.data[0])
        error_map: dict[int, type] = {
            1: SyntaxError_, 2: ValueError_, 3: DomainError, 4: LengthError,
            5: RankError, 6: IndexError_, 7: LimitError, 9: SecurityError,
        }
        err_class = error_map.get(code, DomainError)
        raise err_class(f"Signalled by ⎕SIGNAL {code}")

    def _sys_ea(self, left: APLArray, right: APLArray) -> APLArray:
        """⎕EA: error-guarded execution. Try right; on error, execute left."""
        from marple.errors import APLError
        from marple.parser import parse
        right_str = _apl_chars_to_str(right.data)
        try:
            tree = parse(right_str, self.env.class_dict())
            return self.evaluate(tree)
        except APLError as e:
            self.env["⎕EN"] = S(e.code)
            self.env["⎕DM"] = APLArray.array([len(str(e))], list(str(e)))
            left_str = _apl_chars_to_str(left.data)
            tree = parse(left_str, self.env.class_dict())
            return self.evaluate(tree)

    def _sys_dr_dyadic(self, left: APLArray, right: APLArray) -> APLArray:
        """Dyadic ⎕DR: convert data representation."""
        from marple.backend_functions import to_list, to_bool_array
        target = int(left.data[0])
        vals = to_list(right.data)
        if target == 645:
            new_data = [float(v) for v in vals]
            return APLArray.array(list(right.shape), new_data)
        if target in (643, 323, 163, 83):
            new_data = [int(round(v)) for v in vals]
            return APLArray.array(list(right.shape), new_data)
        if target == 81:
            new_data = to_bool_array([int(bool(v)) for v in vals])
            return APLArray.array(list(right.shape), new_data)
        if target == 320:
            new_data = [chr(int(v)) for v in vals]
            return APLArray.array(list(right.shape), new_data)
        raise DomainError("Invalid ⎕DR type code: " + str(target))

    def _sys_fmt_monadic(self, operand_node: object) -> APLArray:
        """Monadic ⎕FMT — handles both regular operands and FmtArgs."""
        from marple.nodes import FmtArgs
        if isinstance(operand_node, FmtArgs):
            values = [self.evaluate(arg) for arg in operand_node.args]
            parts = [self._fmt_value(v) for v in values]
            all_chars: list[object] = []
            for p in parts:
                all_chars.extend(p.data)
                all_chars.append(" ")
            if all_chars:
                all_chars.pop()
            return APLArray.array([len(all_chars)], all_chars)
        operand = self.evaluate(operand_node)
        return self._fmt_value(operand)

    def _fmt_value(self, operand: APLArray) -> APLArray:
        """Format a single value as a character vector."""
        if operand.shape == []:
            text = format_num(operand.data[0])
        elif len(operand.shape) == 1:
            if is_char_array(operand.data):
                text = chars_to_str(operand.data)
            else:
                text = " ".join(format_num(x) for x in operand.data)
        else:
            text = str(operand)
        return APLArray.array([len(text)], list(text))

    def _sys_fmt_dyadic(self, left_node: object, right_node: object) -> APLArray:
        """Dyadic ⎕FMT — format with specification string."""
        from marple.fmt import dyadic_fmt
        from marple.nodes import FmtArgs
        left = self.evaluate(left_node)
        fmt_str = _apl_chars_to_str(left.data)
        if isinstance(right_node, FmtArgs):
            values = [self.evaluate(arg) for arg in right_node.args]
        else:
            right = self.evaluate(right_node)
            values = [right]
        return dyadic_fmt(fmt_str, values)

    def _sys_cr(self, operand: APLArray) -> APLArray:
        fn_name = _apl_chars_to_str(operand.data)
        source = self.env.get_source(fn_name)
        if source is None:
            raise DomainError("Not a defined function: " + fn_name)
        if isinstance(source, list):
            lines = source
        elif "\n" in source:
            lines = source.split("\n")
        else:
            lines = [source]
        max_len = max(len(l) for l in lines) if lines else 0
        flat: list[object] = []
        for line in lines:
            flat.extend(list(_ljust(line, max_len)))
        return APLArray.array([len(lines), max_len], flat)

    def _sys_fx(self, operand: APLArray) -> APLArray:
        from marple.dfn_binding import DfnBinding
        from marple.errors import APLError
        from marple.parser import parse
        if len(operand.shape) == 2:
            rows, cols = operand.shape
            # Flatten first: 2D uint32 char data otherwise slices rows.
            flat = operand.data.flatten() if hasattr(operand.data, 'flatten') else operand.data
            lines = []
            for r in range(rows):
                row_chars = flat[r * cols : (r + 1) * cols]
                lines.append(_apl_chars_to_str(row_chars).rstrip())
            text = "\n".join(lines)
        else:
            text = _apl_chars_to_str(operand.data)
        parts = text.split("←", 1)
        if len(parts) < 2:
            raise DomainError("⎕FX requires an assignment: name←{body}")
        fn_name = parts[0].strip()
        from marple.executor import _newlines_to_diamonds
        source = _newlines_to_diamonds(text)
        tree = parse(source, self.env.class_dict())
        try:
            self.evaluate(tree)
        except APLError:
            raise DomainError("⎕FX: invalid function definition")
        val = self.env.get(fn_name)
        if not isinstance(val, DfnBinding):
            raise DomainError("⎕FX did not produce a function")
        self.env.set_source(fn_name, text.strip())
        if "⍺⍺" in text or "⍵⍵" in text:
            self.env.classify(fn_name, NC_OPERATOR)
            self.env.set_operator_arity(fn_name, 2 if "⍵⍵" in text else 1)
        chars = list(fn_name)
        return APLArray.array([len(chars)], chars)

    def _sys_dl(self, operand: APLArray) -> APLArray:
        secs = float(operand.data[0])
        elapsed = self.env.timer.sleep(secs)
        return S(elapsed)

    def _sys_csv(self, operand: APLArray) -> APLArray:
        import csv as _csv
        import io as _io
        path = _apl_chars_to_str(operand.data)
        text = self.fs.read_text(path)
        reader = _csv.reader(_io.StringIO(text))
        headers = next(reader)
        col_names = []
        for h in headers:
            name = h.strip().replace(" ", "_")
            name = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
            col_names.append(name)
        columns: list[list[str]] = [[] for _ in col_names]
        row_count = 0
        for row in reader:
            row_count += 1
            for i, val in enumerate(row):
                if i < len(columns):
                    columns[i].append(val.strip())
        for col_name, col_data in zip(col_names, columns):
            try:
                nums: list[int | float] = []
                for v in col_data:
                    if "." in v:
                        nums.append(float(v))
                    else:
                        nums.append(int(v))
                self.env.bind_name(col_name, APLArray.array([len(nums)], nums), NC_ARRAY)
            except (ValueError, TypeError):
                max_len = max((len(v) for v in col_data), default=0)
                chars: list[object] = []
                for v in col_data:
                    chars.extend(list(v.ljust(max_len)))
                self.env.bind_name(
                    col_name,
                    APLArray.array([len(col_data), max_len], chars),
                    NC_ARRAY,
                )
        return S(row_count)

    def _sys_nread(self, operand: APLArray) -> APLArray:
        path = _apl_chars_to_str(operand.data)
        text = self.fs.read_text(path)
        chars = list(text)
        return APLArray.array([len(chars)], chars) if chars else APLArray.array([0], [])

    def _sys_nexists(self, operand: APLArray) -> APLArray:
        path = _apl_chars_to_str(operand.data)
        return S(1 if self.fs.exists(path) else 0)

    def _sys_ndelete(self, operand: APLArray) -> APLArray:
        path = _apl_chars_to_str(operand.data)
        try:
            self.fs.delete(path)
        except OSError:
            raise DomainError("File not found: " + path)
        return S(0)

    def _sys_nwrite(self, left: APLArray, right: APLArray) -> APLArray:
        path = _apl_chars_to_str(right.data)
        text = _apl_chars_to_str(left.data)
        self.fs.write_text(path, text)
        return APLArray.array([0], [])
