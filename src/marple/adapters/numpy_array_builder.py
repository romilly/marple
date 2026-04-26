from marple.numpy_aplarray import NumpyAPLArray
from marple.ports.array import APLArray
from marple.ports.array_builder import ArrayBuilder

class NumpyArrayBuilder(ArrayBuilder):
    def apl_array(self, shape, data) -> APLArray:
        return NumpyAPLArray(shape, data)