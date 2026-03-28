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
    "⎕CR", "⎕FX",
)


class Interpreter(Executor):

    def __init__(self, io: int | None = None) -> None:
        from marple.config import get_default_io
        effective_io = io if io is not None else get_default_io()
        self.env = Environment(io=effective_io)

    def run(self, source: str) -> APLArray:
        """Parse and evaluate APL source code."""
        for qfn in _SYS_FUNCTION_NAMES:
            self.env.classify(qfn, NC_FUNCTION)
        op_arity = self.env.get("__operator_arity__", {})
        source = _newlines_to_diamonds(source)
        tree = parse(source, self.env.class_dict(), op_arity)
        result = self._evaluate(tree)
        if isinstance(tree, Assignment):
            self._track_dfn_source(tree.name, source)
        if isinstance(result, DfnBinding):
            return S(0)
        if isinstance(result, APLArray) and is_numeric_array(result.data):
            result = APLArray(list(result.shape), maybe_downcast(result.data, _DOWNCAST_CT))
        return result

    def _track_dfn_source(self, name: str, source: str) -> None:
        """Record source text for dfn/dop assignments (for workspace save)."""
        value = self.env.get(name)
        if not isinstance(value, DfnBinding):
            return
        sources = self.env.setdefault("__sources__", {})
        sources[name] = source.strip()
        if "⍺⍺" not in source and "⍵⍵" not in source:
            return
        self.env.classify(name, NC_OPERATOR)
        op_ar = self.env.setdefault("__operator_arity__", {})
        op_ar[name] = 2 if "⍵⍵" in source else 1
