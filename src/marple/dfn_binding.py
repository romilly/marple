"""DfnBinding (function) and DopBinding (operator): user-defined
values bound to the environment in which they were defined."""


from marple.numpy_array import APLArray, S
from marple.apl_value import APLValue, Operator
from marple.executor import Executor
from marple.nodes import Evaluatable, ExecutionContext, Node, UnappliedFunction
from marple.parser import AlphaDefault, Dfn, Guard

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


class _DfnExecutor(Executor):
    """Shared body-execution implementation for DfnBinding and DopBinding.

    Captures the defining environment, builds a local env per call, runs the
    body with tail-call optimisation, and supports the ⍺/⍺⍺/⍵⍵ slots.
    Concrete subclasses expose different public apply/call surfaces.
    """

    def __init__(self, dfn: Dfn, defining_env: Environment) -> None:
        self.dfn = dfn
        self.defining_env = defining_env
        self.env = defining_env  # current env; swapped during apply

    def apply(
        self,
        omega: APLArray,
        alpha: APLArray | None = None,
        alpha_alpha: APLValue | None = None,
        omega_omega: APLValue | None = None,
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
        alpha_alpha: APLValue | None,
        omega_omega: APLValue | None,
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
        assert isinstance(self, APLValue)
        local_env["∇"] = self
        return local_env

    def _execute_body(self) -> APLArray | _TailCall:
        """Execute the dfn body statements.

        Returns _TailCall to signal TCO, otherwise the result APLArray.
        """
        result: APLArray = S(0)
        stmts = self.dfn.body
        last_idx = len(stmts) - 1
        for idx, stmt in enumerate(stmts):
            if isinstance(stmt, AlphaDefault):
                if "⍺" not in self.env:
                    self.env["⍺"] = self.evaluate(stmt.default)
            elif isinstance(stmt, Guard):
                cond = self.evaluate(stmt.condition)
                if cond.data.item():
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


class DfnBinding(UnappliedFunction, _DfnExecutor):
    """User-defined function value: bound dfn that takes ⍵ (and optionally ⍺)."""

    def apply_monadic(self, ctx: ExecutionContext, operand_node: Evaluatable) -> APLArray:
        operand = ctx.evaluate(operand_node)
        return self.apply(operand)

    def apply_dyadic(self, ctx: ExecutionContext, left_node: Evaluatable, right_node: Evaluatable) -> APLArray:
        right = ctx.evaluate(right_node)
        left = ctx.evaluate(left_node)
        return self.apply(right, alpha=left)


class DopBinding(Operator, _DfnExecutor):
    """User-defined operator value: bound dfn that references ⍺⍺ (and optionally ⍵⍵)."""

    def apply_monadic_dop(self, ctx: ExecutionContext, argument: APLArray,
                          operand: APLValue, alpha: APLArray | None = None) -> APLArray:
        return self.apply(argument, alpha_alpha=operand, alpha=alpha)

    def apply_dyadic_dop(self, ctx: ExecutionContext, argument: APLArray,
                         left_operand: APLValue, right_operand: APLValue) -> APLArray:
        return self.apply(argument, alpha_alpha=left_operand, omega_omega=right_operand)
