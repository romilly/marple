"""DfnBinding: a dfn/dop that can evaluate its own body."""

from __future__ import annotations

from typing import TYPE_CHECKING

from marple.arraymodel import APLArray, S
from marple.executor import Executor
from marple.parser import AlphaDefault, Dfn, Guard

if TYPE_CHECKING:
    from marple.environment import Environment


class _TailCall:
    """Signal: re-enter dfn with new args instead of recursing."""
    __slots__ = ("omega", "alpha")

    def __init__(self, omega: APLArray, alpha: APLArray | None) -> None:
        self.omega = omega
        self.alpha = alpha


def _is_tail_self_call(node: object) -> bool:
    """Check if an AST node is a ∇ call in tail position."""
    from marple.nodes import DyadicDfnCall, MonadicDfnCall, Nabla
    if isinstance(node, MonadicDfnCall) and isinstance(node.dfn, Nabla):
        return True
    if isinstance(node, DyadicDfnCall) and isinstance(node.dfn, Nabla):
        return True
    return False


class DfnBinding(Executor):
    """A dfn or dop bound to the environment in which it was defined."""

    def __init__(self, dfn: Dfn, defining_env: Environment) -> None:
        self.dfn = dfn
        self.defining_env = defining_env
        self.env = defining_env  # current env; swapped during apply

    def apply(
        self,
        omega: APLArray,
        alpha: APLArray | None = None,
        alpha_alpha: object | None = None,
        omega_omega: object | None = None,
    ) -> APLArray:
        """Apply this dfn or dop to its arguments."""
        saved_env = self.env
        try:
            while True:
                self.env = self._make_env(omega, alpha, alpha_alpha, omega_omega)
                result = self._execute_body()
                if isinstance(result, _TailCall):
                    omega = result.omega
                    alpha = result.alpha
                    continue
                return result
        finally:
            self.env = saved_env

    def _make_env(
        self,
        omega: APLArray,
        alpha: APLArray | None,
        alpha_alpha: object | None,
        omega_omega: object | None,
    ) -> Environment:
        """Build the local environment for this call."""
        local_env = self.defining_env.copy()
        local_env["⍵"] = omega
        if alpha is not None:
            local_env["⍺"] = alpha
        if alpha_alpha is not None:
            local_env["⍺⍺"] = alpha_alpha
        if omega_omega is not None:
            local_env["⍵⍵"] = omega_omega
        local_env["∇"] = self
        return local_env

    def _execute_body(self) -> APLArray | _TailCall:
        """Execute the dfn body statements.

        Returns _TailCall to signal TCO, otherwise the result APLArray.
        """
        from marple.nodes import DyadicDfnCall, MonadicDfnCall
        result: APLArray = S(0)
        stmts = self.dfn.body
        last_idx = len(stmts) - 1
        for idx, stmt in enumerate(stmts):
            if isinstance(stmt, AlphaDefault):
                if "⍺" not in self.env:
                    self.env["⍺"] = self.evaluate(stmt.default)
            elif isinstance(stmt, Guard):
                cond = self.evaluate(stmt.condition)
                if cond.data[0]:
                    if _is_tail_self_call(stmt.body):
                        return self._make_tail_call(stmt.body)
                    return self.evaluate(stmt.body)
            else:
                if idx == last_idx and _is_tail_self_call(stmt):
                    return self._make_tail_call(stmt)
                result = self.evaluate(stmt)
        return result

    def _make_tail_call(self, node: object) -> _TailCall:
        """Extract args from a tail-position ∇ call and return a _TailCall signal."""
        from marple.nodes import DyadicDfnCall, MonadicDfnCall
        if isinstance(node, MonadicDfnCall):
            omega = self.evaluate(node.operand)
            return _TailCall(omega, None)
        if isinstance(node, DyadicDfnCall):
            omega = self.evaluate(node.right)
            alpha = self.evaluate(node.left)
            return _TailCall(omega, alpha)
        raise RuntimeError("_make_tail_call called on non-∇ node")
