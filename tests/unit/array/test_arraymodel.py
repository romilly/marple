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
