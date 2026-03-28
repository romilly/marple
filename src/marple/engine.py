"""Class-based APL interpreter for MARPLE."""

from typing import Any

from marple.arraymodel import APLArray, S
from marple.backend import (
    _DOWNCAST_CT, is_numeric_array, maybe_downcast,
)
from marple.dfn_binding import DfnBinding
from marple.executor import Executor, NC_FUNCTION, NC_OPERATOR, _newlines_to_diamonds
from marple.parser import Assignment, parse


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


class Interpreter(Executor):

    def __init__(self, io: int | None = None) -> None:
        from marple.config import get_default_io
        effective_io = io if io is not None else get_default_io()
        self.env: dict[str, Any] = dict(_SYSTEM_DEFAULTS)
        self.env["⎕IO"] = S(effective_io)

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
        name_table = self.env.get("__name_table__", {})
        name_table[name] = NC_OPERATOR
        self.env["__name_table__"] = name_table
        op_ar = self.env.setdefault("__operator_arity__", {})
        op_ar[name] = 2 if "⍵⍵" in source else 1
