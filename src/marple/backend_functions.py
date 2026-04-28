from typing import Any, TYPE_CHECKING

import numpy as np
import numpy.typing as npt
NDArray = npt.NDArray[Any]

if TYPE_CHECKING:
    from marple.ports.array import APLArray


# TODO: The design of this module appears to fly in the face of the plan:
# we want (at least) two different backends, one for mainstream numpy, one for the pico2.
# def set_char_dtype(dtype: np.dtype[Any]) -> None:
#     """Select the dtype used for character data.

#     The active dtype is process-global — platforms select it once at startup
#     (NumpyAPLArray: uint32; UlabAPLArray: uint16). Callers should save and
#     restore the previous value if they need to temporarily switch, e.g. in
#     tests.
#     """


# Module-level comparison tolerance for downcast
_DOWNCAST_CT: float = 1e-14

