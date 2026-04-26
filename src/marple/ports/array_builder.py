from abc import ABC, abstractmethod

from marple.ports.array import APLArray


class ArrayBuilder(ABC):
    @abstractmethod
    def apl_array(cls, shape, data) -> APLArray:
        pass

