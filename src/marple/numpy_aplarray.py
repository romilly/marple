"""NumpyAPLArray — numpy-backed concrete subclass of APLArray.

Part of the incremental refactor turning APLArray into an abstract base with
backend-specific concrete implementations (see the APLArray inheritance plan
and plan/plan-numeric-backend-port.md). This subclass is currently empty —
it inherits everything from APLArray. Subsequent phases move primitive
operations down from APLArray into here, then mark the APLArray versions
abstract.
"""

from marple.numpy_array import APLArray


class NumpyAPLArray(APLArray):
    """APLArray backed by numpy. Currently inherits everything from APLArray."""
    pass
