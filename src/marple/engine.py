"""Class-based APL interpreter for MARPLE."""

from marple.arraymodel import APLArray, S
from marple.backend import (
    _DOWNCAST_CT, is_numeric_array, maybe_downcast,
)
from marple.dfn_binding import DfnBinding
from marple.environment import Environment
from marple.executor import Executor, _newlines_to_diamonds
from marple.parser import Assignment, parse
from marple.symbol_table import NC_FUNCTION, NC_OPERATOR


_SYS_FUNCTION_NAMES = (
    "⎕EA", "⎕UCS", "⎕NC", "⎕EX", "⎕SIGNAL", "⎕DR",
    "⎕NREAD", "⎕NWRITE", "⎕NEXISTS", "⎕NDELETE",
    "⎕CR", "⎕FX", "⎕CSV",
)


class Interpreter(Executor):

    def __init__(self, io: int | None = None) -> None:
        from marple.config import get_default_io
        effective_io = io if io is not None else get_default_io()
        self.env = Environment(io=effective_io)

    def run(self, source: str) -> APLArray:
        """Parse and evaluate APL source code."""
        if source.strip().startswith("#import"):
            return self._handle_import(source.strip())
        for qfn in _SYS_FUNCTION_NAMES:
            self.env.classify(qfn, NC_FUNCTION)
        source = _newlines_to_diamonds(source)
        tree = parse(source, self.env.class_dict(), self.env.operator_arity_dict())
        result = self.evaluate(tree)
        if isinstance(tree, Assignment):
            self._track_dfn_source(tree.name, source)
        if isinstance(result, DfnBinding):
            return S(0)
        if isinstance(result, APLArray) and is_numeric_array(result.data):
            result = APLArray(list(result.shape), maybe_downcast(result.data, _DOWNCAST_CT))
        return result

    def _handle_import(self, source: str) -> APLArray:
        """Handle #import directive."""
        from marple.errors import DomainError, ValueError_
        from marple.nodes import IBeamDerived
        parts = source.split()
        if len(parts) < 2:
            raise DomainError("Invalid #import directive")
        qualified = parts[1]
        alias = parts[3] if len(parts) >= 4 and parts[2] == "as" else None
        name_parts = qualified.split("::")
        if name_parts[0] != "$":
            raise ValueError_(f"Import from non-system namespace not yet supported: {qualified}")
        result = self.resolve_qualified(name_parts)
        bind_name = alias if alias else name_parts[-1]
        if isinstance(result, (DfnBinding, IBeamDerived)) or (
                hasattr(result, 'dfn') and hasattr(result, 'env')):
            self.env.bind_name(bind_name, result, NC_FUNCTION)
        elif isinstance(result, APLArray):
            from marple.symbol_table import NC_ARRAY
            self.env.bind_name(bind_name, result, NC_ARRAY)
        return S(0)

    def _track_dfn_source(self, name: str, source: str) -> None:
        """Record source text for dfn/dop assignments (for workspace save)."""
        value = self.env.get(name)
        if not isinstance(value, DfnBinding):
            return
        self.env.set_source(name, source.strip())
        if "⍺⍺" not in source and "⍵⍵" not in source:
            return
        self.env.classify(name, NC_OPERATOR)
        self.env.set_operator_arity(name, 2 if "⍵⍵" in source else 1)
