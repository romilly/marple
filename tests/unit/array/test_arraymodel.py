from marple.numpy_array import APLArray, S


class TestAPLArrayScalar:
    def test_scalar_has_empty_shape(self) -> None:
        a = APLArray.scalar(5)
        assert a.shape == []

    def test_scalar_has_single_element_data(self) -> None:
        a = APLArray.scalar(5)
        assert a.data == [5]

    def test_scalar_is_scalar(self) -> None:
        a = APLArray.scalar(5)
        assert a.is_scalar()

    def test_scalar_equality(self) -> None:
        assert APLArray.scalar(5) == APLArray.scalar(5)

    def test_scalar_inequality(self) -> None:
        assert APLArray.scalar(5) != APLArray.scalar(3)


class TestAPLArrayVector:
    def test_vector_shape(self) -> None:
        a = APLArray.array([3], [1, 2, 3])
        assert a.shape == [3]

    def test_vector_data(self) -> None:
        a = APLArray.array([3], [1, 2, 3])
        assert list(a.data) == [1, 2, 3]

    def test_vector_is_not_scalar(self) -> None:
        a = APLArray.array([3], [1, 2, 3])
        assert not a.is_scalar()

    def test_vector_equality(self) -> None:
        assert APLArray.array([3], [1, 2, 3]) == APLArray.array([3], [1, 2, 3])

    def test_vectors_with_different_data_not_equal(self) -> None:
        assert APLArray.array([3], [1, 2, 3]) != APLArray.array([3], [4, 5, 6])

    def test_vectors_with_different_shape_not_equal(self) -> None:
        assert APLArray.array([3], [1, 2, 3]) != APLArray.array([2], [1, 2])


class TestAPLArrayRepr:
    def test_scalar_repr(self) -> None:
        assert repr(APLArray.scalar(5)) == "S(5)"

    def test_vector_repr(self) -> None:
        r = repr(APLArray.array([3], [1, 2, 3]))
        assert "[3]" in r
        assert "1, 2, 3" in r


class TestSubclassPropagation:
    """Arithmetic and factory calls on a subclass produce subclass instances.

    Locks in the invariant that drives the inheritance refactor: when APLArray
    becomes abstract with backend-specific subclasses, the subclass must
    propagate through arithmetic and factory methods without the caller
    having to know the class.
    """

    def test_factory_returns_subclass(self) -> None:
        from marple.numpy_aplarray import NumpyAPLArray
        a = NumpyAPLArray.array([3], [1, 2, 3])
        assert type(a) is NumpyAPLArray

    def test_scalar_factory_returns_subclass(self) -> None:
        from marple.numpy_aplarray import NumpyAPLArray
        a = NumpyAPLArray.scalar(5)
        assert type(a) is NumpyAPLArray

    def test_add_preserves_subclass(self) -> None:
        from marple.numpy_aplarray import NumpyAPLArray
        a = NumpyAPLArray.scalar(1)
        b = NumpyAPLArray.scalar(2)
        assert type(a.add(b)) is NumpyAPLArray

    def test_negate_preserves_subclass(self) -> None:
        from marple.numpy_aplarray import NumpyAPLArray
        a = NumpyAPLArray.scalar(5)
        assert type(a.negate()) is NumpyAPLArray

    def test_reciprocal_preserves_subclass(self) -> None:
        from marple.numpy_aplarray import NumpyAPLArray
        a = NumpyAPLArray.scalar(2)
        assert type(a.reciprocal()) is NumpyAPLArray

    def test_multiply_preserves_subclass(self) -> None:
        from marple.numpy_aplarray import NumpyAPLArray
        a = NumpyAPLArray.scalar(3)
        b = NumpyAPLArray.scalar(4)
        assert type(a.multiply(b)) is NumpyAPLArray

    def test_subtract_preserves_subclass(self) -> None:
        from marple.numpy_aplarray import NumpyAPLArray
        a = NumpyAPLArray.scalar(7)
        b = NumpyAPLArray.scalar(2)
        assert type(a.subtract(b)) is NumpyAPLArray


class TestBackendOverridability:
    """Executable documentation for the backend-override seams.

    APLArray exposes three override hooks that let a subclass swap the numeric
    machinery without touching APL semantics (scalar extension, char guards,
    domain errors): `_numeric_dyadic_op`, `_primitive_negate`, `_primitive_reciprocal`.
    """

    def test_subclass_override_of_primitive_negate_is_called(self) -> None:
        from marple.numpy_aplarray import NumpyAPLArray
        from marple.numpy_array import APLArray

        calls: list[str] = []

        class TracingArray(NumpyAPLArray):
            def _primitive_negate(self) -> APLArray:
                calls.append("negate")
                return super()._primitive_negate()

        TracingArray.scalar(5).negate()
        assert calls == ["negate"]

    def test_subclass_override_of_primitive_reciprocal_is_called(self) -> None:
        from marple.numpy_aplarray import NumpyAPLArray
        from marple.numpy_array import APLArray

        calls: list[str] = []

        class TracingArray(NumpyAPLArray):
            def _primitive_reciprocal(self) -> APLArray:
                calls.append("reciprocal")
                return super()._primitive_reciprocal()

        TracingArray.scalar(2).reciprocal()
        assert calls == ["reciprocal"]

    def test_subclass_override_of_numeric_dyadic_op_is_called(self) -> None:
        from marple.numpy_aplarray import NumpyAPLArray
        from marple.numpy_array import APLArray
        from typing import Any, Callable

        calls: list[str] = []

        class TracingArray(NumpyAPLArray):
            def _numeric_dyadic_op(self, other: APLArray,
                                   op: Callable[[Any, Any], Any],
                                   upcast: bool = False) -> APLArray:
                calls.append("dyadic")
                return super()._numeric_dyadic_op(other, op, upcast)

        a = TracingArray.scalar(1)
        b = TracingArray.scalar(2)
        a.add(b)
        a.subtract(b)
        a.multiply(b)
        assert calls == ["dyadic", "dyadic", "dyadic"]


class TestCharDtype:
    """The char dtype is a backend-specific classmethod.

    NumpyAPLArray stores Unicode codepoints as uint32. A future UlabAPLArray
    will store them as uint16 because ulab has no uint32 support. The dtype
    is chosen by each subclass via `char_dtype()`.
    """

    def test_aplarray_default_char_dtype_is_uint32(self) -> None:
        from marple.numpy_array import APLArray
        from marple.get_numpy import np
        assert APLArray.char_dtype() == np.dtype(np.uint32)

    def test_numpy_aplarray_char_dtype_is_uint32(self) -> None:
        from marple.numpy_aplarray import NumpyAPLArray
        from marple.get_numpy import np
        assert NumpyAPLArray.char_dtype() == np.dtype(np.uint32)

    def test_subclass_can_override_char_dtype(self) -> None:
        from typing import Any
        from marple.numpy_aplarray import NumpyAPLArray
        from marple.get_numpy import np

        class SmallCharArray(NumpyAPLArray):
            @classmethod
            def char_dtype(cls) -> np.dtype[Any]:
                return np.dtype(np.uint16)

        assert SmallCharArray.char_dtype() == np.dtype(np.uint16)


class TestActiveCharDtype:
    """`backend_functions` helpers follow whichever char dtype is active.

    The active dtype is a process-global set at Interpreter construction time.
    Setting it to uint16 flips `is_char_array`, `is_numeric_array`,
    `str_to_char_array`, and `char_fill` to the narrower encoding.
    """

    def test_is_char_array_respects_active_dtype(self) -> None:
        from marple.get_numpy import np
        from marple import backend_functions

        original = backend_functions.get_char_dtype()
        try:
            backend_functions.set_char_dtype(np.dtype(np.uint16))
            u16 = np.array([65, 66], dtype=np.uint16)
            u32 = np.array([65, 66], dtype=np.uint32)
            assert backend_functions.is_char_array(u16)
            assert not backend_functions.is_char_array(u32)
        finally:
            backend_functions.set_char_dtype(original)

    def test_is_numeric_array_respects_active_dtype(self) -> None:
        from marple.get_numpy import np
        from marple import backend_functions

        original = backend_functions.get_char_dtype()
        try:
            backend_functions.set_char_dtype(np.dtype(np.uint16))
            u16 = np.array([65, 66], dtype=np.uint16)
            u32 = np.array([65, 66], dtype=np.uint32)
            assert not backend_functions.is_numeric_array(u16)
            assert backend_functions.is_numeric_array(u32)
        finally:
            backend_functions.set_char_dtype(original)

    def test_str_to_char_array_uses_active_dtype(self) -> None:
        from marple.get_numpy import np
        from marple import backend_functions

        original = backend_functions.get_char_dtype()
        try:
            backend_functions.set_char_dtype(np.dtype(np.uint16))
            result = backend_functions.str_to_char_array("AB")
            assert result.dtype == np.dtype(np.uint16)
        finally:
            backend_functions.set_char_dtype(original)

    def test_char_fill_uses_active_dtype(self) -> None:
        from marple.get_numpy import np
        from marple import backend_functions

        original = backend_functions.get_char_dtype()
        try:
            backend_functions.set_char_dtype(np.dtype(np.uint16))
            fill = backend_functions.char_fill()
            assert fill.dtype == np.dtype(np.uint16)
            assert int(fill) == 32
        finally:
            backend_functions.set_char_dtype(original)

    def test_default_active_dtype_is_uint32(self) -> None:
        from marple.get_numpy import np
        from marple import backend_functions
        assert backend_functions.get_char_dtype() == np.dtype(np.uint32)


class TestInterpreterWiresCharDtype:
    """Constructing an Interpreter selects the char dtype from array_cls.

    Platforms pass `array_cls=UlabAPLArray` (or similar) when bootstrapping
    on non-numpy backends; the Interpreter threads that class's char_dtype
    into backend_functions so the helpers pick up the right encoding.
    """

    def test_interpreter_sets_char_dtype_from_array_cls(self) -> None:
        from typing import Any
        from marple.get_numpy import np
        from marple.engine import Interpreter
        from marple.numpy_aplarray import NumpyAPLArray
        from marple import backend_functions

        class SmallCharArray(NumpyAPLArray):
            @classmethod
            def char_dtype(cls) -> np.dtype[Any]:
                return np.dtype(np.uint16)

        original = backend_functions.get_char_dtype()
        try:
            Interpreter(array_cls=SmallCharArray)
            assert backend_functions.get_char_dtype() == np.dtype(np.uint16)
        finally:
            backend_functions.set_char_dtype(original)

    def test_interpreter_default_leaves_char_dtype_uint32(self) -> None:
        from marple.get_numpy import np
        from marple.engine import Interpreter
        from marple import backend_functions

        original = backend_functions.get_char_dtype()
        try:
            Interpreter()
            assert backend_functions.get_char_dtype() == np.dtype(np.uint32)
        finally:
            backend_functions.set_char_dtype(original)
