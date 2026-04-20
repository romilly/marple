"""I-beam registry.

I-beams are built-in system services selected by integer code, per
Dyalog's `R←{X}(A⌶)Y` model. A is the integer; the registry maps it
to a Python callable that takes the right argument (omega) and an
optional left argument (alpha) and returns an APLArray.

I-beams are not user-definable — this registry is marple's catalog
of services. Numbering below Dyalog's 200+ range leaves headroom for
service codes aligned with Dyalog in the future.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from marple.errors import DomainError
from marple.ports.array import APLArray


if TYPE_CHECKING:
    # Module-level type alias: PEP 604 `APLArray | None` is evaluated
    # at `__or__` time, which MicroPython's `type` doesn't implement.
    # Hidden behind TYPE_CHECKING so the alias exists only for pyright;
    # runtime uses the broader `Any` alias below.
    IBeamImpl = Callable[[APLArray, APLArray | None], APLArray]
else:
    IBeamImpl = Any


_REGISTRY: "dict[int, IBeamImpl]" = {}


def register(code: int, impl: IBeamImpl) -> None:
    """Register a Python implementation against an integer code.

    Re-registration replaces the previous entry; this is intentional
    for test harnesses, but production registrations happen once at
    import time.
    """
    _REGISTRY[code] = impl


def lookup(code: int) -> IBeamImpl:
    """Return the implementation registered for `code`.

    Raises DomainError if no implementation is registered.
    """
    impl = _REGISTRY.get(code)
    if impl is None:
        raise DomainError(f"Unknown i-beam code: {code}")
    return impl


def _register_builtins() -> None:
    """Register marple's built-in i-beams. Called on module import."""
    from marple.stdlib import str_impl

    def _upper(omega: APLArray, alpha: APLArray | None = None) -> APLArray:
        return str_impl.upper(omega)

    def _lower(omega: APLArray, alpha: APLArray | None = None) -> APLArray:
        return str_impl.lower(omega)

    def _trim(omega: APLArray, alpha: APLArray | None = None) -> APLArray:
        return str_impl.trim(omega)

    register(100, _upper)
    register(101, _lower)
    register(102, _trim)


_register_builtins()
