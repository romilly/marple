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
