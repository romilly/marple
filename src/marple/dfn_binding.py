"""DfnBinding: a dfn/dop that can evaluate its own body."""

from typing import Any

from marple.arraymodel import APLArray, S
from marple.executor import Executor
from marple.parser import AlphaDefault, Dfn, Guard


class DfnBinding(Executor):
    """A dfn or dop bound to the environment in which it was defined."""

    def __init__(self, dfn: Dfn, defining_env: dict[str, Any]) -> None:
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
        self.env = self._make_env(omega, alpha, alpha_alpha, omega_omega)
        try:
            return self._execute_body()
        finally:
            self.env = saved_env

    def _make_env(
        self,
        omega: APLArray,
        alpha: APLArray | None,
        alpha_alpha: object | None,
        omega_omega: object | None,
    ) -> dict[str, Any]:
        """Build the local environment for this call."""
        local_env: dict[str, Any] = dict(self.defining_env)
        local_env["⍵"] = omega
        if alpha is not None:
            local_env["⍺"] = alpha
        if alpha_alpha is not None:
            local_env["⍺⍺"] = alpha_alpha
        if omega_omega is not None:
            local_env["⍵⍵"] = omega_omega
        local_env["∇"] = self
        return local_env

    def _execute_body(self) -> APLArray:
        """Execute the dfn body statements."""
        result = S(0)
        for stmt in self.dfn.body:
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
