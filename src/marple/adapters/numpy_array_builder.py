from typing import Any

#from marple.numpy_aplarray import NumpyAPLArray
from marple.ports.array import APLArray
from marple.ports.array_builder import ArrayBuilder


class NumpyArrayBuilder(ArrayBuilder):
    def apl_array(self, shape, data) -> APLArray:
        return APLArray(shape, data)
    
    def S(self, value: Any) -> APLArray:
    # Construct whichever APLArray subclass is active — NumpyAPLArray by
    # default on desktop, UlabAPLArray on the Pico. Route through the
    # backend_functions registry so subclass method overrides (e.g.
    # UlabAPLArray._numeric_dyadic_op) fire on the resulting instance.
    # Lazy import avoids an import cycle with backend_functions.
        return APLArray.scalar(value) # type: ignore

    
BUILDER = NumpyArrayBuilder()